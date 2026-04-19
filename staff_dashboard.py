import tkinter as tk
from tkinter import ttk, messagebox
from staff_sidebar import add_staff_sidebar
import subprocess
import sys

def logout(win):
    win.destroy()
    subprocess.Popen([sys.executable, "login.py"])
    sys.exit()

def main():
    win = tk.Tk()
    win.title("Staff Dashboard - Snack in Save 9Nueve")
    win.geometry("1280x720")
    win.configure(bg="#f0f0f0")
    
    add_staff_sidebar(win)
    
    content_frame = tk.Frame(win, bg="#f0f0f0")
    content_frame.pack(side="right", fill="both", expand=True)
    
    style = ttk.Style()
    style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"), foreground="#d35400", background="#f0f0f0")
    style.configure("Info.TLabel", font=("Segoe UI", 12), background="#f0f0f0")
    
    ttk.Label(content_frame, text="STAFF DASHBOARD", style="Title.TLabel").pack(pady=50)
    ttk.Label(content_frame, text="Welcome, Staff Member!", style="Info.TLabel").pack()
    
    # Summary cards (sample data)
    summary_frame = tk.Frame(content_frame, bg="#f0f0f0")
    summary_frame.pack(pady=40)
    
    cards = [
        ("Today's Orders", "24"),
        ("Pending Queue", "5"),
        ("Completed", "19")
    ]
    
    for title, value in cards:
        card = tk.Frame(summary_frame, bg="white", relief="ridge", bd=1, padx=20, pady=10)
        card.pack(side="left", padx=10)
        tk.Label(card, text=title, font=("Segoe UI", 10), bg="white").pack()
        tk.Label(card, text=value, font=("Segoe UI", 18, "bold"), fg="#d35400", bg="white").pack()
    
    win.mainloop()

if __name__ == "__main__":
    main()