import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from sidebar import add_sidebar
import mysql.connector
import os
import shutil
from PIL import Image, ImageTk

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "app"
}

IMAGE_FOLDER = "menu_images"
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

def connect_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Connection failed: {err}")
        return None

def get_categories():
    conn = connect_db()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories ORDER BY name")
    cats = cursor.fetchall()
    conn.close()
    return cats

def save_uploaded_image(file_path):
    if not file_path:
        return ""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
        messagebox.showerror("Error", "Only image files (jpg, jpeg, png, gif) are allowed.")
        return None
    filename = f"menu_{int(os.path.getmtime(file_path))}{ext}"
    dest_path = os.path.join(IMAGE_FOLDER, filename)
    shutil.copy(file_path, dest_path)
    return dest_path

def styled_modal(title, geometry="520x600"):
    win = tk.Toplevel()
    win.title(title)
    win.geometry(geometry)
    win.configure(bg="#f5f6fa")
    win.grab_set()
    win.resizable(False, False)
    return win

def styled_header(parent, text, bg="#d35400"):
    header = tk.Frame(parent, bg=bg, height=55)
    header.pack(fill="x")
    tk.Label(header, text=text, font=("Segoe UI", 14, "bold"), bg=bg, fg="white").pack(side="left", padx=20, pady=12)

def styled_field(parent, label, row, show=None):
    tk.Label(parent, text=label, font=("Segoe UI", 10), bg="#f5f6fa", fg="#555").grid(
        row=row, column=0, sticky="w", pady=6, padx=(0, 12))
    entry = tk.Entry(parent, font=("Segoe UI", 11), bd=0, relief="flat",
                     highlightthickness=1, highlightbackground="#ccc",
                     highlightcolor="#d35400", bg="white", width=30)
    if show:
        entry.config(show=show)
    entry.grid(row=row, column=1, pady=6, ipady=6, sticky="ew", padx=(0, 5))
    return entry

def styled_button(parent, text, command, bg="#d35400"):
    return tk.Button(parent, text=text, bg=bg, fg="white",
                     font=("Segoe UI", 11, "bold"), relief="flat",
                     cursor="hand2", padx=30, pady=8, command=command)

def preview_image(path, label):
    if path and os.path.exists(path):
        img = Image.open(path)
        img.thumbnail((110, 110))
        photo = ImageTk.PhotoImage(img)
        label.config(image=photo, text="")
        label.image = photo
    else:
        label.config(text="No image selected", image="", fg="#aaa")

def add_category(card_frame, menu_id_map):
    win = styled_modal("Add Category", "420x220")
    styled_header(win, "Add Category", bg="#2c3e50")

    form = tk.Frame(win, bg="#f5f6fa", padx=30, pady=20)
    form.pack(fill="both", expand=True)

    entry_cat = styled_field(form, "Category Name", 0)

    def save_category():
        cat_name = entry_cat.get().strip()
        if not cat_name:
            entry_cat.config(highlightbackground="#e74c3c")
            messagebox.showerror("Error", "Category name is required.")
            return
        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO categories (name) VALUES (%s)", (cat_name,))
            conn.commit()
            messagebox.showinfo("Success", "Category added.")
            win.destroy()
            refresh_menu_display(card_frame, menu_id_map)
        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", "Category already exists.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    btn_frame = tk.Frame(win, bg="#f5f6fa", padx=30, pady=5)
    btn_frame.pack(fill="x")
    styled_button(btn_frame, "Save Category", save_category, bg="#2c3e50").pack(fill="x")

