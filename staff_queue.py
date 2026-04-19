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

def fetch_queue():
    conn = connect_db()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, order_code, customer_name, total_amount, created_at
        FROM orders
        WHERE status = 'waiting'
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
    if not messagebox.askyesno("Serving Order", "Mark this order as serving?"):
        return
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET status = 'serving' WHERE id = %s", (order_id,))
        conn.commit()
        messagebox.showinfo("Serving", "Order marked as serving.")
        refresh_callback()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        conn.close()


def build_queue_cards(parent, orders, refresh_callback):
    for i, order in enumerate(orders):
        is_first = (i == 0)

        outer = tk.Frame(parent, bg="#e0e8f0" if is_first else "#e0e0e0")
        outer.pack(fill="x", padx=20, pady=(0, 10))

        card = tk.Frame(outer, bg="white", padx=16, pady=12)
        card.pack(fill="x", padx=2 if is_first else 1, pady=2 if is_first else 1)

        top_row = tk.Frame(card, bg="white")
        top_row.pack(fill="x", pady=(0, 8))

        pos_label = tk.Label(top_row, text=str(i + 1),
                             font=("Segoe UI", 18, "bold"),
                             bg="white", fg="#2980b9" if is_first else "#aaa",
                             width=3, anchor="w")
        pos_label.pack(side="left")

        if is_first:
            badge = tk.Label(top_row, text="  Preparing  ",
                             font=("Segoe UI", 9, "bold"),
                             bg="#dbeeff", fg="#1a5fa8",
                             padx=4, pady=3)
        else:
            badge = tk.Label(top_row, text="  Waiting  ",
                             font=("Segoe UI", 9, "bold"),
                             bg="#fff0e0", fg="#b35c00",
                             padx=4, pady=3)
        badge.pack(side="left", padx=(0, 12))

        tk.Label(top_row, text=order['order_code'],
                 font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#2c3e50").pack(side="left")

        tk.Label(top_row, text=f"₱{float(order['total_amount']):.2f}",
                 font=("Segoe UI", 12, "bold"),
                 bg="white", fg="#2980b9").pack(side="right")

        tk.Label(top_row, text=order['customer_name'],
                 font=("Segoe UI", 10),
                 bg="white", fg="#888").pack(side="right", padx=(0, 16))

        items = fetch_order_items(order['id'])
        items_str = "   •   ".join([f"{it['name']} ×{it['quantity']}" for it in items])

        items_frame = tk.Frame(card, bg="#f4f6f8", padx=10, pady=6)
        items_frame.pack(fill="x", pady=(0, 10))
        tk.Label(items_frame, text=items_str,
                 font=("Segoe UI", 9),
                 bg="#f4f6f8", fg="#666",
                 anchor="w", wraplength=900).pack(fill="x")

        bottom_row = tk.Frame(card, bg="white")
        bottom_row.pack(fill="x")

        time_str = order['created_at'].strftime("%I:%M %p") if order['created_at'] else ""
        tk.Label(bottom_row, text=time_str,
                 font=("Segoe UI", 9),
                 bg="white", fg="#bbb").pack(side="left")

        btn_frame = tk.Frame(bottom_row, bg="white")
        btn_frame.pack(side="right")

        tk.Button(btn_frame, text="✔ Complete",
                  bg="#eaf5ee", fg="#1a7a3c",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", cursor="hand2",
                  padx=12, pady=5,
                  command=lambda oid=order['id']: mark_completed(oid, refresh_callback)
                  ).pack(side="left", padx=(0, 8))

        tk.Button(btn_frame, text="🍽 Serving",
                  bg="#fff0e0", fg="#b35c00",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", cursor="hand2",
                  padx=12, pady=5,
                  command=lambda oid=order['id']: mark_serving(oid, refresh_callback)
                  ).pack(side="left")


def main():
    win = tk.Tk()
    win.title("Staff - Queue")
    win.geometry("1280x720")
    win.configure(bg="#f5f6fa")

    add_staff_sidebar(win)

    content_frame = tk.Frame(win, bg="#f5f6fa")
    content_frame.pack(side="right", fill="both", expand=True)

    top_bar = tk.Frame(content_frame, bg="#f5f6fa")
    top_bar.pack(fill="x", padx=25, pady=(20, 0))

    tk.Label(top_bar, text="Queue Management", font=("Segoe UI", 22, "bold"),
             fg="#d35400", bg="#f5f6fa").pack(side="left")

    queue_count_lbl = tk.Label(top_bar, text="", font=("Segoe UI", 11),
                               fg="#2980b9", bg="#f5f6fa")
    queue_count_lbl.pack(side="left", padx=16)

    tk.Button(top_bar, text="⟳ Refresh", bg="#2c3e50", fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
              padx=14, pady=6,
              command=lambda: refresh()).pack(side="right")

    tk.Frame(content_frame, bg="#ddd", height=1).pack(fill="x", padx=25, pady=12)

    canvas = tk.Canvas(content_frame, bg="#f5f6fa", highlightthickness=0)
    scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg="#f5f6fa")

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def refresh():
        for w in scroll_frame.winfo_children():
            w.destroy()

        orders = fetch_queue()
        count = len(orders)
        queue_count_lbl.config(
            text=f"{count} order{'s' if count != 1 else ''} in queue" if count > 0 else "No orders in queue"
        )

        if not orders:
            empty = tk.Frame(scroll_frame, bg="#f5f6fa")
            empty.pack(expand=True, pady=80)
            tk.Label(empty, text="🎉", font=("Segoe UI", 36), bg="#f5f6fa").pack()
            tk.Label(empty, text="Queue is empty", font=("Segoe UI", 14),
                     bg="#f5f6fa", fg="#bbb").pack(pady=8)
            return

        build_queue_cards(scroll_frame, orders, refresh)

    refresh()

    def auto_refresh():
        refresh()
        win.after(15000, auto_refresh)

    win.after(15000, auto_refresh)
    win.mainloop()

if __name__ == "__main__":
    main()