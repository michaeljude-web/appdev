from tkinter import *

def customer(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    parent.configure(bg="white")

    Label(parent,
          text="Customer List",
          font=("Arial", 12, "bold"),
          bg="white",
          fg="black").pack(anchor="w", padx=20, pady=10)

    row = Frame(parent, bg="white")
    row.pack(fill="x", padx=20, pady=10)

    info = Frame(row, bg="white")
    info.pack(side="left", fill="x", expand=True)

    Label(info,
          text="FYANG SMITH",
          font=("Arial", 10, "bold"),
          bg="white",
          fg="black").pack(anchor="w")
             
    Label(info,
          text="fsm!th@gmail.com",
          font=("Arial", 9),
          bg="white",
          fg="black").pack(anchor="w")

    buttons = Frame(row, bg="white")
    buttons.pack(side="right")

    Button(buttons,
           text="Approve",
           bg="#1E3A8A",
           fg="white",
           font=("Arial", 9),
           width=10).pack(side="left", padx=5)

    Button(buttons,
           text="❌",
           bg="#7f1d1d",
           fg="white",
           font=("Arial", 9),
           width=3).pack(side="left", padx=5)
