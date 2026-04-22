import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
import mysql.connector
from sidebar import add_sidebar

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'app'
}

BG          = "#ffffff"
CARD_BG     = "#ffffff"
ACCENT      = "#d35400"
ACCENT2     = "#e67e22"
TEXT_LIGHT  = "#2c3e50"
TEXT_DIM    = "#7f8c8d"
GREEN       = "#27ae60"
BLUE        = "#2980b9"
RED         = "#c0392b"
YELLOW      = "#f39c12"

STATUS_COLORS = {
    "pending":   ACCENT,
    "waiting":   YELLOW,
    "serving":   BLUE,
    "completed": GREEN,
    "cancelled": RED,
}


def get_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error:
        return None


def fetch_stats():
    conn = get_db()
    if not conn:
        return None
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS cnt FROM orders")
    total_orders = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='pending'")
    pending = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='waiting'")
    waiting = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='serving'")
    serving = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='completed'")
    completed = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM orders WHERE status='cancelled'")
    cancelled = cur.fetchone()['cnt']

    cur.execute("""
        SELECT COALESCE(SUM(total_amount), 0) AS sales
        FROM orders
        WHERE DATE(created_at) = CURDATE()
          AND status NOT IN ('cancelled')
    """)
    today_sales = float(cur.fetchone()['sales'])

    cur.execute("""
        SELECT COALESCE(SUM(total_amount), 0) AS sales
        FROM orders
        WHERE status NOT IN ('cancelled')
    """)
    total_sales = float(cur.fetchone()['sales'])

    cur.execute("""
        SELECT m.name, SUM(oi.quantity) AS qty
        FROM order_items oi
        JOIN menu m ON oi.menu_id = m.id
        GROUP BY m.id ORDER BY qty DESC LIMIT 5
    """)
    top_items = cur.fetchall()

    cur.execute("""
        SELECT o.order_code, o.total_amount, o.status, o.created_at
        FROM orders o
        ORDER BY o.created_at DESC LIMIT 6
    """)
    recent_orders = cur.fetchall()

    cur.execute("SELECT COUNT(*) AS cnt FROM menu WHERE stock > 0")
    items_available = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM menu WHERE stock = 0")
    out_of_stock = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM staff")
    staff_count = cur.fetchone()['cnt']

    cur.close()
    conn.close()

    return {
        "total_orders": total_orders,
        "pending": pending,
        "waiting": waiting,
        "serving": serving,
        "completed": completed,
        "cancelled": cancelled,
        "today_sales": today_sales,
        "total_sales": total_sales,
        "top_items": top_items,
        "recent_orders": recent_orders,
        "items_available": items_available,
        "out_of_stock": out_of_stock,
        "staff_count": staff_count,
    }


