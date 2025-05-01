from tkinter import *
from customer_transaction import customer_transaction
from add_transaction import open_add_transaction_modal

def load_dashboard():
    for widget in content.winfo_children():
        widget.destroy()
    create_list_section(content)
    create_floating_plus_button(content)

def open_transaction():
    customer_transaction(content, load_dashboard)

def create_list_section(parent):
    section = Frame(parent, bg="#f5f5f5")
    section.pack(padx=20, pady=20, fill="both", expand=True)

    item = Frame(section,
                 bg="white",
                 highlightbackground="gray",
                 highlightthickness=1,
                 cursor="hand2")
    
    item.pack(fill="x",
              pady=5)

    label = Label(item,
                  text="app dev.pdf",
                  bg="white",
                  fg="black",
                  font=("Arial", 12),
                  anchor="w")
    
    label.pack(side="left",
               padx=10,
               pady=10)

    pending_label = Label(item, text="Pending",
                          bg="white", fg="black",
                          font=("Arial", 12,))
    
    pending_label.pack(side="right",
                       padx=10,
                       pady=10)

    label.bind("<Button-1>", lambda e: open_transaction())

def create_floating_plus_button(parent):
    plus_button = Button(parent,
                         text="+",
                         font=("Arial", 20, "bold"),
                         bg="#1E3A8A", fg="white",
                         width=3, height=1, bd=0,
                         relief="flat", command=lambda: open_add_transaction_modal(root))
    
    plus_button.place(relx=0.95, rely=0.85, anchor="center")

def topbar(parent):
    topbar = Frame(parent, bg="white", height=50)
    topbar.pack(side="top", fill="x")
    topbar.pack_propagate(False)

    logo_label = Label(topbar, text="Hera Printing",
                       bg="white", fg="black",
                       font=("Arial", 14, "bold"))
    
    logo_label.pack(side="left",
                    padx=20, pady=10)

    notif_icon = Label(topbar,
                       text="Notification",
                       bg="white",
                       fg="black",
                       font=("Arial", 12))
    
    notif_icon.pack(side="right", padx=10, pady=10)

    profile_icon = Label(topbar, text="Profile",
                         bg="white", fg="black",
                         font=("Arial", 12))
    profile_icon.pack(side="right",
                      padx=10, pady=10)

root = Tk()
root.title("Hera Printing Online")
root.geometry("900x500")
root.configure(bg="#f5f5f5")

topbar(root)

content = Frame(root, bg="#f5f5f5")
content.pack(expand=True, fill="both")

load_dashboard()

root.mainloop()
