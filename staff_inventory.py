import tkinter as tk
from tkinter import ttk, messagebox
from staff_sidebar import add_staff_sidebar
import mysql.connector
import os
from PIL import Image, ImageTk

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

def add_stock(product_id, product_name, current_stock, card_container, menu_id_map):
    win = tk.Toplevel()
    win.title("Add Stock")
    win.geometry("420x280")
    win.configure(bg="#f5f6fa")
    win.grab_set()
    win.resizable(False, False)

    header = tk.Frame(win, bg="#2c3e50", height=55)
    header.pack(fill="x")
    tk.Label(header, text=f"Add Stock — {product_name}", font=("Segoe UI", 13, "bold"),
             bg="#2c3e50", fg="white").pack(side="left", padx=20, pady=12)

    form = tk.Frame(win, bg="#f5f6fa", padx=30, pady=20)
    form.pack(fill="both", expand=True)

    tk.Label(form, text=f"Current Stock:  {current_stock}", font=("Segoe UI", 11),
             bg="#f5f6fa", fg="#555").pack(anchor="w", pady=(0, 12))

    tk.Label(form, text="Quantity to Add", font=("Segoe UI", 10),
             bg="#f5f6fa", fg="#555").pack(anchor="w")

    entry_qty = tk.Entry(form, font=("Segoe UI", 12), bd=0, relief="flat",
                         highlightthickness=1, highlightbackground="#ccc",
                         highlightcolor="#d35400", bg="white", width=20)
    entry_qty.pack(fill="x", ipady=7, pady=(4, 0))
    entry_qty.focus()

    def save_stock():
        qty_str = entry_qty.get().strip()
        entry_qty.config(highlightbackground="#ccc")
        if not qty_str:
            entry_qty.config(highlightbackground="#e74c3c")
            messagebox.showerror("Validation Error", "Please enter a quantity.")
            return
        try:
            qty = int(qty_str)
            if qty <= 0:
                raise ValueError
        except ValueError:
            entry_qty.config(highlightbackground="#e74c3c")
            messagebox.showerror("Validation Error", "Quantity must be a positive whole number.")
            return

        new_stock = current_stock + qty
        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE menu SET stock = %s WHERE id = %s", (new_stock, product_id))
            conn.commit()
            messagebox.showinfo("Success", f"Stock updated! New stock: {new_stock}")
            win.destroy()
            refresh_inventory(card_container, menu_id_map)
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    btn_frame = tk.Frame(win, bg="#f5f6fa", padx=30, pady=5)
    btn_frame.pack(fill="x")
    tk.Button(btn_frame, text="Add Stock", bg="#d35400", fg="white",
              font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
              pady=8, command=save_stock).pack(fill="x")

def refresh_inventory(card_container, menu_id_map):
    for widget in card_container.winfo_children():
        widget.destroy()

    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock, image_path FROM menu ORDER BY name")
    items = cursor.fetchall()
    conn.close()

    menu_id_map.clear()
    cols = 4

    for idx, item in enumerate(items):
        menu_id, name, price, stock, img_path = item
        stock = stock if stock is not None else 0
        menu_id_map[menu_id] = True

        row = idx // cols
        col = idx % cols

        card = tk.Frame(card_container, bg="white", highlightthickness=1,
                        highlightbackground="#e0e0e0")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card_container.columnconfigure(col, weight=1)

        img_box = tk.Frame(card, bg="#f0f2f5", width=140, height=130)
        img_box.pack(fill="x")
        img_box.pack_propagate(False)

        if img_path and os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                img.thumbnail((140, 130))
                photo = ImageTk.PhotoImage(img)
                img_lbl = tk.Label(img_box, image=photo, bg="#f0f2f5")
                img_lbl.image = photo
                img_lbl.pack(expand=True)
            except Exception:
                tk.Label(img_box, text="No Image", bg="#f0f2f5",
                         fg="#bbb", font=("Segoe UI", 9)).pack(expand=True)
        else:
            tk.Label(img_box, text="No Image", bg="#f0f2f5",
                     fg="#bbb", font=("Segoe UI", 9)).pack(expand=True)

        info = tk.Frame(card, bg="white", padx=10, pady=8)
        info.pack(fill="x")

        tk.Label(info, text=name, font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#2c3e50", anchor="w", wraplength=140).pack(fill="x")
        tk.Label(info, text=f"₱{price:.2f}", font=("Segoe UI", 11),
                 bg="white", fg="#d35400", anchor="w").pack(fill="x")

        if stock > 10:
            stock_color, stock_bg, stock_text = "#1e8449", "#eafaf1", f"● In Stock ({stock})"
        elif stock > 0:
            stock_color, stock_bg, stock_text = "#d35400", "#fef5ec", f"● Low Stock ({stock})"
        else:
            stock_color, stock_bg, stock_text = "#c0392b", "#fdedec", "● Out of Stock"

        stock_badge = tk.Frame(info, bg=stock_bg, padx=6)
        stock_badge.pack(anchor="w", pady=(4, 0))
        tk.Label(stock_badge, text=stock_text, font=("Segoe UI", 9, "bold"),
                 bg=stock_bg, fg=stock_color).pack(pady=3)

        btn_row = tk.Frame(card, bg="white", padx=10)
        btn_row.pack(fill="x", pady=(0, 10))

        tk.Button(btn_row, text="+ Add Stock", bg="#3498db", fg="white",
                  font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                  padx=12, pady=4,
                  command=lambda pid=menu_id, pname=name, curr=stock: add_stock(
                      pid, pname, curr, card_container, menu_id_map)
                  ).pack(fill="x")

def main():
    win = tk.Tk()
    win.title("Staff - Inventory Management")
    win.geometry("1280x720")
    win.configure(bg="#f5f6fa")

    add_staff_sidebar(win)

    content_frame = tk.Frame(win, bg="#f5f6fa")
    content_frame.pack(side="right", fill="both", expand=True)

    top_bar = tk.Frame(content_frame, bg="#f5f6fa")
    top_bar.pack(fill="x", padx=25, pady=(20, 0))

    tk.Label(top_bar, text="Inventory Management", font=("Segoe UI", 22, "bold"),
             fg="#d35400", bg="#f5f6fa").pack(side="left")

    tk.Frame(content_frame, bg="#ddd", height=1).pack(fill="x", padx=25, pady=12)

    canvas = tk.Canvas(content_frame, bg="#f5f6fa", highlightthickness=0)
    scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#f5f6fa")

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True, padx=20, pady=10)
    scrollbar.pack(side="right", fill="y")

    card_container = tk.Frame(scrollable_frame, bg="#f5f6fa")
    card_container.pack(fill="both", expand=True, padx=5, pady=5)

    menu_id_map = {}
    refresh_inventory(card_container, menu_id_map)

    win.mainloop()

if __name__ == "__main__":
    main()