def build_product_form(parent, categories):
    cat_names = [c[1] for c in categories]
    cat_id_map = {c[1]: c[0] for c in categories}

    form = tk.Frame(parent, bg="#f5f6fa", padx=30, pady=15)
    form.pack(fill="both", expand=True)
    form.columnconfigure(1, weight=1)

    entry_name = styled_field(form, "Product Name", 0)
    entry_price = styled_field(form, "Price (₱)", 1)

    tk.Label(form, text="Category", font=("Segoe UI", 10), bg="#f5f6fa", fg="#555").grid(
        row=2, column=0, sticky="w", pady=6, padx=(0, 12))
    cat_var = tk.StringVar(value="Select Category")
    cat_dropdown = ttk.Combobox(form, textvariable=cat_var,
                                values=["Select Category"] + cat_names,
                                state="readonly", font=("Segoe UI", 11), width=28)
    cat_dropdown.grid(row=2, column=1, pady=6, sticky="ew")

    tk.Label(form, text="Image", font=("Segoe UI", 10), bg="#f5f6fa", fg="#555").grid(
        row=3, column=0, sticky="nw", pady=6)

    img_box = tk.Frame(form, bg="#eef0f3", width=115, height=115,
                       highlightthickness=1, highlightbackground="#ccc")
    img_box.grid(row=3, column=1, sticky="w", pady=6)
    img_box.pack_propagate(False)

    preview_lbl = tk.Label(img_box, text="No image selected", bg="#eef0f3",
                           fg="#aaa", font=("Segoe UI", 9), wraplength=100, justify="center")
    preview_lbl.pack(expand=True)

    image_path_var = tk.StringVar()

    def browse():
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")])
        if file_path:
            new_path = save_uploaded_image(file_path)
            if new_path:
                image_path_var.set(new_path)
                preview_image(new_path, preview_lbl)

    def clear_img():
        image_path_var.set("")
        preview_lbl.config(text="No image selected", image="", fg="#aaa")

    img_btn_frame = tk.Frame(form, bg="#f5f6fa")
    img_btn_frame.grid(row=4, column=1, sticky="w", pady=(0, 6))

    tk.Button(img_btn_frame, text="Browse", font=("Segoe UI", 9), bg="#3498db", fg="white",
              relief="flat", cursor="hand2", padx=10, pady=4, command=browse).pack(side="left", padx=(0, 6))
    tk.Button(img_btn_frame, text="Clear", font=("Segoe UI", 9), bg="#95a5a6", fg="white",
              relief="flat", cursor="hand2", padx=10, pady=4, command=clear_img).pack(side="left")

    return form, entry_name, entry_price, cat_var, cat_id_map, image_path_var, preview_lbl

def add_product(card_frame, menu_id_map):
    win = styled_modal("Add Product", "520x560")
    styled_header(win, "Add New Product", bg="#2c3e50")

    categories = get_categories()
    form, entry_name, entry_price, cat_var, cat_id_map, image_path_var, preview_lbl = build_product_form(win, categories)

    def save_product():
        name = entry_name.get().strip()
        price_str = entry_price.get().strip()
        category_name = cat_var.get()
        image_path = image_path_var.get()

        entry_name.config(highlightbackground="#ccc")
        entry_price.config(highlightbackground="#ccc")

        if not name:
            entry_name.config(highlightbackground="#e74c3c")
            messagebox.showerror("Validation Error", "Product name is required.")
            return
        if not price_str:
            entry_price.config(highlightbackground="#e74c3c")
            messagebox.showerror("Validation Error", "Price is required.")
            return
        try:
            price = float(price_str)
            if price < 0:
                raise ValueError
        except ValueError:
            entry_price.config(highlightbackground="#e74c3c")
            messagebox.showerror("Validation Error", "Price must be a valid positive number.")
            return
        if category_name == "Select Category" or category_name not in cat_id_map:
            messagebox.showerror("Validation Error", "Please select a valid category.")
            return

        category_id = cat_id_map[category_name]
        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO menu (name, price, category_id, image_path)
                VALUES (%s, %s, %s, %s)
            """, (name, price, category_id, image_path))
            conn.commit()
            messagebox.showinfo("Success", "Product added.")
            win.destroy()
            refresh_menu_display(card_frame, menu_id_map)
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    btn_frame = tk.Frame(win, bg="#f5f6fa", padx=30, pady=8)
    btn_frame.pack(fill="x")
    styled_button(btn_frame, "Save Product", save_product, bg="#2c3e50").pack(fill="x")

def edit_product(product_id, card_frame, menu_id_map):
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, category_id, image_path FROM menu WHERE id=%s", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if not product:
        messagebox.showerror("Error", "Product not found.")
        return

    win = styled_modal("Edit Product", "520x560")
    styled_header(win, "Edit Product", bg="#d35400")

    categories = get_categories()
    form, entry_name, entry_price, cat_var, cat_id_map, image_path_var, preview_lbl = build_product_form(win, categories)

    entry_name.insert(0, product[0])
    entry_price.insert(0, str(product[1]))

    current_cat = next((name for name, cid in cat_id_map.items() if cid == product[2]), "")
    cat_var.set(current_cat if current_cat else "Select Category")

    if product[3]:
        image_path_var.set(product[3])
        preview_image(product[3], preview_lbl)

    def update_product():
        name = entry_name.get().strip()
        price_str = entry_price.get().strip()
        category_name = cat_var.get()
        image_path = image_path_var.get()

        entry_name.config(highlightbackground="#ccc")
        entry_price.config(highlightbackground="#ccc")

        if not name:
            entry_name.config(highlightbackground="#e74c3c")
            messagebox.showerror("Validation Error", "Product name is required.")
            return
        if not price_str:
            entry_price.config(highlightbackground="#e74c3c")
            messagebox.showerror("Validation Error", "Price is required.")
            return
        try:
            price = float(price_str)
            if price < 0:
                raise ValueError
        except ValueError:
            entry_price.config(highlightbackground="#e74c3c")
            messagebox.showerror("Validation Error", "Price must be a valid positive number.")
            return
        if not category_name or category_name not in cat_id_map:
            messagebox.showerror("Validation Error", "Please select a valid category.")
            return

        category_id = cat_id_map[category_name]
        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE menu SET name=%s, price=%s, category_id=%s, image_path=%s
                WHERE id=%s
            """, (name, price, category_id, image_path, product_id))
            conn.commit()
            messagebox.showinfo("Success", "Product updated.")
            win.destroy()
            refresh_menu_display(card_frame, menu_id_map)
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    btn_frame = tk.Frame(win, bg="#f5f6fa", padx=30, pady=8)
    btn_frame.pack(fill="x")
    styled_button(btn_frame, "Update Product", update_product, bg="#d35400").pack(fill="x")