class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Snack in Save 9Nueve — Admin Dashboard")
        self.root.geometry("1280x720")
        self.root.configure(bg=BG)

        add_sidebar(self.root)

        self.content = tk.Frame(self.root, bg=BG)
        self.content.pack(side="right", fill="both", expand=True)

        self._build_header()
        self._build_body()
        self.refresh()

    def _build_header(self):
        hdr = tk.Frame(self.content, bg=ACCENT, pady=0)
        hdr.pack(fill="x")

        inner = tk.Frame(hdr, bg=ACCENT)
        inner.pack(fill="x", padx=20, pady=10)

        tk.Label(inner, text="SNACK IN SAVE  9NUEVE",
                 font=("Segoe UI", 15, "bold"), bg=ACCENT, fg="white").pack(side="left")

        right = tk.Frame(inner, bg=ACCENT)
        right.pack(side="right")

        self.clock_lbl = tk.Label(right, text="", font=("Segoe UI", 10),
                                  bg=ACCENT, fg="white")
        self.clock_lbl.pack(side="right", padx=6)

        self._tick()

    def _tick(self):
        now = datetime.now().strftime("%A, %B %d %Y   %I:%M:%S %p")
        self.clock_lbl.config(text=now)
        self.root.after(1000, self._tick)

    def _build_body(self):
        self.body = tk.Frame(self.content, bg=BG)
        self.body.pack(fill="both", expand=True, padx=18, pady=14)

        self.cards_row  = tk.Frame(self.body, bg=BG)
        self.cards_row.pack(fill="x")

        self.mid_row = tk.Frame(self.body, bg=BG)
        self.mid_row.pack(fill="both", expand=True, pady=(14, 0))

    def refresh(self):
        stats = fetch_stats()
        if not stats:
            return

        for w in self.cards_row.winfo_children():
            w.destroy()
        for w in self.mid_row.winfo_children():
            w.destroy()

        self._build_stat_cards(stats)
        self._build_status_row(stats)
        self._build_mid(stats)

    def _stat_card(self, parent, title, value, color=ACCENT, sub=None):
        card = tk.Frame(parent, bg=CARD_BG, padx=16, pady=12,
                        highlightthickness=1, highlightbackground="#e0e0e0")
        card.pack(side="left", fill="both", expand=True, padx=5)

        bar = tk.Frame(card, bg=color, width=4)
        bar.pack(side="left", fill="y", padx=(0, 12))

        info = tk.Frame(card, bg=CARD_BG)
        info.pack(side="left", fill="both", expand=True)

        tk.Label(info, text=title.upper(), font=("Segoe UI", 8, "bold"),
                 bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w")
        tk.Label(info, text=str(value), font=("Segoe UI", 22, "bold"),
                 bg=CARD_BG, fg=color).pack(anchor="w")
        if sub:
            tk.Label(info, text=sub, font=("Segoe UI", 8),
                     bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w")

    def _build_stat_cards(self, s):
        self._stat_card(self.cards_row, "Today's Sales",
                        f"₱{s['today_sales']:,.2f}", ACCENT)
        self._stat_card(self.cards_row, "Total Sales",
                        f"₱{s['total_sales']:,.2f}", ACCENT2)
        self._stat_card(self.cards_row, "Total Orders",
                        s['total_orders'], BLUE)
        self._stat_card(self.cards_row, "Menu Items",
                        s['items_available'], GREEN,
                        f"{s['out_of_stock']} out of stock")
        self._stat_card(self.cards_row, "Staff",
                        s['staff_count'], TEXT_DIM)

    def _build_status_row(self, s):
        row = tk.Frame(self.body, bg=BG)
        row.pack(fill="x", pady=(10, 0))

        labels = [
            ("Pending",   s['pending'],   STATUS_COLORS['pending']),
            ("Waiting",   s['waiting'],   STATUS_COLORS['waiting']),
            ("Serving",   s['serving'],   STATUS_COLORS['serving']),
            ("Completed", s['completed'], STATUS_COLORS['completed']),
            ("Cancelled", s['cancelled'], STATUS_COLORS['cancelled']),
        ]
        for title, val, color in labels:
            pill = tk.Frame(row, bg=color, padx=14, pady=6)
            pill.pack(side="left", padx=4)
            tk.Label(pill, text=f"{title}  {val}",
                     font=("Segoe UI", 10, "bold"),
                     bg=color, fg="white").pack()

    def _build_mid(self, s):
        left = tk.Frame(self.mid_row, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        right = tk.Frame(self.mid_row, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_recent_orders(left, s['recent_orders'])
        self._build_top_items(right, s['top_items'])

    def _section_title(self, parent, text):
        tk.Label(parent, text=text, font=("Segoe UI", 11, "bold"),
                 bg=BG, fg=TEXT_LIGHT).pack(anchor="w", pady=(0, 6))

    def _build_recent_orders(self, parent, orders):
        self._section_title(parent, "RECENT ORDERS")

        headers = ["Order Code", "Amount", "Status", "Time"]
        widths   = [110, 110, 100, 160]

        hrow = tk.Frame(parent, bg="#f8f9fa", highlightthickness=1,
                        highlightbackground="#dee2e6")
        hrow.pack(fill="x")
        for h, w in zip(headers, widths):
            tk.Label(hrow, text=h, font=("Segoe UI", 9, "bold"),
                     bg="#f8f9fa", fg=TEXT_DIM, width=w//8,
                     anchor="w", padx=8, pady=5).pack(side="left")

        for i, o in enumerate(orders):
            bg_row = "#ffffff" if i % 2 == 0 else "#f8f9fa"
            row = tk.Frame(parent, bg=bg_row)
            row.pack(fill="x")

            status = o['status']
            scolor = STATUS_COLORS.get(status, TEXT_DIM)
            time_str = o['created_at'].strftime("%b %d  %I:%M %p") if o['created_at'] else ""

            cells = [
                (o['order_code'], TEXT_LIGHT),
                (f"₱{float(o['total_amount']):,.2f}", ACCENT),
                (status.capitalize(), scolor),
                (time_str, TEXT_DIM),
            ]
            for (val, color), w in zip(cells, widths):
                tk.Label(row, text=val, font=("Segoe UI", 10),
                         bg=bg_row, fg=color, width=w//8,
                         anchor="w", padx=8, pady=5).pack(side="left")

    def _build_top_items(self, parent, items):
        self._section_title(parent, "TOP SELLING ITEMS")

        if not items:
            tk.Label(parent, text="No data yet.", font=("Segoe UI", 10),
                     bg=BG, fg=TEXT_DIM).pack(anchor="w")
            return

        max_qty = max(item['qty'] for item in items) or 1

        for item in items:
            row = tk.Frame(parent, bg=BG)
            row.pack(fill="x", pady=3)

            tk.Label(row, text=item['name'], font=("Segoe UI", 10),
                     bg=BG, fg=TEXT_LIGHT, width=22, anchor="w").pack(side="left")

            bar_container = tk.Frame(row, bg="#e9ecef", height=18, width=160,
                                     highlightthickness=1, highlightbackground="#ced4da")
            bar_container.pack(side="left", padx=8)
            bar_container.pack_propagate(False)

            fill_w = int((item['qty'] / max_qty) * 156)
            fill = tk.Frame(bar_container, bg=ACCENT, height=18, width=max(fill_w, 4))
            fill.place(x=2, y=1)

            tk.Label(row, text=f"×{item['qty']}", font=("Segoe UI", 10, "bold"),
                     bg=BG, fg=ACCENT).pack(side="left")


def main():
    root = tk.Tk()
    app = Dashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()