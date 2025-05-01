from tkinter import *
import subprocess
from dashboard import dashboard
from transaction import transaction
from customer import customer
from inventory import inventory

pages = {
    "Dashboard": dashboard,
    "Transaction": transaction,
    "Customer": customer,
    "Inventory": inventory
}

def load(page):
    for widget in content.winfo_children():
        widget.destroy()
    pages.get(page, lambda x: None)(content)

def logout_user():
    root.destroy()
    subprocess.Popen(["python", "admin_login.py"])

def create_sidebar(parent, on_select):
    sidebar = Frame(parent, bg="white", width=230)
    sidebar.pack(side="left", fill="y")

    Label(sidebar,
          text="Hera Printing",
          bg="white",
          fg="black",
          font=("Arial", 14, "bold"),
          anchor="w",
          padx=20).pack(pady=(20, 30),
                        fill="x")

    menu_sidebar = [
        ("", "Dashboard"),
        ("", "Transaction"),
        ("", "Customer"),
        ("", "Inventory")
    ]

    for icon, label in menu_sidebar:
        item = Label(sidebar,
                     text=f"{icon}  {label}",
                     bg="white",
                     fg="black",
                     font=("Arial", 10),
                     anchor="w",
                     padx=20,
                     pady=10)
        item.pack(fill="x")
        item.bind("<Button-1>", lambda e, l=label: on_select(l))

    Label(sidebar, bg="white").pack(expand=True, fill="both")

    logout = Label(sidebar,
                   text="↳ Logout",
                   bg="white",
                   fg="black",
                   font=("Arial", 10),
                   anchor="w",
                   padx=20,
                   pady=10,
                   cursor="hand2")
    
    logout.pack(fill="x", pady=(0, 20))
    logout.bind("<Button-1>", lambda e: logout_user())

def topbar(parent):
    topbar = Frame(parent,
                   bg="#f5f5f5",
                   height=50)
    topbar.pack(side="top", fill="x")
    topbar.pack_propagate(False)

    notif_icon = Label(topbar,
                        text="Profile",
                        bg="#f5f5f5",
                        fg="black",
                        font=("Arial", 12))
    notif_icon.pack(side="right",
                     padx=10,
                     pady=10)

    profile_icon = Label(topbar,
                         text="Notification",
                         bg="#f5f5f5",
                         fg="black",
                         font=("Arial", 12))
    profile_icon.pack(side="right", padx=10, pady=10)

root = Tk()
root.title("Hera Printing Online")
root.geometry("900x500")
root.configure(bg="#f5f5f5")

create_sidebar(root, load)
topbar(root)

content = Frame(root, bg="#f5f5f5")
content.pack(expand=True, fill="both")

load("Dashboard")

root.mainloop()
