import mysql.connector
from mysql.connector import Error
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.button import MDRectangleFlatButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineListItem
from kivymd.uix.dialog import MDDialog
import qrcode
from io import BytesIO
import threading
import time
import os

Window.size = (720, 1280)
Window.clearcolor = (0.05, 0.05, 0.05, 1)

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "app"
IMAGE_BASE_URL = "http://localhost/app/menu_images/"

class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=True
            )
        except Error as e:
            print(f"Database error: {e}")
            self.connection = None

    def execute_query(self, query, params=None, fetch=False):
        if not self.connection or not self.connection.is_connected():
            self.connect()
        if not self.connection:
            return None if fetch else None
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
            cursor.close()
            return result
        else:
            cursor.close()
            self.connection.commit()
            return None

    def execute_insert(self, query, params):
        if not self.connection or not self.connection.is_connected():
            self.connect()
        if not self.connection:
            return None
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

db = Database()

def generate_order_code():
    result = db.execute_query(
        "SELECT MAX(CAST(order_code AS UNSIGNED)) AS last_num FROM orders WHERE order_code REGEXP '^[0-9]+$'",
        fetch=True
    )
    last_num = result[0]['last_num'] if result and result[0]['last_num'] else 0
    return str(last_num + 1).zfill(5)

def load_image_from_url(url, callback):
    def on_success(req, result):
        texture = CoreImage(BytesIO(result), ext='png').texture
        callback(texture)
    UrlRequest(url, on_success, timeout=5)

class ProductCard(MDCard):
    def __init__(self, product, cart_callback, **kwargs):
        super().__init__(**kwargs)
        self.product = product
        self.cart_callback = cart_callback
        self.size_hint = (None, None)
        self.size = (220, 320)
        self.md_bg_color = (0.09, 0.09, 0.09, 1)
        self.radius = 15

        self.layout = BoxLayout(orientation='vertical', spacing=5, padding=8)
        self.add_widget(self.layout)

        self.img = Image(size_hint=(1, 0.55), keep_ratio=True)
        self.layout.add_widget(self.img)
        self.load_image()

        name_label = MDLabel(text=product['name'], font_style='Subtitle1', halign='center', theme_text_color='Primary')
        self.layout.add_widget(name_label)

        price_label = MDLabel(text=f"₱{float(product['price']):.2f}", halign='center', theme_text_color='Secondary')
        self.layout.add_widget(price_label)

        stock_color = (0.8, 0.4, 0, 1) if product['stock'] <= 3 else (0.5, 0.5, 0.5, 1)
        stock_label = MDLabel(text=f"Stock: {product['stock']}", halign='center', theme_text_color='Secondary')
        stock_label.color = stock_color
        self.layout.add_widget(stock_label)

        qty_layout = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        self.minus_btn = Button(text='-', size_hint=(0.3, 1), background_color=(0.2, 0.2, 0.2, 1))
        self.qty_label = Label(text='0', size_hint=(0.4, 1))
        self.plus_btn = Button(text='+', size_hint=(0.3, 1), background_color=(0.2, 0.2, 0.2, 1))
        qty_layout.add_widget(self.minus_btn)
        qty_layout.add_widget(self.qty_label)
        qty_layout.add_widget(self.plus_btn)
        self.layout.add_widget(qty_layout)

        self.minus_btn.bind(on_press=self.decrement)
        self.plus_btn.bind(on_press=self.increment)

    def load_image(self):
        if self.product.get('image_path'):
            url = IMAGE_BASE_URL + os.path.basename(self.product['image_path'])
            load_image_from_url(url, self.set_texture)
        else:
            self.set_texture(None)

    def set_texture(self, texture):
        if texture:
            self.img.texture = texture
        else:
            self.img.texture = None

    def increment(self, instance):
        current = int(self.qty_label.text)
        if current < self.product['stock']:
            self.qty_label.text = str(current + 1)
            self.cart_callback(self.product['id'], 'add')

    def decrement(self, instance):
        current = int(self.qty_label.text)
        if current > 0:
            self.qty_label.text = str(current - 1)
            self.cart_callback(self.product['id'], 'remove')

