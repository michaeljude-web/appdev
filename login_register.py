from tkinter import *
from tkinter import messagebox
import mysql.connector

#-----------------------------DATABASE------------------------------------------------------------------------------------
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

#-------------------------------LOGIN--------------------------------------------------------------------------------------
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
            admin_dashboard()
        elif role == "staff":
            print("Staff Access Granted")
            staff_dashboard()
    else:
        messagebox.showerror("Login Failed", "Invalid Username or Password")
        
#-------------------------------REGISTER--------------------------------------------------------------------------------------    
def save_account():
    username = reg_username_entry.get()
    password = reg_password_entry.get()
    role = role_entry.get()
    
    if not username or not password or not role:
        messagebox.showerror("Input Failed", "All fields are required", parent=register_garde)
        return
    cursor = mydb.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
        mydb.commit()
        messagebox.showinfo("Success", "Registration Successful", parent=register_garde)
    except mysql.connector.Error as er:
        messagebox.showerror("Database Error", f"Error: {er}", parent=register_garde)
    finally:
        cursor.close()

#-------------------------------ADMIN DASHBOARD----------------------------------------------------------
def admin_dashboard():
    new_window = Toplevel(window)
    new_window.title("Admin Dashboard")
    new_window.geometry("400x200")
    new_window.config(bg='#d0f0c0')

    Label(new_window, text="Welcome, Admin!", font=('Comic Sans MS', 16), bg='#d0f0c0', fg='#336600').pack(pady=30)
    Button(new_window, text="Back to Main", font=('Arial', 12),
           bg='#ffcccb', command=new_window.destroy).pack(pady=10)


#-------------------------------STAFF DASHBOARD----------------------------------------------------------
def staff_dashboard():
    new_window = Toplevel(window)
    new_window.title("Staff Dashboard")
    new_window.geometry("400x200")
    new_window.config(bg='#d0f0c0')

    Label(new_window, text="Welcome, Staff!", font=('Comic Sans MS', 16), bg='#d0f0c0', fg='#336600').pack(pady=30)
    Button(new_window, text="Back to Main", font=('Arial', 12),
           bg='#ffcccb', command=new_window.destroy).pack(pady=10)


#-------------------------------Register WINDOW---------------------------------------------------------------
def register():
    global reg_username_entry, reg_password_entry, role_entry, register_garde

    register_garde = Toplevel(window)
    register_garde.title("Register")
    register_garde.geometry("400x300")
    register_garde.config(bg='#d0f0c0')
    
    Label(register_garde, text="Register Now!", font=('Comic Sans MS', 22, 'bold'),
          bg='#ffe6f0', fg='#cc3366').pack(pady=20)

    form_frame = Frame(register_garde, bg='#fff0f5', bd=2, relief=RIDGE, padx=20, pady=20)
    form_frame.pack(pady=10)

    Label(form_frame, text="Username:", font=('Arial', 12), bg='#fff0f5', fg="black").pack(anchor='w')
    reg_username_entry = Entry(form_frame, font=('Arial', 12), width=25)
    reg_username_entry.pack(pady=5)

    Label(form_frame, text="Password:", font=('Arial', 12), bg='#fff0f5').pack(anchor='w')
    reg_password_entry = Entry(form_frame, font=('Arial', 12), show='*', width=25)
    reg_password_entry.pack(pady=5)

    Label(form_frame, text="Role:", font=('Arial', 12), bg='#fff0f5').pack(anchor='w')
    role_entry = Entry(form_frame, font=('Arial', 12), width=25)
    role_entry.pack(pady=5)

    Button(form_frame, text="Register", font=('Arial', 12, 'bold'),
           bg='#ff99c8', fg='white', activebackground='#ff66a3', width=22,
           command=save_account).pack(pady=15)


#-------------------------------MAIN WINDOW---------------------------------------------------------------
window = Tk()
window.geometry("550x390")
window.title("garde_firstGUI")
window.config(bg='#ffe6f0')

Label(window, text="Welcome!", font=('Comic Sans MS', 22, 'bold'),
      bg='#ffe6f0', fg='#cc3366').pack(pady=20)

garde_main = Frame(window, bg='#fff0f5', bd=2, relief=RIDGE, padx=20, pady=20)
garde_main.pack(pady=10)

Label(garde_main, text="Username:", font=('Arial', 12), bg='#fff0f5', fg="black").pack(anchor='w')
username_entry = Entry(garde_main, font=('Arial', 12), width=25)
username_entry.pack(pady=5)

Label(garde_main, text="Password", font=('Arial', 12), bg='#fff0f5', fg="black").pack(anchor='w')
password_entry = Entry(garde_main, font=('Arial', 12), show='*', width=25)
password_entry.pack(pady=5)

Button(garde_main, text="Login", font=('Arial', 12, 'bold'),
       bg='#ff99c8', fg='white', activebackground='#ff66a3', width=22,
       command=login).pack(pady=15)

Button(garde_main, text="Register", font=('Arial', 12, 'bold'),
       bg='#ff99c8', fg='white', activebackground='#ff66a3', width=22,
       command=register).pack(pady=15)

window.mainloop()

