
import tkinter as tk
from tkinter import ttk, messagebox
from sidebar import add_sidebar
import mysql.connector
import re

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "app"
}

def connect_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Connection failed: {err}")
        return None

def validate_name(value):
    return bool(re.fullmatch(r"[A-Za-z\s\-']+", value))

def validate_age(value):
    return value.isdigit() and 18 <= int(value) <= 50

def validate_contact(value):
    return bool(re.fullmatch(r"[\d\+\-\s\(\)]+", value)) and len(value) >= 7

def refresh_treeview(tree, staff_id_map):
    for row in tree.get_children():
        tree.delete(row)
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, firstname, lastname, address, contact_number, age, username FROM staff ORDER BY id")
        rows = cursor.fetchall()
        for row in rows:
            staff_id, fname, lname, addr, contact, age, username = row
            fullname = f"{fname} {lname}"
            staff_id_map[staff_id] = True
            tree.insert("", tk.END, iid=str(staff_id), values=(fullname, addr or "", contact or "", age or "", username, "Edit     |    Delete"))
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Failed to load data: {err}")
    finally:
        conn.close()

def styled_form_window(title, geometry="500x580"):
    win = tk.Toplevel()
    win.title(title)
    win.geometry(geometry)
    win.configure(bg="#f5f6fa")
    win.grab_set()
    win.resizable(False, False)
    return win

def build_form_fields(parent, labels):
    entries = {}
    for i, (key, label) in enumerate(labels):
        tk.Label(parent, text=label, font=("Segoe UI", 10), bg="#f5f6fa", fg="#555").grid(row=i, column=0, sticky="w", pady=6, padx=(0, 12))
        entry = tk.Entry(parent, font=("Segoe UI", 11), bd=0, relief="flat", highlightthickness=1,
                         highlightbackground="#ccc", highlightcolor="#d35400", bg="white", width=28)
        entry.grid(row=i, column=1, pady=6, ipady=6, sticky="ew")
        entries[key] = entry
    return entries

def show_field_error(entry, message):
    entry.config(highlightbackground="#e74c3c", highlightcolor="#e74c3c")
    messagebox.showerror("Validation Error", message)
    entry.focus_set()

def clear_field_errors(entries):
    for e in entries.values():
        e.config(highlightbackground="#ccc", highlightcolor="#d35400")

