import tkinter as tk
from tkinter import ttk
import subprocess
import sys

def add_sidebar(parent):
    sidebar = tk.Frame(parent, bg="#2c3e50", width=200)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    header_label = tk.Label(
        sidebar,
        text="Snack in Save\n9Nueve",
        font=("Segoe UI", 14, "bold"),
        bg="#2c3e50",
        fg="white",
        pady=20
    )
    header_label.pack(fill="x")

    tk.Frame(sidebar, bg="#3d5166", height=1).pack(fill="x", padx=15, pady=(0, 10))

    def navigate(page_script):
        parent.destroy()
        subprocess.Popen([sys.executable, page_script])
        sys.exit()

    nav_buttons = [
        ("Dashboard", "admin_dashboard.py"),
        ("Account",   "admin_account.py"),
        ("Menu",      "admin_menu.py"),
        ("Inventory", "admin_inventory.py"),
        ("Reports",   "admin_reports.py"),
    ]

    style = ttk.Style()
    style.configure(
        "Sidebar.TButton",
        font=("Segoe UI", 11),
        padding=10
    )
    style.map(
        "Sidebar.TButton",
        background=[("active", "#34495e")],
        foreground=[("active", "white")]
    )

    for text, script in nav_buttons:
        btn = ttk.Button(
            sidebar,
            text=text,
            style="Sidebar.TButton",
            command=lambda s=script: navigate(s)
        )
        btn.pack(fill="x", padx=10, pady=3)

    bottom_frame = tk.Frame(sidebar, bg="#2c3e50")
    bottom_frame.pack(side="bottom", fill="x", padx=10, pady=15)

    tk.Button(
        bottom_frame,
        text="Logout",
        font=("Segoe UI", 11, "bold"),
        bg="#c0392b",
        fg="white",
        activebackground="#a93226",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        pady=10,
        command=lambda: navigate("login.py")
    ).pack(fill="x")

    return sidebar