class CartItemRow(BoxLayout):
    def __init__(self, product_id, name, price, quantity, update_callback, **kwargs):
        super().__init__(**kwargs)
        self.product_id = product_id
        self.update_callback = update_callback
        self.size_hint_y = None
        self.height = 120
        self.spacing = 10
        self.padding = 5

        self.img = Image(size_hint=(0.25, 1), keep_ratio=True)
        self.add_widget(self.img)
        self.load_product_image(product_id)

        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.45)
        info_layout.add_widget(Label(text=name, size_hint_y=0.4, font_size='14sp'))
        info_layout.add_widget(Label(text=f"₱{price:.2f} each", size_hint_y=0.3, font_size='12sp'))
        self.add_widget(info_layout)

        qty_box = BoxLayout(size_hint_x=0.2, spacing=5)
        minus_btn = Button(text='-', on_press=lambda x: self.change_quantity(-1))
        qty_label = Label(text=str(quantity))
        plus_btn = Button(text='+', on_press=lambda x: self.change_quantity(1))
        qty_box.add_widget(minus_btn)
        qty_box.add_widget(qty_label)
        qty_box.add_widget(plus_btn)
        self.add_widget(qty_box)

        self.subtotal_label = Label(text=f"₱{price * quantity:.2f}", size_hint_x=0.2)
        self.add_widget(self.subtotal_label)

        self.qty_label = qty_label
        self.price = price

    def load_product_image(self, product_id):
        product = db.execute_query("SELECT image_path FROM menu WHERE id = %s", (product_id,), fetch=True)
        if product and product[0].get('image_path'):
            url = IMAGE_BASE_URL + os.path.basename(product[0]['image_path'])
            load_image_from_url(url, self.set_texture)
        else:
            self.set_texture(None)

    def set_texture(self, texture):
        if texture:
            self.img.texture = texture
        else:
            self.img.texture = None

    def change_quantity(self, delta):
        new_qty = int(self.qty_label.text) + delta
        if new_qty <= 0:
            self.update_callback(self.product_id, 0)
        else:
            stock = db.execute_query("SELECT stock FROM menu WHERE id = %s", (self.product_id,), fetch=True)
            if stock and new_qty <= stock[0]['stock']:
                self.qty_label.text = str(new_qty)
                self.subtotal_label.text = f"₱{self.price * new_qty:.2f}"
                self.update_callback(self.product_id, new_qty)
            else:
                dialog = MDDialog(title="Stock Error", text=f"Only {stock[0]['stock']} available.")
                dialog.open()

