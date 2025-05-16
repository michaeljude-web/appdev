from tkinter import *
from tkinter import messagebox
import mysql.connector

def db_connection():
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="garde"
        )
        messagebox.showinfo("Database Connection", "Connected")
        return mydb
    except mysql.connector.Error as err:
        messagebox.showerror("Database Connection", f"Error: {err}")
        return None

mydb = db_connection()
if mydb is None:
    exit()

def login():
    username = username_entry.get()
    password = password_entry.get()
    
    mycursor = mydb.cursor()
    sql = "SELECT role FROM users WHERE username = %s AND password = %s"
    mycursor.execute(sql, (username, password))
    result = mycursor.fetchone()
    
    if result:
        role = result[0]
        if role == "admin":
            print("Admin Access Granted")
            dashboard(role)
        elif role == "staff":
            print("Staff Access Granted")
            dashboard(role)
    else:
        messagebox.showerror("Login Failed", "Invalid Username or Password")

def dashboard(role):
    new_window = Toplevel(window)
    new_window.title(f"{role.capitalize()} Dashboard")
    new_window.geometry("400x200")
    new_window.config(bg='#d0f0c0')

    Label(new_window, text=f"Welcome, {role}!", font=('Comic Sans MS', 16), bg='#d0f0c0', fg='#336600').pack(pady=30)

window = Tk()
window.geometry("360x360")
window.title("garde")
window.config(bg='#ffe6f0')

Label(window, text="Welcome!", font=('Comic Sans MS', 22, 'bold'),
      bg='#ffe6f0', fg='#cc3366').pack(pady=20)

form_frame = Frame(window, bg='#fff0f5', bd=2, relief=RIDGE, padx=20, pady=20)
form_frame.pack(pady=10)

Label(form_frame, text="Username:", font=('Arial', 12), bg='#fff0f5', fg="black").pack(anchor='w')
username_entry = Entry(form_frame, font=('Arial', 12), width=25)
username_entry.pack(pady=5)

Label(form_frame, text="Password", font=('Arial', 12), bg='#fff0f5').pack(anchor='w')
password_entry = Entry(form_frame, font=('Arial', 12), show='*', width=25)
password_entry.pack(pady=5)

Button(form_frame, text="Login", font=('Arial', 12, 'bold'),
       bg='#ff99c8', fg='white', activebackground='#ff66a3', width=22,
       command=login).pack(pady=15)

window.mainloop()
