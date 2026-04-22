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

def get_today_orders_count():
    conn = connect_db()
    if not conn:
        return 0
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = CURDATE()")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_pending_queue_count():
    conn = connect_db()
    if not conn:
        return 0
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_today_completed_count():
    conn = connect_db()
    if not conn:
        return 0
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed' AND DATE(created_at) = CURDATE()")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_today_sales():
    conn = connect_db()
    if not conn:
        return 0.0
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE DATE(created_at) = CURDATE() AND status = 'completed'")
    total = cursor.fetchone()[0]
    conn.close()
    return float(total)

def main():
    win = tk.Tk()
    win.title("Cashier Dashboard - Snack in Save 9Nueve")
    win.geometry("1280x720")
    win.configure(bg="#f0f0f0")

    add_staff_sidebar(win)

    content_frame = tk.Frame(win, bg="#f0f0f0")
    content_frame.pack(side="right", fill="both", expand=True)

    style = ttk.Style()
    style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"), foreground="#d35400", background="#f0f0f0")

    ttk.Label(content_frame, text="CASHIER DASHBOARD", style="Title.TLabel").pack(pady=50)

    summary_frame = tk.Frame(content_frame, bg="#f0f0f0")
    summary_frame.pack(pady=40)

    today_orders = get_today_orders_count()
    pending = get_pending_queue_count()
    completed_today = get_today_completed_count()
    sales_today = get_today_sales()

    cards_data = [
        ("Today's Orders", str(today_orders)),
        ("Pending Queue", str(pending)),
        ("Completed Today", str(completed_today)),
        ("Sales Today", f"₱{sales_today:,.2f}")
    ]

    for title, value in cards_data:
        card = tk.Frame(summary_frame, bg="white", relief="ridge", bd=1, padx=30, pady=20)
        card.pack(side="left", padx=20)
        tk.Label(card, text=title, font=("Segoe UI", 11), bg="white").pack()
        tk.Label(card, text=value, font=("Segoe UI", 22, "bold"), fg="#d35400", bg="white").pack()

    win.mainloop()

if __name__ == "__main__":
    main()