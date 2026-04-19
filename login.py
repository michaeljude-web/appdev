import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import subprocess
import sys

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="app"
    )

def perform_login(login_win, username, password):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
    admin = cursor.fetchone()

    if admin:
        messagebox.showinfo("Login Success", "Welcome Admin!")
        login_win.destroy()
        subprocess.Popen([sys.executable, "admin_dashboard.py"])
        sys.exit()

    cursor.execute("SELECT * FROM staff WHERE username=%s AND password=%s", (username, password))
    staff = cursor.fetchone()

    if staff:
        messagebox.showinfo("Login Success", f"Welcome {staff[1]} {staff[2]}!")
        login_win.destroy()
        subprocess.Popen([sys.executable, "staff_dashboard.py"])
        sys.exit()

    messagebox.showerror("Login Failed", "Invalid Username or Password")
    conn.close()

def main_login():
    login_win = tk.Tk()
    login_win.title("Snack in Save 9Nueve - Login")
    login_win.geometry("400x450")
    login_win.configure(bg="#fdf6e3")
    login_win.resizable(False, False)

    login_win.eval('tk::PlaceWindow . center')

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", background="#fdf6e3", font=("Segoe UI", 11))
    style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
    style.configure("Accent.TButton", background="#d35400", foreground="white")
    style.map("Accent.TButton", background=[("active", "#a04000")])

    header_frame = tk.Frame(login_win, bg="#d35400", height=100)
    header_frame.pack(fill="x", pady=(0, 20))

    brand_label = tk.Label(header_frame, text="Snack in Save", font=("Segoe UI", 20, "bold"), fg="white", bg="#d35400")
    brand_label.pack(pady=15)
    sub_label = tk.Label(header_frame, text="9Nueve", font=("Segoe UI", 12), fg="#ffe0b3", bg="#d35400")
    sub_label.pack()

    form_frame = tk.Frame(login_win, bg="#fdf6e3")
    form_frame.pack(padx=30, pady=20, fill="both", expand=True)

    ttk.Label(form_frame, text="Username:", font=("Segoe UI", 12)).pack(anchor="w", pady=(10, 5))
    username_entry = ttk.Entry(form_frame, font=("Segoe UI", 12), width=25)
    username_entry.pack(fill="x", pady=(0, 10))
    username_entry.focus()

    ttk.Label(form_frame, text="Password:", font=("Segoe UI", 12)).pack(anchor="w", pady=(10, 5))
    password_entry = ttk.Entry(form_frame, font=("Segoe UI", 12), width=25, show="•")
    password_entry.pack(fill="x", pady=(0, 10))

    login_btn = ttk.Button(form_frame, text="LOGIN", style="Accent.TButton",
                           command=lambda: perform_login(login_win, username_entry.get(), password_entry.get()))
    login_btn.pack(pady=20, fill="x")


    login_win.bind('<Return>', lambda event: perform_login(login_win, username_entry.get(), password_entry.get()))

    login_win.mainloop()

if __name__ == "__main__":
    main_login()