from tkinter import *

def customer_transaction(parent, back_callback):
    for widget in parent.winfo_children():
        widget.destroy()

    parent.configure(bg="white")

    box = Frame(parent, bg="white",
                bd=1, relief="solid")
    box.pack(padx=40, pady=30,
             fill="both", expand=True)

    Label(box, text="ARIANA GRANDE",
          font=("Arial", 10, "bold"),
          bg="white", fg="black").pack(anchor="w", padx=20, pady=(10, 5))
    Label(box, text="APP DEV PAPERS.pdf",
          bg="white", fg="black").pack(anchor="w", padx=30)
    
    
    Label(box, text="LONG BOND PAPER", bg="white", fg="black").pack(anchor="w", padx=30)
    
    
    Label(box, text="3 COPIES", bg="white", fg="black").pack(anchor="w", padx=30)
    
    
    Label(box, text="COLORED", bg="white", fg="black").pack(anchor="w", padx=30)


    Label(box, text="Total bill", bg="white", fg="black").pack(anchor="e", padx=40, pady=(10, 0))
    
    
    Label(box, text="₱125", font=("Arial", 10, "bold"), bg="white", fg="black").pack(anchor="e", padx=40)


    Button(box, text="Cancel", bg="#e0e0e0", fg="black", command=back_callback).pack(pady=20)