def edit_staff_item(staff_id, tree, staff_id_map):
    conn = connect_db()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT firstname, lastname, address, contact_number, age, username, password FROM staff WHERE id=%s", (staff_id,))
    staff = cursor.fetchone()
    conn.close()
    if not staff:
        messagebox.showerror("Error", "Staff not found.")
        return

    win = styled_form_window("Edit Staff Account")

    header = tk.Frame(win, bg="#d35400", height=55)
    header.pack(fill="x")
    tk.Label(header, text="Edit Staff Account", font=("Segoe UI", 14, "bold"), bg="#d35400", fg="white").pack(side="left", padx=20, pady=12)

    form_frame = tk.Frame(win, bg="#f5f6fa", padx=30, pady=20)
    form_frame.pack(fill="both", expand=True)

    field_defs = [
        ("firstname", "First Name"),
        ("lastname",  "Last Name"),
        ("address",   "Address"),
        ("contact",   "Contact Number"),
        ("age",       "Age (18-50)"),
        ("username",  "Username"),
        ("password",  "Password (blank = unchanged)"),
    ]
    entries = build_form_fields(form_frame, field_defs)

    entries["firstname"].insert(0, staff[0])
    entries["lastname"].insert(0, staff[1])
    entries["address"].insert(0, staff[2] or "")
    entries["contact"].insert(0, staff[3] or "")
    entries["age"].insert(0, staff[4] or "")
    entries["username"].insert(0, staff[5])
    entries["password"].config(show="●")

    def update_staff():
        clear_field_errors(entries)
        fname   = entries["firstname"].get().strip()
        lname   = entries["lastname"].get().strip()
        addr    = entries["address"].get().strip()
        contact = entries["contact"].get().strip()
        age_str = entries["age"].get().strip()
        user    = entries["username"].get().strip()
        pwd     = entries["password"].get().strip()

        if not fname:
            show_field_error(entries["firstname"], "First name is required."); return
        if not validate_name(fname):
            show_field_error(entries["firstname"], "First name must contain letters only (no numbers or special characters)."); return
        if not lname:
            show_field_error(entries["lastname"], "Last name is required."); return
        if not validate_name(lname):
            show_field_error(entries["lastname"], "Last name must contain letters only (no numbers or special characters)."); return
        if contact and not validate_contact(contact):
            show_field_error(entries["contact"], "Contact number must contain digits only."); return
        if age_str and not validate_age(age_str):
            show_field_error(entries["age"], "Age must be between 18 and 50."); return
        if not user:
            show_field_error(entries["username"], "Username is required."); return

        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            age_val = int(age_str) if age_str else None
            if pwd:
                cursor.execute("""
                    UPDATE staff SET firstname=%s, lastname=%s, address=%s, contact_number=%s,
                    age=%s, username=%s, password=%s WHERE id=%s
                """, (fname, lname, addr, contact, age_val, user, pwd, staff_id))
            else:
                cursor.execute("""
                    UPDATE staff SET firstname=%s, lastname=%s, address=%s, contact_number=%s,
                    age=%s, username=%s WHERE id=%s
                """, (fname, lname, addr, contact, age_val, user, staff_id))
            conn.commit()
            messagebox.showinfo("Success", "Staff account updated.")
            win.destroy()
            refresh_treeview(tree, staff_id_map)
        except mysql.connector.IntegrityError:
            show_field_error(entries["username"], "Username already exists.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    btn_frame = tk.Frame(win, bg="#f5f6fa", pady=10)
    btn_frame.pack(fill="x", padx=30)
    tk.Button(btn_frame, text="Update", bg="#d35400", fg="white", font=("Segoe UI", 11, "bold"),
              relief="flat", cursor="hand2", padx=30, pady=8, command=update_staff).pack(fill="x")

def delete_staff_item(staff_id, tree, staff_id_map):
    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this staff account?"):
        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM staff WHERE id=%s", (staff_id,))
            conn.commit()
            messagebox.showinfo("Success", "Staff account deleted.")
            refresh_treeview(tree, staff_id_map)
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

def add_staff(tree, staff_id_map):
    win = styled_form_window("Add Staff Account")

    header = tk.Frame(win, bg="#2c3e50", height=55)
    header.pack(fill="x")
    tk.Label(header, text="Add New Staff Account", font=("Segoe UI", 14, "bold"), bg="#2c3e50", fg="white").pack(side="left", padx=20, pady=12)

    form_frame = tk.Frame(win, bg="#f5f6fa", padx=30, pady=20)
    form_frame.pack(fill="both", expand=True)

    field_defs = [
        ("firstname", "First Name"),
        ("lastname",  "Last Name"),
        ("address",   "Address"),
        ("contact",   "Contact Number"),
        ("age",       "Age (18-50)"),
        ("username",  "Username"),
        ("password",  "Password"),
    ]
    entries = build_form_fields(form_frame, field_defs)
    entries["password"].config(show="●")

    def save_staff():
        clear_field_errors(entries)
        fname   = entries["firstname"].get().strip()
        lname   = entries["lastname"].get().strip()
        addr    = entries["address"].get().strip()
        contact = entries["contact"].get().strip()
        age_str = entries["age"].get().strip()
        user    = entries["username"].get().strip()
        pwd     = entries["password"].get().strip()

        if not fname:
            show_field_error(entries["firstname"], "First name is required."); return
        if not validate_name(fname):
            show_field_error(entries["firstname"], "First name must contain letters only (no numbers or special characters)."); return
        if not lname:
            show_field_error(entries["lastname"], "Last name is required."); return
        if not validate_name(lname):
            show_field_error(entries["lastname"], "Last name must contain letters only (no numbers or special characters)."); return
        if contact and not validate_contact(contact):
            show_field_error(entries["contact"], "Contact number must contain digits only."); return
        if age_str and not validate_age(age_str):
            show_field_error(entries["age"], "Age must be between 18 and 50."); return
        if not user:
            show_field_error(entries["username"], "Username is required."); return
        if not pwd:
            show_field_error(entries["password"], "Password is required."); return

        conn = connect_db()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            age_val = int(age_str) if age_str else None
            cursor.execute("""
                INSERT INTO staff (firstname, lastname, address, contact_number, age, username, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (fname, lname, addr, contact, age_val, user, pwd))
            conn.commit()
            messagebox.showinfo("Success", "Staff account added.")
            win.destroy()
            refresh_treeview(tree, staff_id_map)
        except mysql.connector.IntegrityError:
            show_field_error(entries["username"], "Username already exists.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            conn.close()

    btn_frame = tk.Frame(win, bg="#f5f6fa", pady=10)
    btn_frame.pack(fill="x", padx=30)
    tk.Button(btn_frame, text="Save Staff", bg="#2c3e50", fg="white", font=("Segoe UI", 11, "bold"),
              relief="flat", cursor="hand2", padx=30, pady=8, command=save_staff).pack(fill="x")

def main():
    win = tk.Tk()
    win.title("Admin - Account Management")
    win.geometry("1280x720")
    win.configure(bg="#f5f6fa")

    add_sidebar(win)

    content_frame = tk.Frame(win, bg="#f5f6fa")
    content_frame.pack(side="right", fill="both", expand=True)

    top_bar = tk.Frame(content_frame, bg="#f5f6fa")
    top_bar.pack(fill="x", padx=25, pady=(20, 0))

    tk.Label(top_bar, text="Account Management", font=("Segoe UI", 22, "bold"),
             fg="#d35400", bg="#f5f6fa").pack(side="left")

    tk.Button(top_bar, text="+ Add Staff Account", bg="#2c3e50", fg="white",
              font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
              padx=16, pady=7, command=lambda: add_staff(tree, staff_id_map)).pack(side="right")

    tk.Frame(content_frame, bg="#ddd", height=1).pack(fill="x", padx=25, pady=12)

    tree_outer = tk.Frame(content_frame, bg="#f5f6fa")
    tree_outer.pack(fill="both", expand=True, padx=25, pady=(0, 20))

    style = ttk.Style()
    style.configure("Treeview", background="white", foreground="#2c3e50",
                    rowheight=32, fieldbackground="white", font=("Segoe UI", 10))
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                    foreground="#d35400", background="#fdf0e8")
    style.map("Treeview", background=[("selected", "#d35400")], foreground=[("selected", "white")])

    scroll_y = ttk.Scrollbar(tree_outer, orient="vertical")
    scroll_x = ttk.Scrollbar(tree_outer, orient="horizontal")

    columns = ("Fullname", "Address", "Contact", "Age", "Username", "Actions")
    tree = ttk.Treeview(tree_outer, columns=columns, show="headings", height=20,
                        yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

    scroll_y.config(command=tree.yview)
    scroll_x.config(command=tree.xview)
    scroll_y.pack(side="right", fill="y")
    scroll_x.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)

    col_widths = {"Fullname": 180, "Address": 180, "Contact": 130, "Age": 60, "Username": 130, "Actions": 120}
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=col_widths[col], anchor="center")

    staff_id_map = {}
    refresh_treeview(tree, staff_id_map)

    def on_click(event):
        if tree.identify_region(event.x, event.y) != "cell":
            return
        if tree.identify_column(event.x) != "#6":
            return
        item_id = tree.identify_row(event.y)
        if not item_id:
            return
        bbox = tree.bbox(item_id, "#6")
        if not bbox:
            return
        if (event.x - bbox[0]) < 60:
            edit_staff_item(item_id, tree, staff_id_map)
        else:
            delete_staff_item(item_id, tree, staff_id_map)

    tree.bind("<ButtonRelease-1>", on_click)
    win.mainloop()

if __name__ == "__main__":
    main()