class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cart = {}
        self.current_category_name = "All"
        self.build_ui()
        self.start_queue_polling()

    def build_ui(self):
        main_layout = BoxLayout(orientation='vertical')

        top_bar = MDTopAppBar(title="Snack in Save", elevation=4,
                              right_action_items=[["cart", lambda x: self.go_to_cart()]])
        main_layout.add_widget(top_bar)

        categories = db.execute_query("SELECT id, name FROM categories ORDER BY name", fetch=True)
        if not categories:
            categories = [{'id': 0, 'name': 'All'}]
        else:
            categories.insert(0, {'id': 0, 'name': 'All'})

        cat_scroll = ScrollView(size_hint_y=None, height=50)
        cat_layout = BoxLayout(size_hint_x=None, spacing=5, padding=5)
        cat_layout.bind(minimum_width=cat_layout.setter('width'))
        for cat in categories:
            btn = MDRectangleFlatButton(text=cat['name'], size_hint=(None, 1), width=100)
            btn.bind(on_press=lambda x, cid=cat['id'], cname=cat['name']: self.load_products(cid, cname))
            cat_layout.add_widget(btn)
        cat_scroll.add_widget(cat_layout)
        main_layout.add_widget(cat_scroll)

        self.category_label = MDLabel(text="Category: All", halign='center', font_style='Subtitle1', size_hint_y=None, height=30)
        main_layout.add_widget(self.category_label)

        self.products_grid = GridLayout(cols=2, spacing=10, size_hint_y=None, padding=10)
        self.products_grid.bind(minimum_height=self.products_grid.setter('height'))
        products_scroll = ScrollView()
        products_scroll.add_widget(self.products_grid)
        main_layout.add_widget(products_scroll)

        queue_layout = BoxLayout(orientation='horizontal', size_hint_y=0.35, spacing=10, padding=10)
        self.prepare_panel = self.make_queue_panel("PREPARING")
        self.serving_panel = self.make_queue_panel("NOW SERVING")
        queue_layout.add_widget(self.prepare_panel)
        queue_layout.add_widget(self.serving_panel)
        main_layout.add_widget(queue_layout)

        self.add_widget(main_layout)
        self.load_products(0, "All")

    def make_queue_panel(self, title):
        panel = BoxLayout(orientation='vertical', size_hint=(0.5, 1))
        header = MDLabel(text=title, halign='center', font_style='H6', size_hint_y=None, height=40)
        panel.add_widget(header)
        scroll = ScrollView()
        list_view = GridLayout(cols=1, size_hint_y=None, spacing=5)
        list_view.bind(minimum_height=list_view.setter('height'))
        scroll.add_widget(list_view)
        panel.add_widget(scroll)
        panel.list_view = list_view
        return panel

    def start_queue_polling(self):
        def poll():
            while True:
                waiting = db.execute_query("SELECT order_code, created_at FROM orders WHERE status = 'waiting' ORDER BY created_at ASC LIMIT 30", fetch=True)
                serving = db.execute_query("SELECT order_code, created_at FROM orders WHERE status = 'serving' ORDER BY created_at ASC LIMIT 10", fetch=True)
                Clock.schedule_once(lambda dt: self.refresh_queue_panels(waiting, serving))
                time.sleep(5)
        thread = threading.Thread(target=poll, daemon=True)
        thread.start()

    def refresh_queue_panels(self, waiting, serving):
        self.prepare_panel.list_view.clear_widgets()
        self.serving_panel.list_view.clear_widgets()

        for idx, order in enumerate(waiting):
            item = OneLineListItem(text=f"#{idx+1}  {order['order_code']}  {order['created_at'].strftime('%H:%M')}")
            self.prepare_panel.list_view.add_widget(item)
        for order in serving:
            item = OneLineListItem(text=f"{order['order_code']}  {order['created_at'].strftime('%H:%M')}")
            self.serving_panel.list_view.add_widget(item)

    def load_products(self, category_id, category_name):
        self.current_category_name = category_name
        self.category_label.text = f"Category: {category_name}"
        self.products_grid.clear_widgets()
        if category_id == 0:
            products = db.execute_query("SELECT id, name, price, stock, image_path FROM menu ORDER BY name", fetch=True)
        else:
            products = db.execute_query("""
                SELECT m.id, m.name, m.price, m.stock, m.image_path
                FROM menu m
                INNER JOIN categories c ON m.category_id = c.id
                WHERE c.id = %s
                ORDER BY m.name
            """, (category_id,), fetch=True)
        if not products:
            return
        for prod in products:
            card = ProductCard(prod, self.update_cart)
            self.products_grid.add_widget(card)

    def update_cart(self, product_id, action):
        if product_id not in self.cart:
            product = db.execute_query("SELECT id, name, price FROM menu WHERE id = %s", (product_id,), fetch=True)
            if product:
                self.cart[product_id] = {'name': product[0]['name'], 'price': float(product[0]['price']), 'quantity': 0}
        if action == 'add':
            self.cart[product_id]['quantity'] += 1
        elif action == 'remove':
            if self.cart[product_id]['quantity'] > 0:
                self.cart[product_id]['quantity'] -= 1
                if self.cart[product_id]['quantity'] == 0:
                    del self.cart[product_id]

    def go_to_cart(self):
        app = MDApp.get_running_app()
        cart_screen = app.root.get_screen('cart')
        cart_screen.update_cart(self.cart)
        app.root.current = 'cart'

class CartScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cart = {}
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical')
        top_bar = MDTopAppBar(title="Your Order", elevation=4, left_action_items=[["arrow-left", lambda x: self.go_back()]])
        layout.add_widget(top_bar)

        self.cart_list = ScrollView()
        self.cart_layout = GridLayout(cols=1, size_hint_y=None, spacing=5, padding=10)
        self.cart_layout.bind(minimum_height=self.cart_layout.setter('height'))
        self.cart_list.add_widget(self.cart_layout)
        layout.add_widget(self.cart_list)

        self.total_label = MDLabel(text="Total: ₱0.00", halign='right', font_style='H6', size_hint_y=None, height=50, padding=(10, 0))
        layout.add_widget(self.total_label)

        self.place_btn = MDRaisedButton(text="Place Order", size_hint=(1, None), height=50, on_press=self.place_order)
        layout.add_widget(self.place_btn)

        self.add_widget(layout)

    def update_cart(self, cart):
        self.cart = cart
        self.cart_layout.clear_widgets()
        total = 0
        for pid, item in self.cart.items():
            total += item['price'] * item['quantity']
            row = CartItemRow(pid, item['name'], item['price'], item['quantity'], self.change_quantity)
            self.cart_layout.add_widget(row)
        self.total_label.text = f"Total: ₱{total:.2f}"

    def change_quantity(self, product_id, new_quantity):
        if new_quantity <= 0:
            if product_id in self.cart:
                del self.cart[product_id]
        else:
            self.cart[product_id]['quantity'] = new_quantity
        self.update_cart(self.cart)
        app = MDApp.get_running_app()
        menu_screen = app.root.get_screen('menu')
        menu_screen.cart = self.cart

    def go_back(self):
        app = MDApp.get_running_app()
        app.root.current = 'menu'

    def place_order(self, instance):
        if not self.cart:
            dialog = MDDialog(title="Error", text="Your cart is empty.")
            dialog.open()
            return
        for pid, item in self.cart.items():
            stock = db.execute_query("SELECT stock FROM menu WHERE id = %s", (pid,), fetch=True)
            if not stock or item['quantity'] > stock[0]['stock']:
                dialog = MDDialog(title="Stock Error", text=f"Insufficient stock for {item['name']}.")
                dialog.open()
                return
        total = sum(item['price'] * item['quantity'] for item in self.cart.values())
        order_code = generate_order_code()
        order_id = db.execute_insert(
            "INSERT INTO orders (order_code, total_amount, status) VALUES (%s, %s, 'pending')",
            (order_code, total)
        )
        for pid, item in self.cart.items():
            db.execute_query(
                "INSERT INTO order_items (order_id, menu_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (order_id, pid, item['quantity'], item['price'])
            )
        qr = qrcode.QRCode(box_size=5, border=2)
        qr_data = f"http://{DB_HOST}/app/staff_scan.php?code={order_code}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_bytes = BytesIO()
        qr_img.save(qr_bytes, format='PNG')
        qr_bytes.seek(0)
        self.cart = {}
        self.update_cart(self.cart)
        app = MDApp.get_running_app()
        success_screen = app.root.get_screen('success')
        success_screen.set_order(order_code, total, qr_bytes)
        app.root.current = 'success'

class SuccessScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        top_bar = MDTopAppBar(title="Order Placed", elevation=4, left_action_items=[["arrow-left", lambda x: self.go_back()]])
        layout.add_widget(top_bar)

        self.order_code_label = MDLabel(text="", halign='center', font_style='H4')
        layout.add_widget(self.order_code_label)

        self.qr_image = Image(size_hint=(None, None), size=(200, 200), pos_hint={'center_x': 0.5})
        layout.add_widget(self.qr_image)

        self.status_label = MDLabel(text="", halign='center', font_style='Subtitle1')
        layout.add_widget(self.status_label)

        self.queue_pos_label = MDLabel(text="", halign='center')
        layout.add_widget(self.queue_pos_label)

        new_order_btn = MDRaisedButton(text="New Order", on_press=lambda x: self.go_back())
        layout.add_widget(new_order_btn)

        self.add_widget(layout)

    def set_order(self, order_code, total, qr_bytes):
        self.order_code = order_code
        self.order_code_label.text = f"Order Code: {order_code}"
        texture = CoreImage(BytesIO(qr_bytes.getvalue()), ext='png').texture
        self.qr_image.texture = texture
        self.poll_status()

    def poll_status(self):
        def update():
            while True:
                order = db.execute_query("SELECT status FROM orders WHERE order_code = %s", (self.order_code,), fetch=True)
                if order:
                    status = order[0]['status']
                    Clock.schedule_once(lambda dt: self.update_status(status))
                time.sleep(5)
        thread = threading.Thread(target=update, daemon=True)
        thread.start()

    def update_status(self, status):
        status_text = {
            'pending': 'Waiting for staff',
            'waiting': 'Preparing',
            'serving': 'Ready to claim!',
            'completed': 'Completed'
        }.get(status, status)
        self.status_label.text = f"Status: {status_text}"
        if status in ('pending', 'waiting'):
            pos = db.execute_query("""
                SELECT COUNT(*) AS pos FROM orders WHERE status IN ('pending','waiting') AND id <= (
                    SELECT id FROM orders WHERE order_code = %s
                )
            """, (self.order_code,), fetch=True)
            if pos:
                self.queue_pos_label.text = f"Queue position: #{pos[0]['pos']}"
        else:
            self.queue_pos_label.text = ""

    def go_back(self):
        app = MDApp.get_running_app()
        app.root.current = 'menu'
        menu_screen = app.root.get_screen('menu')
        menu_screen.cart = {}
        menu_screen.load_products(0, "All")

class SnackInSaveApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.theme_style = "Dark"
        sm = ScreenManager()
        menu_screen = MenuScreen(name='menu')
        cart_screen = CartScreen(name='cart')
        success_screen = SuccessScreen(name='success')
        sm.add_widget(menu_screen)
        sm.add_widget(cart_screen)
        sm.add_widget(success_screen)
        return sm

if __name__ == '__main__':
    SnackInSaveApp().run()