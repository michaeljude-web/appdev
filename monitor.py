import tkinter as tk
from tkinter import ttk
import mysql.connector
from datetime import datetime

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
        print(f"Database error: {err}")
        return None

def fetch_preparing():
    """Orders with status 'waiting' (preparing)."""
    conn = connect_db()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_code FROM orders
        WHERE status = 'waiting'
        ORDER BY created_at ASC
    """)
    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows

def fetch_now_serving():
    """Orders with status 'serving'."""
    conn = connect_db()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_code FROM orders
        WHERE status = 'serving'
        ORDER BY created_at ASC
    """)
    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows

class ClaimMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Claim Monitor")
        self.root.configure(bg="#f0f2f5")
        self.root.attributes("-fullscreen", False)
        self.root.geometry("1200x600")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        left_frame = tk.Frame(root, bg="#ffffff", relief="ridge", bd=2)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        tk.Label(left_frame, text="PREPARING", font=("Segoe UI", 28, "bold"),
                 fg="#000", bg="#ffffff").pack(pady=(20, 10))

        self.left_canvas = tk.Canvas(left_frame, bg="#ffffff", highlightthickness=0)
        left_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.left_canvas.yview)
        self.left_inner = tk.Frame(self.left_canvas, bg="#ffffff")
        self.left_inner.bind("<Configure>", lambda e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all")))
        self.left_canvas.create_window((0, 0), window=self.left_inner, anchor="nw")
        self.left_canvas.configure(yscrollcommand=left_scrollbar.set)

        self.left_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        left_scrollbar.pack(side="right", fill="y")

        right_frame = tk.Frame(root, bg="#ffffff", relief="ridge", bd=2)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        tk.Label(right_frame, text="NOW SERVING", font=("Segoe UI", 28, "bold"),
                 fg="#000", bg="#ffffff").pack(pady=(20, 10))

        self.right_canvas = tk.Canvas(right_frame, bg="#ffffff", highlightthickness=0)
        right_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.right_canvas.yview)
        self.right_inner = tk.Frame(self.right_canvas, bg="#ffffff")
        self.right_inner.bind("<Configure>", lambda e: self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all")))
        self.right_canvas.create_window((0, 0), window=self.right_inner, anchor="nw")
        self.right_canvas.configure(yscrollcommand=right_scrollbar.set)

        self.right_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        right_scrollbar.pack(side="right", fill="y")

        self.update_display()

        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        self.root.bind("<F11>", lambda e: self.root.attributes("-fullscreen", True))

    def update_display(self):
        """Fetch latest orders and refresh both columns."""
        preparing_list = fetch_preparing()
        serving_list = fetch_now_serving()

        for widget in self.left_inner.winfo_children():
            widget.destroy()

        if not preparing_list:
            tk.Label(self.left_inner, text="", font=("Segoe UI", 16),
                     bg="#ffffff", fg="#aaa", justify="center").pack(expand=True, pady=40)
        else:
            for code in preparing_list:
                self._add_order_card(self.left_inner, code, "#fef9ec", "#d35400")

        for widget in self.right_inner.winfo_children():
            widget.destroy()

        if not serving_list:
            tk.Label(self.right_inner, text="", font=("Segoe UI", 16),
                     bg="#ffffff", fg="#aaa", justify="center").pack(expand=True, pady=40)
        else:
            for code in serving_list:
                self._add_order_card(self.right_inner, code, "#eafaf1", "#27ae60")

        self.root.after(3000, self.update_display)

    def _add_order_card(self, parent, order_code, bg_color, fg_color):
        """Create a card-like widget for a single order code."""
        card = tk.Frame(parent, bg=bg_color, relief="flat", bd=1, highlightthickness=1,
                        highlightbackground="#e0e0e0")
        card.pack(fill="x", padx=10, pady=5)

        lbl = tk.Label(card, text=order_code, font=("Courier New", 24, "bold"),
                       bg=bg_color, fg=fg_color, pady=12)
        lbl.pack()


def main():
    root = tk.Tk()
    app = ClaimMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main()