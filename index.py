from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
import mysql.connector
from mysql.connector import Error

# Database configuration (adjust if needed)
DB_CONFIG = {
    'host': 'localhost',      # or the IP of your laptop if app runs on phone
    'user': 'root',
    'password': '',
    'database': 'app'
}

class CustomerOrderApp(App):
    def build(self):
        self.cart = {}
        self.menu_items = []
        self.main_layout = BoxLayout(orientation='vertical')

        # Top bar
        self.top_bar = BoxLayout(size_hint_y=0.1, padding=5)
        self.cart_btn = Button(text=f"Cart (0)", on_press=self.show_cart)
        self.top_bar.add_widget(Label(text="Snack in Save 9Nueve", font_size=20))
        self.top_bar.add_widget(self.cart_btn)
        self.main_layout.add_widget(self.top_bar)

        # Menu area (scrollable)
        self.scroll = ScrollView()
        self.menu_grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        self.menu_grid.bind(minimum_height=self.menu_grid.setter('height'))
        self.scroll.add_widget(self.menu_grid)
        self.main_layout.add_widget(self.scroll)

        # Load menu from database
        Clock.schedule_once(lambda dt: self.load_menu(), 0.5)

        return self.main_layout

    def load_menu(self):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, price FROM menu WHERE is_available = 1 ORDER BY name")
            self.menu_items = cursor.fetchall()
            conn.close()

            # Populate menu grid
            self.menu_grid.clear_widgets()
            for item in self.menu_items:
                item_box = BoxLayout(orientation='vertical', size_hint_y=None, height=150)
                item_box.add_widget(Label(text=item['name'], font_size=16, bold=True))
                item_box.add_widget(Label(text=f"₱{item['price']:.2f}", color=(0.8, 0.3, 0, 1)))
                add_btn = Button(text="Add", size_hint_y=0.3)
                add_btn.bind(on_press=lambda btn, i=item: self.add_to_cart(i))
                item_box.add_widget(add_btn)
                self.menu_grid.add_widget(item_box)
        except Error as e:
            self.show_popup("Database Error", f"Failed to load menu:\n{e}")

    def add_to_cart(self, item):
        item_id = item['id']
        if item_id in self.cart:
            self.cart[item_id]['quantity'] += 1
        else:
            self.cart[item_id] = {
                'id': item_id,
                'name': item['name'],
                'price': item['price'],
                'quantity': 1
            }
        self.update_cart_button()

    def update_cart_button(self):
        total_qty = sum(i['quantity'] for i in self.cart.values())
        self.cart_btn.text = f"Cart ({total_qty})"

    def show_cart(self, instance):
        if not self.cart:
            self.show_popup("Cart", "Your cart is empty.")
            return

        # Create popup content
        content = BoxLayout(orientation='vertical', spacing=5, padding=10)
        scroll = ScrollView(size_hint=(1, 0.8))
        items_layout = GridLayout(cols=1, size_hint_y=None, spacing=5)
        items_layout.bind(minimum_height=items_layout.setter('height'))

        total = 0
        for item in self.cart.values():
            subtotal = item['price'] * item['quantity']
            total += subtotal
            row = BoxLayout(size_hint_y=None, height=40)
            row.add_widget(Label(text=item['name'], size_hint_x=0.4))
            row.add_widget(Label(text=f"₱{item['price']:.2f}", size_hint_x=0.2))
            row.add_widget(Label(text=str(item['quantity']), size_hint_x=0.1))
            row.add_widget(Label(text=f"₱{subtotal:.2f}", size_hint_x=0.2))
            remove_btn = Button(text="X", size_hint_x=0.1)
            remove_btn.bind(on_press=lambda btn, iid=item['id']: self.remove_from_cart(iid, cart_popup))
            row.add_widget(remove_btn)
            items_layout.add_widget(row)

        scroll.add_widget(items_layout)

        total_label = Label(text=f"TOTAL: ₱{total:.2f}", font_size=18, bold=True, size_hint_y=0.1)

        # Customer name input
        name_input = TextInput(hint_text="Your name", multiline=False, size_hint_y=0.1)

        # Buttons
        btn_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        order_btn = Button(text="Place Order")
        close_btn = Button(text="Close")

        content.add_widget(scroll)
        content.add_widget(total_label)
        content.add_widget(name_input)
        content.add_widget(btn_layout)
        btn_layout.add_widget(order_btn)
        btn_layout.add_widget(close_btn)

        cart_popup = Popup(title="Your Cart", content=content, size_hint=(0.9, 0.8))
        close_btn.bind(on_press=cart_popup.dismiss)
        order_btn.bind(on_press=lambda x: self.place_order(name_input.text, cart_popup))
        cart_popup.open()

    def remove_from_cart(self, item_id, popup):
        if item_id in self.cart:
            if self.cart[item_id]['quantity'] > 1:
                self.cart[item_id]['quantity'] -= 1
            else:
                del self.cart[item_id]
            self.update_cart_button()
            # Refresh cart popup (close and reopen)
            popup.dismiss()
            self.show_cart(None)

    def place_order(self, customer_name, popup):
        if not customer_name.strip():
            self.show_popup("Error", "Please enter your name.")
            return
        if not self.cart:
            self.show_popup("Error", "Cart is empty.")
            return

        # Calculate total
        total = sum(i['price'] * i['quantity'] for i in self.cart.values())
        order_code = f"ORD{int(time.time())}{random.randint(100, 999)}"

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Insert order
            cursor.execute(
                "INSERT INTO orders (order_code, customer_name, total_amount) VALUES (%s, %s, %s)",
                (order_code, customer_name, total)
            )
            order_id = cursor.lastrowid

            # Insert order items
            for item in self.cart.values():
                cursor.execute(
                    "INSERT INTO order_items (order_id, menu_id, quantity, price) VALUES (%s, %s, %s, %s)",
                    (order_id, item['id'], item['quantity'], item['price'])
                )
            conn.commit()
            conn.close()

            # Clear cart
            self.cart.clear()
            self.update_cart_button()
            popup.dismiss()
            self.show_popup("Order Placed", f"Order code: {order_code}\nPlease show this to staff.")
        except Error as e:
            self.show_popup("Database Error", f"Failed to place order:\n{e}")

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()

import time
import random

if __name__ == '__main__':
    CustomerOrderApp().run()