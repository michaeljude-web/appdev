import tkinter as tk
from sidebar import add_sidebar

def main():
    win = tk.Tk()
    win.title("Admin Dashboard - Snack in Save 9Nueve")
    win.geometry("1280x720")
    win.configure(bg="#f0f0f0")
    
    add_sidebar(win)
    
    content_frame = tk.Frame(win, bg="#f0f0f0")
    content_frame.pack(side="right", fill="both", expand=True)
    
    tk.Label(content_frame, text="ADMIN PANEL", font=("Segoe UI", 24, "bold"), bg="#f0f0f0", fg="#d35400").pack(pady=50)
    tk.Label(content_frame, text="Welcome, Administrator!", font=("Segoe UI", 12), bg="#f0f0f0").pack()
    
    summary_frame = tk.Frame(content_frame, bg="#f0f0f0")
    summary_frame.pack(pady=40)
    
    cards = [
        ("Total Orders", "128"),
        ("Pending", "12"),
        ("Today's Sales", "₱3,240")
    ]
    
    for title, value in cards:
        card = tk.Frame(summary_frame, bg="white", relief="ridge", bd=1, padx=20, pady=10)
        card.pack(side="left", padx=10)
        tk.Label(card, text=title, font=("Segoe UI", 10), bg="white").pack()
        tk.Label(card, text=value, font=("Segoe UI", 18, "bold"), fg="#d35400", bg="white").pack()
    
    win.mainloop()

if __name__ == "__main__":
    main()