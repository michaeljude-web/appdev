import tkinter as tk
from tkinter import ttk, messagebox
from staff_sidebar import add_staff_sidebar
import mysql.connector
from datetime import datetime
import cv2
from pyzbar.pyzbar import decode
from PIL import Image, ImageTk
import random
import os
import socket
import urllib.parse
import urllib.request
import re

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "app"
}

def connect_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Connection failed: {err}")
        return None

STATUS_COLORS = {
    "pending":   {"bg": "#fef9ec", "fg": "#d35400", "badge": "#f39c12"},
    "waiting":   {"bg": "#eaf4fb", "fg": "#1a5276", "badge": "#2980b9"},
    "completed": {"bg": "#eafaf1", "fg": "#1e8449", "badge": "#27ae60"},
    "cancelled": {"bg": "#fdedec", "fg": "#c0392b", "badge": "#e74c3c"},
}

def refresh_orders(tree, details_card, status_filter="pending"):
    for row in tree.get_children():
        tree.delete(row)
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)
    if status_filter == "all":
        cursor.execute("""
            SELECT id, order_code, customer_name, total_amount, created_at, status
            FROM orders ORDER BY created_at DESC
        """)
    else:
        cursor.execute("""
            SELECT id, order_code, customer_name, total_amount, created_at, status
            FROM orders WHERE status = %s ORDER BY created_at DESC
        """, (status_filter,))
    orders = cursor.fetchall()
    conn.close()
    for order in orders:
        created = order['created_at'].strftime("%Y-%m-%d %H:%M") if order['created_at'] else ""
        status = order['status']
        tree.insert("", tk.END, iid=str(order['id']), values=(
            order['order_code'],
            order['customer_name'],
            f"₱{order['total_amount']:.2f}",
            created,
            status.capitalize()
        ), tags=(status,))
    tree.tag_configure("pending",   background="#fef9ec", foreground="#d35400")
    tree.tag_configure("waiting",   background="#eaf4fb", foreground="#2980b9")
    tree.tag_configure("completed", background="#eafaf1", foreground="#1e8449")
    tree.tag_configure("cancelled", background="#fdedec", foreground="#c0392b")
    details_card.clear()

def search_order_by_code(code, tree, details_card):
    code = code.strip()
    if not code:
        messagebox.showwarning("Search", "Please enter an order code.")
        return
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM orders WHERE order_code = %s", (code,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        messagebox.showwarning("Not Found", f"No order found with code: {code}")
        return
    order_id = str(result['id'])
    for item in tree.get_children():
        if item == order_id:
            tree.selection_set(order_id)
            tree.focus(order_id)
            tree.see(order_id)
            show_order_details(order_id, details_card)
            return
    show_order_details(order_id, details_card)

def show_order_details(order_id, details_card):
    if not order_id:
        return
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, order_code, customer_name, total_amount, created_at, status FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    if not order:
        conn.close()
        return
    cursor.execute("""
        SELECT m.name, oi.quantity, oi.price
        FROM order_items oi
        JOIN menu m ON oi.menu_id = m.id
        WHERE oi.order_id = %s
    """, (order_id,))
    items = cursor.fetchall()
    conn.close()
    details_card.display(order, items)

def confirm_order(order_id, tree, details_card, status_filter_var, from_modal=False):
    if not order_id:
        if not from_modal:
            messagebox.showwarning("No Selection", "Please select an order to confirm.")
        return False
    conn = connect_db()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
    status = cursor.fetchone()
    if not status or status[0] != 'pending':
        messagebox.showwarning("Invalid", "Only pending orders can be confirmed.")
        conn.close()
        return False
    if not messagebox.askyesno("Confirm Order", "Confirm this order? It will be added to the queue."):
        conn.close()
        return False
    try:
        cursor.execute("UPDATE orders SET status = 'waiting' WHERE id = %s", (order_id,))
        conn.commit()
        messagebox.showinfo("Success", "Order confirmed and added to queue.")
        refresh_orders(tree, details_card, status_filter_var.get())
        return True
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        conn.close()