def delete_product(product_id, card_frame, menu_id_map):
    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?"):
        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT image_path FROM menu WHERE id=%s", (product_id,))
            result = cursor.fetchone()
            if result and result[0] and os.path.exists(result[0]):
                os.remove(result[0])
            cursor.execute("DELETE FROM menu WHERE id=%s", (product_id,))
            conn.commit()
            messagebox.showinfo("Success", "Product deleted.")
            refresh_menu_display(card_frame, menu_id_map)
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

def refresh_menu_display(card_frame, menu_id_map):
    for widget in card_frame.winfo_children():
        widget.destroy()

    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.name, m.price, c.name, m.image_path
        FROM menu m
        LEFT JOIN categories c ON m.category_id = c.id
        ORDER BY m.id
    """)
    items = cursor.fetchall()
    conn.close()

    menu_id_map.clear()

    cols = 4
    for idx, item in enumerate(items):
        menu_id, name, price, category, img_path = item
        category = category if category else "Uncategorized"
        menu_id_map[menu_id] = True

        row = idx // cols
        col = idx % cols

        card = tk.Frame(card_frame, bg="white", bd=0,
                        highlightthickness=1, highlightbackground="#e0e0e0")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card_frame.columnconfigure(col, weight=1)

        img_box = tk.Frame(card, bg="#f0f2f5", width=140, height=130)
        img_box.pack(fill="x")
        img_box.pack_propagate(False)

        if img_path and os.path.exists(img_path):
            img = Image.open(img_path)
            img.thumbnail((140, 130))
            photo = ImageTk.PhotoImage(img)
            img_lbl = tk.Label(img_box, image=photo, bg="#f0f2f5")
            img_lbl.image = photo
            img_lbl.pack(expand=True)
        else:
            tk.Label(img_box, text="No Image", bg="#f0f2f5",
                     fg="#bbb", font=("Segoe UI", 9)).pack(expand=True)

        info = tk.Frame(card, bg="white", padx=10, pady=8)
        info.pack(fill="x")

        tk.Label(info, text=name, font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#2c3e50", anchor="w", wraplength=140).pack(fill="x")
        tk.Label(info, text=f"₱{price:.2f}", font=("Segoe UI", 11),
                 bg="white", fg="#d35400", anchor="w").pack(fill="x")
        tk.Label(info, text=category, font=("Segoe UI", 9),
                 bg="white", fg="#95a5a6", anchor="w").pack(fill="x")

        btn_row = tk.Frame(card, bg="white", padx=10)
        btn_row.pack(fill="x", pady=(0, 10))

        tk.Button(btn_row, text="Edit", bg="#3498db", fg="white",
                  font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                  padx=12, pady=4,
                  command=lambda pid=menu_id: edit_product(pid, card_frame, menu_id_map)).pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="Delete", bg="#e74c3c", fg="white",
                  font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                  padx=12, pady=4,
                  command=lambda pid=menu_id: delete_product(pid, card_frame, menu_id_map)).pack(side="left")

def main():
    win = tk.Tk()
    win.title("Admin - Menu Management")
    win.geometry("1280x720")
    win.configure(bg="#f5f6fa")

    add_sidebar(win)

    content_frame = tk.Frame(win, bg="#f5f6fa")
    content_frame.pack(side="right", fill="both", expand=True)

    top_bar = tk.Frame(content_frame, bg="#f5f6fa")
    top_bar.pack(fill="x", padx=25, pady=(20, 0))

    tk.Label(top_bar, text="Menu Management", font=("Segoe UI", 22, "bold"),
             fg="#d35400", bg="#f5f6fa").pack(side="left")

    btn_group = tk.Frame(top_bar, bg="#f5f6fa")
    btn_group.pack(side="right")

    tk.Button(btn_group, text="+ Add Product", bg="#d35400", fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
              padx=16, pady=7,
              command=lambda: add_product(card_container, menu_id_map)).pack(side="left", padx=(0, 8))
    tk.Button(btn_group, text="+ Add Category", bg="#2c3e50", fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
              padx=16, pady=7,
              command=lambda: add_category(card_container, menu_id_map)).pack(side="left")

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
    refresh_menu_display(card_container, menu_id_map)

    win.mainloop()

if __name__ == "__main__":
    main()