import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import mysql.connector
from sidebar import add_sidebar
import tempfile
import webbrowser
import os

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'app'
}

PRINT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; margin: 30px; color: #2c3e50; }}
  h2 {{ color: #d35400; border-bottom: 2px solid #d35400; padding-bottom: 6px; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 16px; font-size: 13px; }}
  th {{ background: #d35400; color: white; padding: 8px 12px; text-align: left; }}
  td {{ padding: 7px 12px; border-bottom: 1px solid #eee; }}
  tr:nth-child(even) td {{ background: #fafafa; }}
  .meta {{ font-size: 12px; color: #888; margin-bottom: 8px; }}
  .summary {{ margin-top: 20px; font-size: 14px; }}
  .summary span {{ font-weight: bold; color: #d35400; }}
  @media print {{ button {{ display: none; }} }}
</style>
</head>
<body>
<button onclick="window.print()" style="background:#d35400;color:white;border:none;padding:8px 18px;
  font-size:13px;cursor:pointer;border-radius:4px;margin-bottom:16px;">🖨 Print / Save as PDF</button>
<h2>{title}</h2>
<p class="meta">{meta}</p>
{body}
</body>
</html>"""

class ReportsWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin - Reports Dashboard")
        self.root.geometry("1280x720")
        self.root.configure(bg="#f0f0f0")

        add_sidebar(self.root)

        self.content_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.content_frame.pack(side="right", fill="both", expand=True)

        tk.Label(self.content_frame, text="REPORTS DASHBOARD",
                 font=("Segoe UI", 24, "bold"),
                 bg="#f0f0f0", fg="#d35400").pack(pady=20)

        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_daily = tk.Frame(self.notebook, bg="#f0f0f0")
        self.tab_queue = tk.Frame(self.notebook, bg="#f0f0f0")
        self.tab_summary = tk.Frame(self.notebook, bg="#f0f0f0")

        self.notebook.add(self.tab_daily, text="Daily Orders & Transactions")
        self.notebook.add(self.tab_queue, text="Queue Status & Order History")
        self.notebook.add(self.tab_summary, text="Sales Summary Report")

        self.build_daily_tab()
        self.build_queue_tab()
        self.build_summary_tab()

    def get_db_connection(self):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Cannot connect: {err}")
            return None

    def _open_print_window(self, title, meta, body_html):
        html = PRINT_TEMPLATE.format(title=title, meta=meta, body=body_html)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tmp:
            tmp.write(html)
            tmp_path = tmp.name
        webbrowser.open(f"file://{tmp_path}")

    def _rows_to_html_table(self, headers, rows):
        th = "".join(f"<th>{h}</th>" for h in headers)
        body = ""
        for row in rows:
            body += "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
        return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"

    def build_daily_tab(self):
        filter_frame = tk.Frame(self.tab_daily, bg="#f0f0f0")
        filter_frame.pack(pady=10)

        tk.Label(filter_frame, text="Select Date (YYYY-MM-DD):",
                 font=("Segoe UI", 11), bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5)

        self.daily_date_entry = tk.Entry(filter_frame, font=("Segoe UI", 11), width=15)
        self.daily_date_entry.grid(row=0, column=1, padx=5, pady=5)
        self.daily_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        btn_load = tk.Button(filter_frame, text="Load Orders",
                             font=("Segoe UI", 10, "bold"),
                             bg="#d35400", fg="white",
                             command=self.load_daily_orders)
        btn_load.grid(row=0, column=2, padx=10, pady=5)

        btn_print = tk.Button(filter_frame, text="Print",
                              font=("Segoe UI", 10),
                              bg="#bdc3c7", fg="#2c3e50",
                              command=self.print_daily_orders)
        btn_print.grid(row=0, column=3, padx=10, pady=5)

        tree_frame = tk.Frame(self.tab_daily, bg="#f0f0f0")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("Order Code", "Time", "Total Amount", "Status", "Items")
        self.daily_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)

        self.daily_tree.heading("Order Code", text="Order Code")
        self.daily_tree.heading("Time", text="Time")
        self.daily_tree.heading("Total Amount", text="Total Amount")
        self.daily_tree.heading("Status", text="Status")
        self.daily_tree.heading("Items", text="Items")

        self.daily_tree.column("Order Code", width=90, anchor="center")
        self.daily_tree.column("Time", width=100, anchor="center")
        self.daily_tree.column("Total Amount", width=110, anchor="e")
        self.daily_tree.column("Status", width=90, anchor="center")
        self.daily_tree.column("Items", width=400, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.daily_tree.yview)
        self.daily_tree.configure(yscrollcommand=scrollbar.set)

        self.daily_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        summary_frame = tk.Frame(self.tab_daily, bg="#f0f0f0")
        summary_frame.pack(fill="x", padx=10, pady=10)

        self.daily_total_label = tk.Label(summary_frame, text="Total Sales: ₱0.00",
                                          font=("Segoe UI", 12, "bold"),
                                          bg="#f0f0f0", fg="#27ae60")
        self.daily_total_label.pack(side="left", padx=20)

        self.daily_count_label = tk.Label(summary_frame, text="Orders: 0",
                                          font=("Segoe UI", 12, "bold"),
                                          bg="#f0f0f0", fg="#2980b9")
        self.daily_count_label.pack(side="left", padx=20)

        self.load_daily_orders()

    def load_daily_orders(self):
        selected_date = self.daily_date_entry.get().strip()
        try:
            datetime.strptime(selected_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Use YYYY-MM-DD format")
            return

        conn = self.get_db_connection()
        if not conn:
            return
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                o.order_code,
                TIME(o.created_at) AS order_time,
                o.total_amount,
                o.status,
                GROUP_CONCAT(CONCAT(m.name, ' (', oi.quantity, ' x ₱', oi.price, ')') SEPARATOR ', ') AS items_list
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu m ON oi.menu_id = m.id
            WHERE DATE(o.created_at) = %s
            GROUP BY o.id
            ORDER BY o.created_at DESC
        """
        try:
            cursor.execute(query, (selected_date,))
            results = cursor.fetchall()
        except mysql.connector.Error as err:
            messagebox.showerror("Query Error", str(err))
            cursor.close()
            conn.close()
            return

        for row in self.daily_tree.get_children():
            self.daily_tree.delete(row)

        total_sales = 0.0
        order_count = len(results)

        for row in results:
            order_code = row['order_code']
            order_time = str(row['order_time']) if row['order_time'] else ""
            total_amount = float(row['total_amount'])
            status = row['status'].capitalize()
            items_list = row['items_list'] if row['items_list'] else ""

            self.daily_tree.insert("", "end", values=(
                order_code,
                order_time,
                f"₱{total_amount:,.2f}",
                status,
                items_list
            ))
            total_sales += total_amount

        self.daily_total_label.config(text=f"Total Sales: ₱{total_sales:,.2f}")
        self.daily_count_label.config(text=f"Orders: {order_count}")

        cursor.close()
        conn.close()

    def print_daily_orders(self):
        headers = ["Order Code", "Time", "Total Amount", "Status", "Items"]
        rows = [self.daily_tree.item(r)["values"] for r in self.daily_tree.get_children()]
        if not rows:
            messagebox.showinfo("No Data", "No orders to print.")
            return
        meta = f"Date: {self.daily_date_entry.get()} | {self.daily_count_label.cget('text')} | {self.daily_total_label.cget('text')}"
        table_html = self._rows_to_html_table(headers, rows)
        summary_html = f"<div class='summary'>{self.daily_total_label.cget('text')} &nbsp; {self.daily_count_label.cget('text')}</div>"
        body_html = table_html + summary_html
        self._open_print_window("Daily Orders & Transactions", meta, body_html)

    def build_queue_tab(self):
        control_frame = tk.Frame(self.tab_queue, bg="#f0f0f0")
        control_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(control_frame, text="Filter by Status:",
                 font=("Segoe UI", 11), bg="#f0f0f0").pack(side="left", padx=5)

        self.status_filter = ttk.Combobox(control_frame, values=["All", "pending", "waiting", "serving", "completed", "cancelled"],
                                          state="readonly", width=12)
        self.status_filter.pack(side="left", padx=5)
        self.status_filter.set("pending")

        btn_refresh = tk.Button(control_frame, text="Refresh",
                                font=("Segoe UI", 10, "bold"),
                                bg="#d35400", fg="white",
                                command=self.load_queue_orders)
        btn_refresh.pack(side="left", padx=10)

        btn_all_history = tk.Button(control_frame, text="Show All History",
                                    font=("Segoe UI", 10),
                                    command=lambda: self.status_filter.set("All") or self.load_queue_orders())
        btn_all_history.pack(side="left", padx=5)

        btn_print = tk.Button(control_frame, text="Print",
                              font=("Segoe UI", 10),
                              bg="#bdc3c7", fg="#2c3e50",
                              command=self.print_queue_orders)
        btn_print.pack(side="left", padx=5)

        tree_frame = tk.Frame(self.tab_queue, bg="#f0f0f0")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("Order Code", "Date", "Time", "Total", "Status", "Items")
        self.queue_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

        self.queue_tree.heading("Order Code", text="Order Code")
        self.queue_tree.heading("Date", text="Date")
        self.queue_tree.heading("Time", text="Time")
        self.queue_tree.heading("Total", text="Total")
        self.queue_tree.heading("Status", text="Status")
        self.queue_tree.heading("Items", text="Items")

        self.queue_tree.column("Order Code", width=90, anchor="center")
        self.queue_tree.column("Date", width=100, anchor="center")
        self.queue_tree.column("Time", width=80, anchor="center")
        self.queue_tree.column("Total", width=100, anchor="e")
        self.queue_tree.column("Status", width=90, anchor="center")
        self.queue_tree.column("Items", width=350, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=scrollbar.set)

        self.queue_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        status_summary_frame = tk.Frame(self.tab_queue, bg="#f0f0f0")
        status_summary_frame.pack(fill="x", padx=10, pady=5)

        self.status_labels = {}
        for status in ["pending", "waiting", "serving", "completed", "cancelled"]:
            lbl = tk.Label(status_summary_frame, text=f"{status.capitalize()}: 0",
                           font=("Segoe UI", 10, "bold"), bg="#f0f0f0")
            lbl.pack(side="left", padx=10)
            self.status_labels[status] = lbl

        self.load_queue_orders()

    def load_queue_orders(self):
        selected_status = self.status_filter.get()

        conn = self.get_db_connection()
        if not conn:
            return
        cursor = conn.cursor(dictionary=True)

        where_clause = ""
        params = ()
        if selected_status != "All":
            where_clause = "WHERE o.status = %s"
            params = (selected_status,)

        query = f"""
            SELECT 
                o.order_code,
                DATE(o.created_at) AS order_date,
                TIME(o.created_at) AS order_time,
                o.total_amount,
                o.status,
                GROUP_CONCAT(CONCAT(m.name, ' (', oi.quantity, ' x ₱', oi.price, ')') SEPARATOR ', ') AS items_list
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN menu m ON oi.menu_id = m.id
            {where_clause}
            GROUP BY o.id
            ORDER BY 
                FIELD(o.status, 'pending', 'waiting', 'serving', 'completed', 'cancelled'),
                o.created_at DESC
        """
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
        except mysql.connector.Error as err:
            messagebox.showerror("Query Error", str(err))
            cursor.close()
            conn.close()
            return

        for row in self.queue_tree.get_children():
            self.queue_tree.delete(row)

        for row in results:
            order_code = row['order_code']
            order_date = row['order_date'].strftime("%Y-%m-%d") if row['order_date'] else ""
            order_time = str(row['order_time']) if row['order_time'] else ""
            total_amount = float(row['total_amount'])
            status = row['status'].capitalize()
            items_list = row['items_list'] if row['items_list'] else ""

            self.queue_tree.insert("", "end", values=(
                order_code,
                order_date,
                order_time,
                f"₱{total_amount:,.2f}",
                status,
                items_list
            ))

        self.update_status_summary(cursor)

        cursor.close()
        conn.close()

    def update_status_summary(self, cursor):
        query = """
            SELECT status, COUNT(*) as cnt
            FROM orders
            GROUP BY status
        """
        cursor.execute(query)
        counts = {row['status']: row['cnt'] for row in cursor.fetchall()}

        for status in self.status_labels:
            cnt = counts.get(status, 0)
            self.status_labels[status].config(text=f"{status.capitalize()}: {cnt}")

    def print_queue_orders(self):
        headers = ["Order Code", "Date", "Time", "Total", "Status", "Items"]
        rows = [self.queue_tree.item(r)["values"] for r in self.queue_tree.get_children()]
        if not rows:
            messagebox.showinfo("No Data", "No orders to print.")
            return
        meta = f"Filter: {self.status_filter.get()} | Records: {len(rows)} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        table_html = self._rows_to_html_table(headers, rows)
        self._open_print_window("Queue Status & Order History", meta, table_html)

    def build_summary_tab(self):
        filter_frame = tk.Frame(self.tab_summary, bg="#f0f0f0")
        filter_frame.pack(pady=10)

        tk.Label(filter_frame, text="From:",
                 font=("Segoe UI", 11), bg="#f0f0f0").grid(row=0, column=0, padx=5, pady=5)
        self.summary_from_entry = tk.Entry(filter_frame, font=("Segoe UI", 11), width=12)
        self.summary_from_entry.grid(row=0, column=1, padx=5, pady=5)
        default_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        self.summary_from_entry.insert(0, default_from)

        tk.Label(filter_frame, text="To:",
                 font=("Segoe UI", 11), bg="#f0f0f0").grid(row=0, column=2, padx=5, pady=5)
        self.summary_to_entry = tk.Entry(filter_frame, font=("Segoe UI", 11), width=12)
        self.summary_to_entry.grid(row=0, column=3, padx=5, pady=5)
        self.summary_to_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        btn_generate = tk.Button(filter_frame, text="Generate Summary",
                                 font=("Segoe UI", 10, "bold"),
                                 bg="#d35400", fg="white",
                                 command=self.load_sales_summary)
        btn_generate.grid(row=0, column=4, padx=10, pady=5)

        btn_print = tk.Button(filter_frame, text="Print",
                              font=("Segoe UI", 10),
                              bg="#bdc3c7", fg="#2c3e50",
                              command=self.print_sales_summary)
        btn_print.grid(row=0, column=5, padx=10, pady=5)

        self.summary_text = tk.Text(self.tab_summary, font=("Consolas", 11),
                                    bg="white", fg="#2c3e50", wrap="word",
                                    height=15, width=90)
        self.summary_text.pack(padx=20, pady=10, fill="both", expand=True)

        table_frame = tk.Frame(self.tab_summary, bg="#f0f0f0")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0,10))

        columns = ("Date", "Orders", "Total Sales", "Avg Order Value")
        self.summary_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=6)

        self.summary_tree.heading("Date", text="Date")
        self.summary_tree.heading("Orders", text="Orders")
        self.summary_tree.heading("Total Sales", text="Total Sales")
        self.summary_tree.heading("Avg Order Value", text="Avg Order Value")

        self.summary_tree.column("Date", width=120, anchor="center")
        self.summary_tree.column("Orders", width=80, anchor="center")
        self.summary_tree.column("Total Sales", width=130, anchor="e")
        self.summary_tree.column("Avg Order Value", width=130, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=scrollbar.set)

        self.summary_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.load_sales_summary()

    def load_sales_summary(self):
        from_date = self.summary_from_entry.get().strip()
        to_date = self.summary_to_entry.get().strip()

        try:
            datetime.strptime(from_date, "%Y-%m-%d")
            datetime.strptime(to_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Use YYYY-MM-DD format")
            return

        conn = self.get_db_connection()
        if not conn:
            return
        cursor = conn.cursor(dictionary=True)

        query_overall = """
            SELECT 
                COUNT(DISTINCT o.id) AS total_orders,
                COALESCE(SUM(o.total_amount), 0) AS total_sales,
                COALESCE(AVG(o.total_amount), 0) AS avg_order_value
            FROM orders o
            WHERE DATE(o.created_at) BETWEEN %s AND %s
              AND o.status IN ('completed', 'serving', 'waiting', 'pending')
        """
        cursor.execute(query_overall, (from_date, to_date))
        overall = cursor.fetchone()

        query_items = """
            SELECT 
                m.name,
                SUM(oi.quantity) AS total_qty,
                SUM(oi.quantity * oi.price) AS revenue
            FROM order_items oi
            JOIN menu m ON oi.menu_id = m.id
            JOIN orders o ON oi.order_id = o.id
            WHERE DATE(o.created_at) BETWEEN %s AND %s
            GROUP BY m.id
            ORDER BY total_qty DESC
            LIMIT 5
        """
        cursor.execute(query_items, (from_date, to_date))
        top_items = cursor.fetchall()

        query_daily = """
            SELECT 
                DATE(o.created_at) AS date,
                COUNT(DISTINCT o.id) AS order_count,
                COALESCE(SUM(o.total_amount), 0) AS daily_sales,
                COALESCE(AVG(o.total_amount), 0) AS avg_order
            FROM orders o
            WHERE DATE(o.created_at) BETWEEN %s AND %s
            GROUP BY DATE(o.created_at)
            ORDER BY date DESC
        """
        cursor.execute(query_daily, (from_date, to_date))
        daily_data = cursor.fetchall()

        for row in self.summary_tree.get_children():
            self.summary_tree.delete(row)

        for row in daily_data:
            date_str = row['date'].strftime("%Y-%m-%d") if row['date'] else ""
            self.summary_tree.insert("", "end", values=(
                date_str,
                row['order_count'],
                f"₱{float(row['daily_sales']):,.2f}",
                f"₱{float(row['avg_order']):,.2f}"
            ))

        summary_str = f"=== SALES SUMMARY REPORT ===\n"
        summary_str += f"Period: {from_date} to {to_date}\n\n"
        summary_str += f"Total Orders: {overall['total_orders']}\n"
        summary_str += f"Total Sales: ₱{overall['total_sales']:,.2f}\n"
        summary_str += f"Average Order Value: ₱{overall['avg_order_value']:,.2f}\n\n"
        summary_str += "--- Top 5 Selling Items ---\n"
        for idx, item in enumerate(top_items, 1):
            summary_str += f"{idx}. {item['name']} - Qty: {item['total_qty']}, Revenue: ₱{float(item['revenue']):,.2f}\n"

        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary_str)

        self._summary_cache = {
            "overall": overall,
            "top_items": top_items,
            "daily_data": daily_data,
            "from_date": from_date,
            "to_date": to_date
        }

        cursor.close()
        conn.close()

    def print_sales_summary(self):
        if not hasattr(self, '_summary_cache'):
            messagebox.showinfo("No Data", "Generate a summary first.")
            return

        c = self._summary_cache
        overall = c['overall']
        top_items = c['top_items']
        from_date = c['from_date']
        to_date = c['to_date']

        meta = f"Period: {from_date} to {to_date} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        overview_html = f"""
        <div class='summary'>
          Total Orders: <span>{overall['total_orders']}</span> &nbsp;|&nbsp;
          Total Sales: <span>₱{overall['total_sales']:,.2f}</span> &nbsp;|&nbsp;
          Avg Order Value: <span>₱{overall['avg_order_value']:,.2f}</span>
        </div>
        """

        top_rows = [(item['name'], item['total_qty'], f"₱{float(item['revenue']):,.2f}") for item in top_items]
        top_html = "<h3>Top 5 Selling Items</h3>" + self._rows_to_html_table(("Item", "Qty Sold", "Revenue"), top_rows)

        daily_rows = [self.summary_tree.item(r)["values"] for r in self.summary_tree.get_children()]
        daily_html = "<h3>Daily Breakdown</h3>" + self._rows_to_html_table(("Date", "Orders", "Total Sales", "Avg Order Value"), daily_rows)

        body_html = overview_html + top_html + daily_html
        self._open_print_window("Sales Summary Report", meta, body_html)

def main():
    root = tk.Tk()
    app = ReportsWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()