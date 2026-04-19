import tkinter as tk
from sidebar import add_sidebar

def main():
    win = tk.Tk()
    win.title("Admin - Reports")
    win.geometry("1280x720")
    win.configure(bg="#f0f0f0")
    
    add_sidebar(win)
    
    content_frame = tk.Frame(win, bg="#f0f0f0")
    content_frame.pack(side="right", fill="both", expand=True)
    
    tk.Label(content_frame, text="REPORTS", font=("Segoe UI", 24, "bold"), bg="#f0f0f0", fg="#d35400").pack(pady=100)
    
    win.mainloop()

if __name__ == "__main__":
    main()