def cancel_order(order_id, tree, details_card, status_filter_var, from_modal=False):
    if not order_id:
        if not from_modal:
            messagebox.showwarning("No Selection", "Please select an order to cancel.")
        return False
    conn = connect_db()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
    status = cursor.fetchone()
    if not status or status[0] != 'pending':
        messagebox.showwarning("Invalid", "Only pending orders can be cancelled.")
        conn.close()
        return False
    if not messagebox.askyesno("Cancel Order", "Cancel this order? Stock will be returned."):
        conn.close()
        return False
    try:
        cursor.execute("SELECT menu_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        items = cursor.fetchall()
        for menu_id, qty in items:
            cursor.execute("UPDATE menu SET stock = stock + %s WHERE id = %s", (qty, menu_id))
        cursor.execute("UPDATE orders SET status = 'cancelled' WHERE id = %s", (order_id,))
        conn.commit()
        messagebox.showinfo("Success", "Order cancelled. Stock returned.")
        refresh_orders(tree, details_card, status_filter_var.get())
        return True
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        conn.close()

def edit_order(order_id, tree, details_card, status_filter_var):
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, order_code, customer_name, total_amount, status FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    if not order:
        conn.close()
        messagebox.showerror("Error", "Order not found.")
        return
    if order['status'] != 'pending':
        conn.close()
        messagebox.showwarning("Invalid", "Only pending orders can be edited.")
        return
    cursor.execute("""
        SELECT oi.id as item_id, oi.menu_id, m.name, m.image_path, oi.quantity, oi.price, m.stock
        FROM order_items oi
        JOIN menu m ON oi.menu_id = m.id
        WHERE oi.order_id = %s
    """, (order_id,))
    order_items = cursor.fetchall()
    cursor.execute("SELECT id, name, price, stock, image_path FROM menu ORDER BY name")
    all_products = cursor.fetchall()
    conn.close()

    win = tk.Toplevel()
    win.title(f"Edit Order — {order['order_code']}")
    win.geometry("900x700")
    win.configure(bg="#f5f6fa")
    win.grab_set()
    win.resizable(False, False)

    header = tk.Frame(win, bg="#d35400", height=55)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(header, text=f"Edit Order — {order['order_code']}",
             font=("Segoe UI", 14, "bold"), bg="#d35400", fg="white").pack(side="left", padx=20, pady=12)

    body = tk.Frame(win, bg="#f5f6fa")
    body.pack(fill="both", expand=True, padx=16, pady=12)

    left = tk.Frame(body, bg="#f5f6fa")
    left.pack(side="left", fill="both", expand=True, padx=(0, 10))

    right = tk.Frame(body, bg="white", width=300, highlightthickness=1,
                     highlightbackground="#e0e0e0")
    right.pack(side="right", fill="y")
    right.pack_propagate(False)

    cart_header = tk.Frame(right, bg="#2c3e50", height=40)
    cart_header.pack(fill="x")
    cart_header.pack_propagate(False)
    tk.Label(cart_header, text="Current Order", font=("Segoe UI", 11, "bold"),
             bg="#2c3e50", fg="white").pack(side="left", padx=12, pady=8)

    cart_inner = tk.Frame(right, bg="white")
    cart_inner.pack(fill="both", expand=True, padx=10, pady=8)

    item_vars = {}
    for oi in order_items:
        item_vars[oi['menu_id']] = {
            'item_id': oi['item_id'],
            'name': oi['name'],
            'price': oi['price'],
            'qty': tk.IntVar(value=oi['quantity']),
            'max_stock': oi['stock'] + oi['quantity'],
        }

    total_lbl = tk.Label(right, text="Total: ₱0.00", font=("Segoe UI", 13, "bold"),
                         bg="white", fg="#d35400")
    total_lbl.pack(pady=6, padx=10, anchor="e")

    def refresh_cart():
        for w in cart_inner.winfo_children():
            w.destroy()
        total = 0
        for mid, data in item_vars.items():
            qty = data['qty'].get()
            if qty > 0:
                subtotal = data['price'] * qty
                total += subtotal
                row = tk.Frame(cart_inner, bg="white")
                row.pack(fill="x", pady=3)
                tk.Label(row, text=data['name'], font=("Segoe UI", 9, "bold"),
                         bg="white", fg="#2c3e50", anchor="w", wraplength=150).pack(side="left", fill="x", expand=True)
                tk.Label(row, text=f"×{qty}  ₱{subtotal:.2f}",
                         font=("Segoe UI", 9), bg="white", fg="#555").pack(side="right")
        total_lbl.config(text=f"Total: ₱{total:.2f}")

    tk.Label(left, text="Add / Adjust Products", font=("Segoe UI", 12, "bold"),
             bg="#f5f6fa", fg="#2c3e50").pack(anchor="w", pady=(0, 8))

    search_var = tk.StringVar()
    search_entry = tk.Entry(left, textvariable=search_var, font=("Segoe UI", 10),
                            bd=0, relief="flat", highlightthickness=1,
                            highlightbackground="#ccc", highlightcolor="#d35400",
                            bg="white", width=30)
    search_entry.pack(fill="x", ipady=6, pady=(0, 8))

    prod_canvas = tk.Canvas(left, bg="#f5f6fa", highlightthickness=0)
    prod_scroll = ttk.Scrollbar(left, orient="vertical", command=prod_canvas.yview)
    prod_frame = tk.Frame(prod_canvas, bg="#f5f6fa")
    prod_frame.bind("<Configure>", lambda e: prod_canvas.configure(scrollregion=prod_canvas.bbox("all")))
    prod_canvas.create_window((0, 0), window=prod_frame, anchor="nw")
    prod_canvas.configure(yscrollcommand=prod_scroll.set)
    prod_canvas.pack(side="left", fill="both", expand=True)
    prod_scroll.pack(side="right", fill="y")

    product_widgets = {}

    def render_products(filter_text=""):
        for w in prod_frame.winfo_children():
            w.destroy()
        cols = 3
        filtered = [p for p in all_products if filter_text.lower() in p['name'].lower()]
        for i, prod in enumerate(filtered):
            row = i // cols
            col = i % cols
            mid = prod['id']

            card = tk.Frame(prod_frame, bg="white", highlightthickness=1,
                            highlightbackground="#e0e0e0")
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            prod_frame.columnconfigure(col, weight=1)

            img_box = tk.Frame(card, bg="#f0f2f5", width=100, height=80)
            img_box.pack(fill="x")
            img_box.pack_propagate(False)
            img_path = prod.get('image_path')
            if img_path and os.path.exists(img_path):
                try:
                    pil_img = Image.open(img_path)
                    pil_img.thumbnail((100, 80))
                    photo = ImageTk.PhotoImage(pil_img)
                    lbl_img = tk.Label(img_box, image=photo, bg="#f0f2f5")
                    lbl_img.image = photo
                    lbl_img.pack(expand=True)
                except Exception:
                    tk.Label(img_box, text="No Image", bg="#f0f2f5", fg="#bbb",
                             font=("Segoe UI", 8)).pack(expand=True)
            else:
                tk.Label(img_box, text="No Image", bg="#f0f2f5", fg="#bbb",
                         font=("Segoe UI", 8)).pack(expand=True)

            info = tk.Frame(card, bg="white", padx=6, pady=4)
            info.pack(fill="x")
            tk.Label(info, text=prod['name'], font=("Segoe UI", 9, "bold"),
                     bg="white", fg="#2c3e50", wraplength=110, anchor="w").pack(fill="x")
            tk.Label(info, text=f"₱{prod['price']:.2f}", font=("Segoe UI", 9),
                     bg="white", fg="#d35400", anchor="w").pack(fill="x")
            avail_stock = prod['stock']
            if mid in item_vars:
                avail_stock = item_vars[mid]['max_stock']
            stock_color = "#27ae60" if avail_stock > 5 else "#e67e22" if avail_stock > 0 else "#e74c3c"
            tk.Label(info, text=f"Stock: {avail_stock}", font=("Segoe UI", 8),
                     bg="white", fg=stock_color, anchor="w").pack(fill="x")

            qty_row = tk.Frame(card, bg="white", padx=6)
            qty_row.pack(fill="x", pady=(0, 6))

            if mid not in item_vars:
                item_vars[mid] = {
                    'item_id': None,
                    'name': prod['name'],
                    'price': prod['price'],
                    'qty': tk.IntVar(value=0),
                    'max_stock': avail_stock,
                }

            cur_qty = item_vars[mid]['qty'].get()

            def make_dec(m=mid):
                def dec():
                    v = item_vars[m]['qty'].get()
                    if v > 0:
                        item_vars[m]['qty'].set(v - 1)
                    refresh_cart()
                    render_products(search_var.get())
                return dec

            def make_inc(m=mid):
                def inc():
                    v = item_vars[m]['qty'].get()
                    if v < item_vars[m]['max_stock']:
                        item_vars[m]['qty'].set(v + 1)
                    refresh_cart()
                    render_products(search_var.get())
                return inc

            tk.Button(qty_row, text="−", font=("Segoe UI", 10, "bold"),
                      bg="#f0f2f5", fg="#2c3e50", relief="flat", cursor="hand2",
                      width=2, command=make_dec()).pack(side="left")
            qty_lbl = tk.Label(qty_row, text=str(cur_qty), font=("Segoe UI", 10, "bold"),
                               bg="white", fg="#2c3e50", width=3)
            qty_lbl.pack(side="left", padx=4)
            tk.Button(qty_row, text="+", font=("Segoe UI", 10, "bold"),
                      bg="#f0f2f5", fg="#2c3e50", relief="flat", cursor="hand2",
                      width=2, command=make_inc()).pack(side="left")
            product_widgets[mid] = qty_lbl

    def on_search(*args):
        render_products(search_var.get())

    search_var.trace_add("write", on_search)
    render_products()
    refresh_cart()

    def save_edits():
        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
            total = 0
            for mid, data in item_vars.items():
                qty = data['qty'].get()
                if qty > 0:
                    cursor.execute("""
                        INSERT INTO order_items (order_id, menu_id, quantity, price)
                        VALUES (%s, %s, %s, %s)
                    """, (order_id, mid, qty, data['price']))
                    total += data['price'] * qty

            cursor.execute("SELECT menu_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
            new_items = {row[0]: row[1] for row in cursor.fetchall()}

            orig_qtys = {oi['menu_id']: oi['quantity'] for oi in order_items}
            all_mids = set(list(orig_qtys.keys()) + list(new_items.keys()))
            for mid in all_mids:
                old_q = orig_qtys.get(mid, 0)
                new_q = new_items.get(mid, 0)
                diff = old_q - new_q
                if diff != 0:
                    cursor.execute("UPDATE menu SET stock = stock + %s WHERE id = %s", (diff, mid))

            cursor.execute("UPDATE orders SET total_amount = %s WHERE id = %s", (total, order_id))
            conn.commit()
            messagebox.showinfo("Success", "Order updated successfully.")
            win.destroy()
            refresh_orders(tree, details_card, status_filter_var.get())
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    btn_bar = tk.Frame(win, bg="#f5f6fa", padx=16)
    btn_bar.pack(fill="x", pady=(0, 12))
    tk.Button(btn_bar, text="Save Changes", bg="#d35400", fg="white",
              font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
              pady=8, command=save_edits).pack(fill="x")


class OrderDetailsCard(tk.Frame):
    def __init__(self, parent, tree, status_filter_var):
        super().__init__(parent, bg="white", highlightthickness=1, highlightbackground="#e0e0e0")
        self.tree = tree
        self.status_filter_var = status_filter_var
        self.order_id = None
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        header = tk.Frame(self, bg="#2c3e50", height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Order Details", font=("Segoe UI", 13, "bold"),
                 bg="#2c3e50", fg="white").pack(side="left", padx=16, pady=10)

        self.placeholder = tk.Frame(self, bg="white")
        self.placeholder.pack(fill="both", expand=True)
        tk.Label(self.placeholder, text="Select an order\nto view details",
                 font=("Segoe UI", 11), bg="white", fg="#bbb").pack(expand=True)

        self.body = tk.Frame(self, bg="white")

        meta = tk.Frame(self.body, bg="white", padx=16, pady=12)
        meta.pack(fill="x")

        self.lbl_code     = tk.Label(meta, text="", font=("Segoe UI", 10), bg="white", fg="#555", anchor="w")
        self.lbl_customer = tk.Label(meta, text="", font=("Segoe UI", 10), bg="white", fg="#555", anchor="w")
        self.lbl_date     = tk.Label(meta, text="", font=("Segoe UI", 10), bg="white", fg="#555", anchor="w")
        self.lbl_total    = tk.Label(meta, text="", font=("Segoe UI", 14, "bold"), bg="white", fg="#d35400", anchor="w")
        self.lbl_status   = tk.Label(meta, text="", font=("Segoe UI", 10, "bold"), bg="white", anchor="w")

        for lbl in (self.lbl_code, self.lbl_customer, self.lbl_date, self.lbl_total, self.lbl_status):
            lbl.pack(fill="x", pady=2)

        tk.Frame(self.body, bg="#eee", height=1).pack(fill="x", padx=16, pady=6)

        items_outer = tk.Frame(self.body, bg="white", padx=16)
        items_outer.pack(fill="both", expand=True)
        tk.Label(items_outer, text="Items", font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#2c3e50").pack(anchor="w", pady=(0, 4))

        self.items_text = tk.Text(items_outer, font=("Segoe UI", 9), height=9,
                                  wrap=tk.WORD, bd=0, relief="flat",
                                  bg="#f8f9fa", fg="#2c3e50", padx=8, pady=6)
        self.items_text.pack(fill="both", expand=True)
        self.items_text.config(state="disabled")

        btn_row = tk.Frame(self.body, bg="white", padx=16)
        btn_row.pack(fill="x", pady=12)

        self.edit_btn = tk.Button(btn_row, text="✎", bg="#2980b9", fg="white",
                                  font=("Segoe UI", 12), relief="flat",
                                  cursor="hand2", padx=10, pady=6, command=self._edit)
        self.edit_btn.pack(side="left", padx=(0, 8))

        self.confirm_btn = tk.Button(btn_row, text="✔ Confirm", bg="#27ae60", fg="white",
                                     font=("Segoe UI", 10, "bold"), relief="flat",
                                     cursor="hand2", padx=14, pady=6, command=self._confirm)
        self.confirm_btn.pack(side="left", padx=(0, 8))

        self.cancel_btn = tk.Button(btn_row, text="✖ Cancel", bg="#e74c3c", fg="white",
                                    font=("Segoe UI", 10, "bold"), relief="flat",
                                    cursor="hand2", padx=14, pady=6, command=self._cancel)
        self.cancel_btn.pack(side="left")

    def clear(self):
        self.order_id = None
        self.body.pack_forget()
        self.placeholder.pack(fill="both", expand=True)

    def display(self, order, items):
        self.order_id = order['id']
        self.placeholder.pack_forget()
        self.body.pack(fill="both", expand=True)

        self.lbl_code.config(text=f"Order Code:  {order['order_code']}")
        self.lbl_customer.config(text=f"Customer:  {order['customer_name']}")
        date_str = order['created_at'].strftime("%b %d, %Y  %H:%M") if order['created_at'] else ""
        self.lbl_date.config(text=f"Date:  {date_str}")
        self.lbl_total.config(text=f"₱{order['total_amount']:.2f}")

        status = order['status']
        sc = STATUS_COLORS.get(status, {})
        self.lbl_status.config(text=f"● {status.capitalize()}", fg=sc.get("badge", "#555"))

        self.items_text.config(state="normal")
        self.items_text.delete(1.0, tk.END)
        for item in items:
            subtotal = item['price'] * item['quantity']
            self.items_text.insert(tk.END, f"  {item['name']}  ×{item['quantity']}  =  ₱{subtotal:.2f}\n")
        self.items_text.config(state="disabled")

        is_pending = status == 'pending'
        self.edit_btn.config(state="normal" if is_pending else "disabled",
                             bg="#2980b9" if is_pending else "#aaa")
        self.confirm_btn.config(state="normal" if is_pending else "disabled",
                                bg="#27ae60" if is_pending else "#aaa")
        self.cancel_btn.config(state="normal" if is_pending else "disabled",
                               bg="#e74c3c" if is_pending else "#aaa")

    def _edit(self):
        edit_order(self.order_id, self.tree, self, self.status_filter_var)

    def _confirm(self):
        confirm_order(self.order_id, self.tree, self, self.status_filter_var)

    def _cancel(self):
        cancel_order(self.order_id, self.tree, self, self.status_filter_var)


def show_order_modal(order_id, tree, details_card, status_filter_var):
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, order_code, customer_name, total_amount, created_at, status FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    if not order:
        conn.close()
        messagebox.showerror("Error", "Order not found.")
        return
    cursor.execute("""
        SELECT m.name, oi.quantity, oi.price
        FROM order_items oi
        JOIN menu m ON oi.menu_id = m.id
        WHERE oi.order_id = %s
    """, (order_id,))
    items = cursor.fetchall()
    conn.close()

    modal = tk.Toplevel()
    modal.title("Order Details")
    modal.geometry("480x540")
    modal.configure(bg="#f5f6fa")
    modal.grab_set()
    modal.resizable(False, False)

    status = order['status']
    sc = STATUS_COLORS.get(status, {})

    header = tk.Frame(modal, bg="#2c3e50", height=55)
    header.pack(fill="x")
    tk.Label(header, text="Order Information", font=("Segoe UI", 14, "bold"),
             bg="#2c3e50", fg="white").pack(side="left", padx=20, pady=12)

    body = tk.Frame(modal, bg="#f5f6fa", padx=24, pady=16)
    body.pack(fill="both", expand=True)

    tk.Label(body, text=f"  ● {status.capitalize()}  ",
             font=("Segoe UI", 10, "bold"),
             bg=sc.get("bg", "#eee"), fg=sc.get("badge", "#333")).pack(anchor="w", pady=(0, 10))

    for label, value in [
        ("Order Code", order['order_code']),
        ("Customer",   order['customer_name']),
        ("Date",       order['created_at'].strftime("%b %d, %Y  %H:%M") if order['created_at'] else ""),
        ("Total",      f"₱{order['total_amount']:.2f}"),
    ]:
        row = tk.Frame(body, bg="#f5f6fa")
        row.pack(fill="x", pady=2)
        tk.Label(row, text=f"{label}:", font=("Segoe UI", 10), bg="#f5f6fa",
                 fg="#888", width=12, anchor="w").pack(side="left")
        tk.Label(row, text=value, font=("Segoe UI", 10, "bold"), bg="#f5f6fa",
                 fg="#d35400" if label == "Total" else "#2c3e50").pack(side="left")

    tk.Frame(body, bg="#ddd", height=1).pack(fill="x", pady=10)
    tk.Label(body, text="Items", font=("Segoe UI", 10, "bold"),
             bg="#f5f6fa", fg="#2c3e50").pack(anchor="w", pady=(0, 4))

    items_text = tk.Text(body, font=("Segoe UI", 9), height=8, wrap=tk.WORD,
                         bd=0, relief="flat", bg="#eef0f3", fg="#2c3e50", padx=8, pady=6)
    items_text.pack(fill="both", expand=True)
    for item in items:
        items_text.insert(tk.END, f"  {item['name']}  ×{item['quantity']}  =  ₱{item['price']*item['quantity']:.2f}\n")
    items_text.config(state="disabled")

    btn_row = tk.Frame(modal, bg="#f5f6fa", padx=24)
    btn_row.pack(fill="x", pady=(0, 16))

    def modal_confirm():
        if confirm_order(order['id'], tree, details_card, status_filter_var, from_modal=True):
            modal.destroy()

    def modal_cancel():
        if cancel_order(order['id'], tree, details_card, status_filter_var, from_modal=True):
            modal.destroy()

    def modal_edit():
        modal.destroy()
        edit_order(order['id'], tree, details_card, status_filter_var)

    if status == 'pending':
        tk.Button(btn_row, text="✎", bg="#2980b9", fg="white",
                  font=("Segoe UI", 12), relief="flat", cursor="hand2",
                  padx=10, pady=7, command=modal_edit).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="✔ Confirm", bg="#27ae60", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                  padx=14, pady=7, command=modal_confirm).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="✖ Cancel", bg="#e74c3c", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                  padx=14, pady=7, command=modal_cancel).pack(side="left")

    tk.Button(btn_row, text="Close", bg="#95a5a6", fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
              padx=14, pady=7, command=modal.destroy).pack(side="right")


def scan_qr_camera(tree, details_card, status_filter_var):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Cannot open camera.")
        return

    scan_win = tk.Toplevel()
    scan_win.title("Scan QR Code")
    scan_win.geometry("660x520")
    scan_win.configure(bg="#1a1a2e")
    scan_win.resizable(False, False)

    tk.Label(scan_win, text="Position QR code in front of camera",
             font=("Segoe UI", 11), bg="#1a1a2e", fg="#aaa").pack(pady=(12, 4))

    video_label = tk.Label(scan_win, bg="#1a1a2e")
    video_label.pack()

    status_lbl = tk.Label(scan_win, text="Scanning...", font=("Segoe UI", 10),
                          bg="#1a1a2e", fg="#f39c12")
    status_lbl.pack(pady=6)

    tk.Button(scan_win, text="Cancel", bg="#e74c3c", fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
              padx=20, pady=6, command=lambda: stop_scan()).pack()

    scanning = True

    def stop_scan():
        nonlocal scanning
        scanning = False
        cap.release()
        scan_win.destroy()

    def update_frame():
        if not scanning:
            return
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            for obj in decode(gray):
                qr_data = obj.data.decode('utf-8')
                match = re.search(r'code=([A-Za-z0-9]+)', qr_data)
                order_code = match.group(1) if match else qr_data
                conn = connect_db()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT id FROM orders WHERE order_code = %s", (order_code,))
                    result = cursor.fetchone()
                    conn.close()
                    if result:
                        stop_scan()
                        show_order_modal(result['id'], tree, details_card, status_filter_var)
                        return
                    else:
                        status_lbl.config(text=f"Order '{order_code}' not found.", fg="#e74c3c")
                break
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imgtk = ImageTk.PhotoImage(image=Image.fromarray(img_rgb))
            video_label.imgtk = imgtk
            video_label.config(image=imgtk)
        scan_win.after(30, update_frame)

    scan_win.after(30, update_frame)
    scan_win.protocol("WM_DELETE_WINDOW", stop_scan)


def direct_order(tree, details_card, status_filter_var):
    direct_win = tk.Toplevel()
    direct_win.title("Direct Order (POS)")
    direct_win.geometry("1050x780")
    direct_win.configure(bg="#f5f6fa")
    direct_win.grab_set()

    header = tk.Frame(direct_win, bg="#2c3e50", height=55)
    header.pack(fill="x")
    tk.Label(header, text="Direct Order — POS", font=("Segoe UI", 14, "bold"),
             bg="#2c3e50", fg="white").pack(side="left", padx=20, pady=12)

    main_frame = tk.Frame(direct_win, bg="#f5f6fa")
    main_frame.pack(fill="both", expand=True, padx=16, pady=12)

    products_frame = tk.Frame(main_frame, bg="#f5f6fa")
    products_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(products_frame, bg="#f5f6fa", highlightthickness=0)
    scrollbar = ttk.Scrollbar(products_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#f5f6fa")
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    product_vars = {}
    conn = connect_db()
    if not conn:
        direct_win.destroy()
        return
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, price, stock, image_path FROM menu ORDER BY name")
    products = cursor.fetchall()
    conn.close()

    cols = 4
    for i, prod in enumerate(products):
        row = i // cols
        col = i % cols

        card = tk.Frame(scrollable_frame, bg="white", highlightthickness=1,
                        highlightbackground="#e0e0e0")
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        scrollable_frame.columnconfigure(col, weight=1)

        img_box = tk.Frame(card, bg="#f0f2f5", width=110, height=100)
        img_box.pack(fill="x")
        img_box.pack_propagate(False)

        img_path = prod.get('image_path')
        if img_path and os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path)
                pil_img.thumbnail((110, 100))
                img = ImageTk.PhotoImage(pil_img)
                lbl = tk.Label(img_box, image=img, bg="#f0f2f5")
                lbl.image = img
                lbl.pack(expand=True)
            except Exception:
                tk.Label(img_box, text="No Image", bg="#f0f2f5", fg="#bbb",
                         font=("Segoe UI", 8)).pack(expand=True)
        else:
            tk.Label(img_box, text="No Image", bg="#f0f2f5", fg="#bbb",
                     font=("Segoe UI", 8)).pack(expand=True)

        info = tk.Frame(card, bg="white", padx=8, pady=6)
        info.pack(fill="x")
        tk.Label(info, text=prod['name'], font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#2c3e50", wraplength=120, anchor="w").pack(fill="x")
        tk.Label(info, text=f"₱{prod['price']:.2f}", font=("Segoe UI", 10),
                 bg="white", fg="#d35400", anchor="w").pack(fill="x")

        stock = prod['stock'] if prod['stock'] else 0
        stock_color = "#27ae60" if stock > 10 else "#e67e22" if stock > 0 else "#e74c3c"
        tk.Label(info, text=f"Stock: {stock}", font=("Segoe UI", 8),
                 bg="white", fg=stock_color, anchor="w").pack(fill="x")

        qty_frame = tk.Frame(card, bg="white", padx=8)
        qty_frame.pack(fill="x", pady=(0, 8))
        tk.Label(qty_frame, text="Qty:", font=("Segoe UI", 9),
                 bg="white", fg="#555").pack(side="left")
        spinbox = tk.Spinbox(qty_frame, from_=0, to=stock, width=5,
                             state="readonly", font=("Segoe UI", 10))
        spinbox.pack(side="left", padx=6)
        product_vars[prod['id']] = {'spin': spinbox, 'price': prod['price'], 'name': prod['name']}

    cart_frame = tk.Frame(main_frame, bg="white", highlightthickness=1,
                          highlightbackground="#e0e0e0")
    cart_frame.pack(fill="x", pady=(10, 0))

    cart_header = tk.Frame(cart_frame, bg="#2c3e50", height=36)
    cart_header.pack(fill="x")
    cart_header.pack_propagate(False)
    tk.Label(cart_header, text="Cart", font=("Segoe UI", 11, "bold"),
             bg="#2c3e50", fg="white").pack(side="left", padx=12, pady=6)

    cart_listbox = tk.Listbox(cart_frame, height=5, font=("Segoe UI", 9),
                              bd=0, relief="flat", bg="white", fg="#2c3e50",
                              selectbackground="#d35400", selectforeground="white")
    cart_listbox.pack(fill="x", padx=12, pady=8)

    totals_row = tk.Frame(cart_frame, bg="white", padx=12)
    totals_row.pack(fill="x", pady=(0, 8))
    total_label = tk.Label(totals_row, text="Total: ₱0.00",
                           font=("Segoe UI", 13, "bold"), bg="white", fg="#d35400")
    total_label.pack(side="left")

    payment_frame = tk.Frame(cart_frame, bg="white", padx=12)
    payment_frame.pack(fill="x", pady=(0, 8))

    tk.Label(payment_frame, text="Amount Paid:", font=("Segoe UI", 10),
             bg="white", fg="#555").pack(side="left")
    paid_entry = tk.Entry(payment_frame, width=12, font=("Segoe UI", 11),
                          bd=0, relief="flat", highlightthickness=1,
                          highlightbackground="#ccc", highlightcolor="#d35400", bg="white")
    paid_entry.pack(side="left", padx=8, ipady=5)

    tk.Label(payment_frame, text="Change:", font=("Segoe UI", 10),
             bg="white", fg="#555").pack(side="left")
    change_label = tk.Label(payment_frame, text="₱0.00",
                            font=("Segoe UI", 11, "bold"), bg="white", fg="#27ae60")
    change_label.pack(side="left", padx=8)

    def update_cart():
        cart_listbox.delete(0, tk.END)
        total = 0
        for pid, data in product_vars.items():
            qty = int(data['spin'].get())
            if qty > 0:
                subtotal = data['price'] * qty
                total += subtotal
                cart_listbox.insert(tk.END, f"  {data['name']}  ×{qty}  =  ₱{subtotal:.2f}")
        total_label.config(text=f"Total: ₱{total:.2f}")
        try:
            paid = float(paid_entry.get()) if paid_entry.get() else 0
            change = paid - total if paid >= total else 0
            change_label.config(text=f"₱{change:.2f}",
                                fg="#27ae60" if paid >= total else "#e74c3c")
        except Exception:
            change_label.config(text="₱0.00")

    def update_change(event=None):
        try:
            total = float(total_label.cget("text").split("₱")[1])
            paid = float(paid_entry.get()) if paid_entry.get() else 0
            change = paid - total if paid >= total else 0
            change_label.config(text=f"₱{change:.2f}",
                                fg="#27ae60" if paid >= total else "#e74c3c")
        except Exception:
            change_label.config(text="₱0.00")

    for data in product_vars.values():
        data['spin'].config(command=update_cart)
    paid_entry.bind("<KeyRelease>", update_change)

    def place_direct_order():
        cart = {pid: {'name': d['name'], 'price': d['price'], 'quantity': int(d['spin'].get())}
                for pid, d in product_vars.items() if int(d['spin'].get()) > 0}
        if not cart:
            messagebox.showerror("Error", "No items selected.")
            return
        total = sum(i['price'] * i['quantity'] for i in cart.values())
        try:
            paid = float(paid_entry.get()) if paid_entry.get() else 0
        except Exception:
            messagebox.showerror("Error", "Invalid payment amount.")
            return
        if paid < total:
            messagebox.showerror("Error", f"Amount paid (₱{paid:.2f}) is less than total (₱{total:.2f}).")
            return

        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        errors = []
        for pid, item in cart.items():
            cursor.execute("SELECT stock FROM menu WHERE id = %s", (pid,))
            stock = cursor.fetchone()[0]
            if item['quantity'] > stock:
                errors.append(f"{item['name']} (only {stock} left)")
        if errors:
            messagebox.showerror("Stock Error", "Insufficient stock:\n" + "\n".join(errors))
            conn.close()
            return

        order_code = 'ORD' + str(int(datetime.now().timestamp())) + str(random.randint(100, 999))
        cursor.execute("INSERT INTO orders (order_code, customer_name, total_amount) VALUES (%s, %s, %s)",
                       (order_code, "Direct", total))
        order_id = cursor.lastrowid
        for pid, item in cart.items():
            cursor.execute("INSERT INTO order_items (order_id, menu_id, quantity, price) VALUES (%s, %s, %s, %s)",
                           (order_id, pid, item['quantity'], item['price']))
            cursor.execute("UPDATE menu SET stock = stock - %s WHERE id = %s", (item['quantity'], pid))
        conn.commit()
        conn.close()

        if not os.path.exists('qr_codes'):
            os.makedirs('qr_codes')
        qr_data = f"http://{socket.gethostname()}.local/app/staff_scan.php?code={order_code}"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(qr_data)}"
        try:
            with urllib.request.urlopen(qr_url) as response:
                with open(f"qr_codes/{order_code}.png", 'wb') as f:
                    f.write(response.read())
        except Exception:
            pass

        change = paid - float(total)
        messagebox.showinfo("Order Placed",
                            f"Order Code: {order_code}\nTotal: ₱{total:.2f}\nPaid: ₱{paid:.2f}\nChange: ₱{change:.2f}")
        direct_win.destroy()
        refresh_orders(tree, details_card, status_filter_var.get())

    btn_frame = tk.Frame(direct_win, bg="#f5f6fa", padx=16)
    btn_frame.pack(fill="x", pady=(0, 12))
    tk.Button(btn_frame, text="PLACE ORDER", bg="#d35400", fg="white",
              font=("Segoe UI", 12, "bold"), relief="flat", cursor="hand2",
              pady=10, command=place_direct_order).pack(fill="x")


def main():
    win = tk.Tk()
    win.title("Staff - Orders Management")
    win.geometry("1400x800")
    win.configure(bg="#f5f6fa")
    add_staff_sidebar(win)

    content_frame = tk.Frame(win, bg="#f5f6fa")
    content_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    top_bar = tk.Frame(content_frame, bg="#f5f6fa")
    top_bar.pack(fill="x", pady=(0, 10))
    tk.Label(top_bar, text="Orders Management", font=("Segoe UI", 22, "bold"),
             fg="#d35400", bg="#f5f6fa").pack(side="left")

    tk.Frame(content_frame, bg="#ddd", height=1).pack(fill="x", pady=(0, 12))

    status_filter_var = tk.StringVar(value="pending")

    filter_bar = tk.Frame(content_frame, bg="#f5f6fa")
    filter_bar.pack(fill="x", pady=(0, 8))

    filter_buttons = {}

    main_panel = tk.Frame(content_frame, bg="#f5f6fa")
    main_panel.pack(fill="both", expand=True)

    left_frame = tk.Frame(main_panel, bg="#f5f6fa")
    left_frame.pack(side="left", fill="both", expand=True, padx=(0, 12))

    tree_frame = tk.Frame(left_frame, bg="#f5f6fa")
    tree_frame.pack(fill="both", expand=True)

    style = ttk.Style()
    style.configure("Orders.Treeview", background="white", foreground="#2c3e50",
                    rowheight=30, fieldbackground="white", font=("Segoe UI", 10))
    style.configure("Orders.Treeview.Heading", font=("Segoe UI", 10, "bold"),
                    foreground="#d35400")
    style.map("Orders.Treeview", background=[("selected", "#2c3e50")],
              foreground=[("selected", "white")])

    scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
    scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")

    columns = ("Order Code", "Customer", "Total", "Date", "Status")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                        style="Orders.Treeview",
                        yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    scroll_y.config(command=tree.yview)
    scroll_x.config(command=tree.xview)
    scroll_y.pack(side="right", fill="y")
    scroll_x.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)

    col_widths = {"Order Code": 150, "Customer": 160, "Total": 100, "Date": 140, "Status": 100}
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=col_widths[col],
                    anchor="w" if col == "Customer" else "center")

    right_frame = tk.Frame(main_panel, bg="#f5f6fa", width=380)
    right_frame.pack(side="right", fill="both")
    right_frame.pack_propagate(False)

    details_card = OrderDetailsCard(right_frame, tree, status_filter_var)

    action_bar = tk.Frame(left_frame, bg="#f5f6fa")
    action_bar.pack(fill="x", pady=(8, 0))

    tk.Button(action_bar, text="⟳ Refresh", bg="#2c3e50", fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
              padx=14, pady=6,
              command=lambda: refresh_orders(tree, details_card, status_filter_var.get())).pack(side="left", padx=(0, 8))
    tk.Button(action_bar, text="📷 Scan QR", bg="#2c3e50", fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
              padx=14, pady=6,
              command=lambda: scan_qr_camera(tree, details_card, status_filter_var)).pack(side="left", padx=(0, 8))
    tk.Button(action_bar, text="＋ Direct Order", bg="#d35400", fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
              padx=14, pady=6,
              command=lambda: direct_order(tree, details_card, status_filter_var)).pack(side="left")

    search_frame = tk.Frame(action_bar, bg="#f5f6fa")
    search_frame.pack(side="right")

    search_entry = tk.Entry(search_frame, font=("Segoe UI", 10), width=20,
                            bd=0, relief="flat", highlightthickness=1,
                            highlightbackground="#ccc", highlightcolor="#d35400", bg="white")
    search_entry.pack(side="left", ipady=6, padx=(0, 6))
    search_entry.insert(0, "Search order code...")
    search_entry.config(fg="#aaa")

    def on_focus_in(e):
        if search_entry.get() == "Search order code...":
            search_entry.delete(0, tk.END)
            search_entry.config(fg="#2c3e50")

    def on_focus_out(e):
        if not search_entry.get():
            search_entry.insert(0, "Search order code...")
            search_entry.config(fg="#aaa")

    search_entry.bind("<FocusIn>", on_focus_in)
    search_entry.bind("<FocusOut>", on_focus_out)
    search_entry.bind("<Return>", lambda e: search_order_by_code(
        search_entry.get() if search_entry.get() != "Search order code..." else "",
        tree, details_card))

    tk.Button(search_frame, text="Search", bg="#2980b9", fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
              padx=12, pady=6,
              command=lambda: search_order_by_code(
                  search_entry.get() if search_entry.get() != "Search order code..." else "",
                  tree, details_card)).pack(side="left")

    def set_filter(status):
        status_filter_var.set(status)
        for s, b in filter_buttons.items():
            sc = STATUS_COLORS.get(s, {})
            if s == status:
                b.config(bg=sc.get("badge", "#2c3e50"), fg="white")
            else:
                b.config(bg="white", fg=sc.get("badge", "#555"))
        refresh_orders(tree, details_card, status)

    for label, value in [("Pending", "pending"), ("Waiting", "waiting"),
                         ("Completed", "completed"), ("Cancelled", "cancelled"), ("All", "all")]:
        sc = STATUS_COLORS.get(value, {"badge": "#2c3e50"})
        b = tk.Button(filter_bar, text=label,
                      font=("Segoe UI", 10, "bold"), relief="flat",
                      cursor="hand2", padx=16, pady=6,
                      command=lambda v=value: set_filter(v))
        b.pack(side="left", padx=(0, 6))
        filter_buttons[value] = b

    def on_tree_select(event):
        selected = tree.selection()
        if selected:
            show_order_details(selected[0], details_card)

    tree.bind("<<TreeviewSelect>>", on_tree_select)

    set_filter("pending")
    win.mainloop()

if __name__ == "__main__":
    main()