import tkinter as tk
from tkinter import ttk, messagebox
from staff_sidebar import add_staff_sidebar
import mysql.connector

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

def fetch_waiting():
    conn = connect_db()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, order_code, total_amount, created_at
        FROM orders
        WHERE status = 'waiting'
        ORDER BY created_at ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def fetch_serving():
    conn = connect_db()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, order_code, total_amount, created_at
        FROM orders
        WHERE status = 'serving'
        ORDER BY created_at ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def fetch_order_items(order_id):
    conn = connect_db()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.name, oi.quantity, oi.price
        FROM order_items oi
        JOIN menu m ON oi.menu_id = m.id
        WHERE oi.order_id = %s
    """, (order_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def mark_completed(order_id, refresh_callback):
    if not messagebox.askyesno("Complete Order", "Mark this order as completed?"):
        return
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET status = 'completed' WHERE id = %s", (order_id,))
        conn.commit()
        messagebox.showinfo("Done", "Order marked as completed.")
        refresh_callback()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        conn.close()

def mark_serving(order_id, refresh_callback):
    if not messagebox.askyesno("Serving Order", "Move this order to Serving section?"):
        return
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET status = 'serving' WHERE id = %s", (order_id,))
        conn.commit()
        messagebox.showinfo("Serving", "Order moved to Serving section.")
        refresh_callback()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        conn.close()

def build_column(parent, title, orders, is_waiting_column, refresh_callback):
    """Build one column (waiting or serving) with its cards."""
    col_frame = tk.Frame(parent, bg="#f5f6fa")
    col_frame.pack(side="left", fill="both", expand=True, padx=10)

    tk.Label(col_frame, text=title, font=("Segoe UI", 14, "bold"),
             fg="#d35400" if not is_waiting_column else "#2c3e50",
             bg="#f5f6fa").pack(anchor="w", pady=(0, 12))

    canvas = tk.Canvas(col_frame, bg="#f5f6fa", highlightthickness=0)
    scrollbar = ttk.Scrollbar(col_frame, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg="#f5f6fa")

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    if not orders:
        empty = tk.Frame(scroll_frame, bg="#f5f6fa")
        empty.pack(expand=True, pady=40)
        tk.Label(empty, text="No orders", font=("Segoe UI", 12),
                 bg="#f5f6fa", fg="#bbb").pack()
        return

    for idx, order in enumerate(orders):
        is_first = (idx == 0 and is_waiting_column)
        _build_card(scroll_frame, order, idx, is_first, is_waiting_column, refresh_callback)

def _build_card(parent, order, position, is_first, is_waiting, refresh_callback):
    outer = tk.Frame(parent, bg="#e0e8f0" if is_first else "#e0e0e0")
    outer.pack(fill="x", padx=5, pady=(0, 10))

    card = tk.Frame(outer, bg="white", padx=12, pady=10)
    card.pack(fill="x", padx=2 if is_first else 1, pady=2 if is_first else 1)

    top_row = tk.Frame(card, bg="white")
    top_row.pack(fill="x", pady=(0, 6))

    pos_label = tk.Label(top_row, text=str(position + 1),
                         font=("Segoe UI", 16, "bold"),
                         bg="white", fg="#2980b9" if is_first else "#aaa",
                         width=3, anchor="w")
    pos_label.pack(side="left")

    if is_waiting:
        if is_first:
            badge = tk.Label(top_row, text="  Preparing  ", bg="#dbeeff", fg="#1a5fa8",
                             font=("Segoe UI", 9, "bold"), padx=4, pady=3)
        else:
            badge = tk.Label(top_row, text="  Waiting  ", bg="#fff0e0", fg="#b35c00",
                             font=("Segoe UI", 9, "bold"), padx=4, pady=3)
    else:
        badge = tk.Label(top_row, text="  Serving  ", bg="#ffe6cc", fg="#cc7a00",
                         font=("Segoe UI", 9, "bold"), padx=4, pady=3)
    badge.pack(side="left", padx=(0, 10))

    tk.Label(top_row, text=order['order_code'], font=("Segoe UI", 10, "bold"),
             bg="white", fg="#2c3e50").pack(side="left")

    tk.Label(top_row, text=f"₱{float(order['total_amount']):.2f}",
             font=("Segoe UI", 11, "bold"), bg="white", fg="#2980b9").pack(side="right")

    items = fetch_order_items(order['id'])
    items_str = "   •   ".join([f"{it['name']} ×{it['quantity']}" for it in items])
    items_frame = tk.Frame(card, bg="#f4f6f8", padx=8, pady=5)
    items_frame.pack(fill="x", pady=(0, 8))
    tk.Label(items_frame, text=items_str, font=("Segoe UI", 9),
             bg="#f4f6f8", fg="#666", anchor="w", wraplength=250).pack(fill="x")

    bottom_row = tk.Frame(card, bg="white")
    bottom_row.pack(fill="x")

    time_str = order['created_at'].strftime("%I:%M %p") if order['created_at'] else ""
    tk.Label(bottom_row, text=time_str, font=("Segoe UI", 9),
             bg="white", fg="#bbb").pack(side="left")

    btn_frame = tk.Frame(bottom_row, bg="white")
    btn_frame.pack(side="right")

    tk.Button(btn_frame, text="✔ Complete", bg="#eaf5ee", fg="#1a7a3c",
              font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
              padx=10, pady=4,
              command=lambda oid=order['id']: mark_completed(oid, refresh_callback)
              ).pack(side="left", padx=(0, 6))

    if is_waiting:
        tk.Button(btn_frame, text="🍽 Serving", bg="#fff0e0", fg="#b35c00",
                  font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                  padx=10, pady=4,
                  command=lambda oid=order['id']: mark_serving(oid, refresh_callback)
                  ).pack(side="left")

def main():
    win = tk.Tk()
    win.title("Staff - Queue")
    win.geometry("1400x750")
    win.configure(bg="#f5f6fa")

    add_staff_sidebar(win)

    content_frame = tk.Frame(win, bg="#f5f6fa")
    content_frame.pack(side="right", fill="both", expand=True)

    top_bar = tk.Frame(content_frame, bg="#f5f6fa")
    top_bar.pack(fill="x", padx=20, pady=(15, 5))

    tk.Label(top_bar, text="Queue Management", font=("Segoe UI", 22, "bold"),
             fg="#d35400", bg="#f5f6fa").pack(side="left")

    tk.Button(top_bar, text="⟳ Refresh", bg="#2c3e50", fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
              padx=14, pady=6,
              command=lambda: refresh_all()).pack(side="right")

    tk.Frame(content_frame, bg="#ddd", height=1).pack(fill="x", padx=20, pady=8)

    columns_frame = tk.Frame(content_frame, bg="#f5f6fa")
    columns_frame.pack(fill="both", expand=True, padx=10, pady=5)

    waiting_frame = None
    serving_frame = None

    def refresh_all():
        nonlocal waiting_frame, serving_frame
        for widget in columns_frame.winfo_children():
            widget.destroy()

        waiting_orders = fetch_waiting()
        serving_orders = fetch_serving()

        waiting_col = tk.Frame(columns_frame, bg="#f5f6fa")
        waiting_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        build_column(waiting_col, " WAITING QUEUE", waiting_orders, True, refresh_all)

        serving_col = tk.Frame(columns_frame, bg="#f5f6fa")
        serving_col.pack(side="right", fill="both", expand=True, padx=(10, 0))
        build_column(serving_col, "SERVING NOW", serving_orders, False, refresh_all)

    refresh_all()

    def auto_refresh():
        refresh_all()
        win.after(15000, auto_refresh)
    win.after(15000, auto_refresh)

    win.mainloop()

if __name__ == "__main__":
    main()