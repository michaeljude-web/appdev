from tkinter import *
from tkinter import ttk

def open_add_transaction_modal(master):
    modal = Toplevel(master)
    modal.title("")
    modal.geometry("400x400")
    modal.configure(bg="white")
    modal.grab_set()
    modal.resizable(False, False)

    box = Frame(modal, bg="white", bd=1, relief="solid")
    box.place(relx=0.5, rely=0.5, anchor="center", width=350, height=330)

    Label(box,
          text="Select file",
          bg="white",
          fg="black",
          anchor="w").pack(fill="x", padx=20, pady=(20, 5))

    Entry(box,
          bg="white",
          fg="black").pack(fill="x", padx=20)

    Label(box,
          text="Select size",
          bg="white",
          fg="black",
          anchor="w").pack(fill="x", padx=20, pady=(15, 5))

    size_var = StringVar(value="A4")

    ttk.Combobox(box,
                 textvariable=size_var,
                 values=["A4", "SHORT", "LONG"]).pack(fill="x", padx=20)

    Label(box,
          text="Number of copies",
          bg="white",
          fg="black",
          anchor="w").pack(fill="x", padx=20, pady=(15, 5))

    Entry(box,
          bg="white",
          fg="black").pack(fill="x", padx=20)

    Label(box,
          text="",
          bg="white").pack(pady=5)

    type_frame = Frame(box, bg="white")
    type_frame.pack(pady=5)

    print_type = StringVar(value="B&W")

    Radiobutton(type_frame,
                text="B&W",
                variable=print_type,
                value="B&W",
                bg="white",
                fg="black").pack(side="left", padx=10)

    Radiobutton(type_frame,
                text="Colored",
                variable=print_type,
                value="Colored",
                bg="white",
                fg="black").pack(side="left", padx=10)

    Button(box,
           text="Send",
           bg="#1E3A8A",
           fg="white",
           width=20).pack(pady=20)
