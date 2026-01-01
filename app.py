import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import tempfile
import os

# ================= DATABASE =================
conn = sqlite3.connect("hospital.db")
cur = conn.cursor()

# Users table
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Default users
default_users = [
    ("admin","admin123"),
    ("hamza","hamza123"),
    ("muzamil","muzamil123")
]

for uname, pwd in default_users:
    cur.execute("SELECT * FROM users WHERE username=?", (uname,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(username,password) VALUES(?,?)", (uname, pwd))
conn.commit()

# Patients and tests tables
cur.execute("""
CREATE TABLE IF NOT EXISTS patients(
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    cnic TEXT UNIQUE NOT NULL
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS tests(
    test_id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_name TEXT NOT NULL,
    test_result TEXT,
    test_date TEXT,
    department TEXT,
    patient_id INTEGER,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
)
""")
conn.commit()

# ================= DASHBOARD FUNCTION =================
def dashboard(user_role="user"):
    global tree, entry_patient, entry_cnic, entry_test, entry_result, entry_date, entry_dept, entries, selected_test_id, search_entry
    dash = tk.Tk()
    dash.title("Hospital Management Dashboard")
    dash.geometry("1450x750")
    dash.configure(bg="#f5f6fa")
    selected_test_id = None

    # -------- Live clock --------
    def live_clock():
        clock_lbl.config(text=datetime.now().strftime("%d %b %Y | %H:%M:%S"))
        clock_lbl.after(1000, live_clock)

    # -------- Table refresh --------
    def refresh(dept=None, search=None):
        tree.delete(*tree.get_children())
        query = """
        SELECT t.test_id, p.patient_name, p.cnic,
               t.test_name, t.test_result,
               t.test_date, t.department
        FROM tests t
        JOIN patients p ON t.patient_id=p.patient_id
        """
        params = []
        if dept:
            query += " WHERE t.department=?"
            params.append(dept)
        if search:
            query += " AND (p.patient_name LIKE ? OR t.test_name LIKE ?)" if dept else " WHERE (p.patient_name LIKE ? OR t.test_name LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        cur.execute(query, tuple(params))
        for row in cur.fetchall():
            tree.insert("", tk.END, values=row)

    # -------- Clear form --------
    def clear_form():
        global selected_test_id
        selected_test_id = None
        for e in entries:
            e.delete(0, tk.END)
        entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

    # -------- Add Test --------
    def add_test():
        if not entry_patient.get() or not entry_cnic.get() or not entry_test.get():
            messagebox.showerror("Error","Patient Name, CNIC & Test Name required")
            return
        if len(entry_cnic.get()) != 13 or not entry_cnic.get().isdigit():
            messagebox.showerror("Error","CNIC must be 13 digits")
            return
        cur.execute("SELECT patient_id FROM patients WHERE cnic=?", (entry_cnic.get(),))
        row = cur.fetchone()
        if row:
            pid = row[0]
            cur.execute("UPDATE patients SET patient_name=? WHERE patient_id=?", (entry_patient.get(), pid))
        else:
            cur.execute("INSERT INTO patients(patient_name,cnic) VALUES(?,?)", (entry_patient.get(), entry_cnic.get()))
            pid = cur.lastrowid
        cur.execute("INSERT INTO tests(test_name,test_result,test_date,department,patient_id) VALUES(?,?,?,?,?)",
                    (entry_test.get(), entry_result.get(), entry_date.get(), entry_dept.get(), pid))
        conn.commit()
        refresh()
        clear_form()
        messagebox.showinfo("Success","Record Added Successfully")

    # -------- Update Test --------
    def update_test():
        global selected_test_id
        if not selected_test_id:
            messagebox.showerror("Error","Select a record to update")
            return
        try:
            cur.execute("""UPDATE tests SET test_name=?, test_result=?, test_date=?, department=? WHERE test_id=?""",
                        (entry_test.get(), entry_result.get(), entry_date.get(), entry_dept.get(), selected_test_id))
            cur.execute("""UPDATE patients SET patient_name=?, cnic=? WHERE patient_id=(SELECT patient_id FROM tests WHERE test_id=?)""",
                        (entry_patient.get(), entry_cnic.get(), selected_test_id))
            conn.commit()
            refresh()
            clear_form()
            messagebox.showinfo("Updated","Record Updated Successfully")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error","CNIC already exists!")

    # -------- Delete Test --------
    def delete_test():
        global selected_test_id
        if not selected_test_id:
            messagebox.showerror("Error","Select a record to delete")
            return
        if messagebox.askyesno("Confirm","Are you sure you want to delete this record?"):
            cur.execute("DELETE FROM tests WHERE test_id=?", (selected_test_id,))
            conn.commit()
            cur.execute("DELETE FROM patients WHERE patient_id NOT IN (SELECT patient_id FROM tests)")
            conn.commit()
            refresh()
            clear_form()
            messagebox.showinfo("Deleted","Record Deleted Successfully")

    # -------- Select row --------
    def select_row(e):
        global selected_test_id
        row = tree.item(tree.focus())["values"]
        if not row:
            return
        clear_form()
        selected_test_id = row[0]
        entry_patient.insert(0,row[1])
        entry_cnic.insert(0,row[2])
        entry_test.insert(0,row[3])
        entry_result.insert(0,row[4])
        entry_date.delete(0, tk.END)
        entry_date.insert(0,row[5])
        entry_dept.set(row[6])

    # -------- Print Table --------
    def print_table():
        if not tree.get_children():
            messagebox.showerror("Error","No records to print")
            return
        temp_file = tempfile.mktemp(".txt")
        with open(temp_file, "w") as f:
            for child in tree.get_children():
                f.write(str(tree.item(child)["values"]) + "\n")
        os.startfile(temp_file, "print")
        messagebox.showinfo("Print", "Print command sent successfully")

    # ================= ADMIN PANEL =================
    def open_admin_panel():
        admin_win = tk.Toplevel(dash)
        admin_win.title("Admin Panel - User Management")
        admin_win.geometry("500x400")
        admin_win.configure(bg="#ecf0f3")

        tk.Label(admin_win, text="User Management", font=("Segoe UI",16,"bold"), bg="#ecf0f3").pack(pady=10)

        # Treeview
        cols = ("ID","Username","Password")
        user_tree = ttk.Treeview(admin_win, columns=cols, show="headings")
        for c in cols:
            user_tree.heading(c, text=c)
            user_tree.column(c, width=130)
        user_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Load users
        def load_users():
            user_tree.delete(*user_tree.get_children())
            cur.execute("SELECT * FROM users")
            for row in cur.fetchall():
                user_tree.insert("", tk.END, values=row)
        load_users()

        # Entry fields
        frame = tk.Frame(admin_win, bg="#ecf0f3")
        frame.pack(pady=5)
        tk.Label(frame, text="Username:", bg="#ecf0f3").grid(row=0,column=0,padx=5,pady=5)
        tk.Label(frame, text="Password:", bg="#ecf0f3").grid(row=1,column=0,padx=5,pady=5)
        entry_u = tk.Entry(frame)
        entry_p = tk.Entry(frame, show="*")
        entry_u.grid(row=0,column=1,padx=5,pady=5)
        entry_p.grid(row=1,column=1,padx=5,pady=5)

        # Buttons
        def add_user():
            u = entry_u.get().strip()
            p = entry_p.get().strip()
            if not u or not p:
                messagebox.showerror("Error","Username & Password required")
                return
            try:
                cur.execute("INSERT INTO users(username,password) VALUES(?,?)",(u,p))
                conn.commit()
                load_users()
                entry_u.delete(0,tk.END)
                entry_p.delete(0,tk.END)
                messagebox.showinfo("Success","User Added Successfully")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error","Username already exists!")

        def delete_user():
            selected = user_tree.item(user_tree.focus())["values"]
            if not selected:
                messagebox.showerror("Error","Select a user to delete")
                return
            if selected[1] in ["admin","hamza","muzamil"]:
                messagebox.showerror("Error","Cannot delete default users")
                return
            if messagebox.askyesno("Confirm","Are you sure you want to delete this user?"):
                cur.execute("DELETE FROM users WHERE user_id=?",(selected[0],))
                conn.commit()
                load_users()
                messagebox.showinfo("Deleted","User Deleted Successfully")

        tk.Button(admin_win, text="Add User", bg="#27ae60", fg="white", width=15, command=add_user).pack(side=tk.LEFT, padx=20, pady=10)
        tk.Button(admin_win, text="Delete User", bg="#c0392b", fg="white", width=15, command=delete_user).pack(side=tk.RIGHT, padx=20, pady=10)

    # ================= HEADER =================
    header = tk.Frame(dash,bg="#2c3e50",height=70)
    header.pack(fill=tk.X)
    tk.Label(header,text="🏥 Hospital Dashboard",bg="#2c3e50",fg="white",font=("Segoe UI",22,"bold")).pack(side=tk.LEFT,padx=20)
    clock_lbl = tk.Label(header,bg="#2c3e50",fg="white",font=("Segoe UI",12))
    clock_lbl.pack(side=tk.RIGHT,padx=20)
    live_clock()

    # ================= SIDEBAR =================
    sidebar = tk.Frame(dash,bg="#34495e",width=220)
    sidebar.pack(side=tk.LEFT,fill=tk.Y)
    tk.Label(sidebar,text="DEPARTMENTS",bg="#34495e",fg="white",font=("Segoe UI",14,"bold")).pack(pady=15)
    departments = ["Cardiology","Neurology","Orthopedics","Pediatrics","Gynecology","Radiology","Pathology","Emergency"]
    for d in departments:
        btn = tk.Button(sidebar,text=d,bg="#34495e",fg="white",font=("Segoe UI",11,"bold"),relief="flat",
                  activebackground="#16a085",activeforeground="white",command=lambda x=d: refresh(x))
        btn.pack(fill=tk.X,pady=3)
    tk.Button(sidebar,text="Show All",bg="#1abc9c",fg="white",font=("Segoe UI",11,"bold"),command=lambda: refresh()).pack(fill=tk.X,pady=20)

    if user_role=="admin":
        tk.Button(sidebar,text="Admin Panel",bg="#9b59b6",fg="white",font=("Segoe UI",11,"bold"),command=open_admin_panel).pack(fill=tk.X,pady=10)
        tk.Button(sidebar,text="Print Records",bg="#f39c12",fg="white",font=("Segoe UI",11,"bold"),command=print_table).pack(fill=tk.X,pady=10)

    # ================= FORM =================
    form = tk.LabelFrame(dash,text="Patient Test Entry",bg="white",font=("Segoe UI",12,"bold"))
    form.place(x=240,y=100,width=420,height=480)
    labels = ["Patient Name","CNIC","Test Name","Result","Date","Department"]
    for i,l in enumerate(labels):
        tk.Label(form,text=l,bg="white",anchor="w").grid(row=i,column=0,padx=10,pady=8)
    entry_patient = tk.Entry(form, font=("Segoe UI",11))
    entry_cnic = tk.Entry(form, font=("Segoe UI",11))
    entry_test = tk.Entry(form, font=("Segoe UI",11))
    entry_result = tk.Entry(form, font=("Segoe UI",11))
    entry_date = tk.Entry(form, font=("Segoe UI",11))
    entry_dept = ttk.Combobox(form, values=departments, state="readonly", font=("Segoe UI",11))
    entries = [entry_patient,entry_cnic,entry_test,entry_result,entry_date,entry_dept]
    for i,e in enumerate(entries):
        e.grid(row=i,column=1,padx=10,pady=8)
    entry_date.insert(0,datetime.now().strftime("%Y-%m-%d"))

    tk.Button(form,text="ADD",bg="#2980b9",fg="white",font=("Segoe UI",11,"bold"),width=12,command=add_test).grid(row=7,column=0,pady=12)
    tk.Button(form,text="UPDATE",bg="#27ae60",fg="white",font=("Segoe UI",11,"bold"),width=12,command=update_test).grid(row=7,column=1,pady=12)
    tk.Button(form,text="DELETE",bg="#c0392b",fg="white",font=("Segoe UI",11,"bold"),width=12,command=delete_test).grid(row=8,column=0,columnspan=2,pady=6)
    tk.Label(form,text="Search Patient/Test:",bg="white").grid(row=9,column=0,padx=10,pady=6)
    search_entry = tk.Entry(form, font=("Segoe UI",11))
    search_entry.grid(row=9,column=1,pady=6)
    tk.Button(form,text="Search",bg="#8e44ad",fg="white",font=("Segoe UI",11,"bold"),width=12,command=lambda: refresh(search=search_entry.get())).grid(row=10,column=0,columnspan=2,pady=6)
    tk.Button(form,text="Clear",bg="#7f8c8d",fg="white",font=("Segoe UI",11,"bold"),width=12,command=lambda:[refresh(),clear_form(),search_entry.delete(0,tk.END)]).grid(row=11,column=0,columnspan=2,pady=6)

    # ================= TABLE =================
    cols = ("ID","Patient","CNIC","Test","Result","Date","Department")
    tree = ttk.Treeview(dash,columns=cols,show="headings")
    style = ttk.Style(dash)
    style.theme_use("clam")
    style.configure("Treeview.Heading", font=("Segoe UI",11,"bold"), foreground="#2c3e50")
    style.configure("Treeview", font=("Segoe UI",10), rowheight=28, background="white", fieldbackground="white")
    style.map('Treeview', background=[('selected', '#16a085')], foreground=[('selected', 'white')])
    for c in cols:
        tree.heading(c,text=c)
        tree.column(c,width=130)
    tree.place(x=680,y=100,width=730,height=580)
    tree.bind("<ButtonRelease-1>",select_row)

    refresh()
    dash.mainloop()

# ================= LOGIN WINDOW =================
def login_user():
    uname = entry_user.get().strip()
    pwd = entry_pass.get().strip()
    if uname == "" or pwd == "":
        messagebox.showerror("Error", "Please enter username & password")
        return
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (uname, pwd))
    row = cur.fetchone()
    if row:
        user_role = "admin" if uname=="admin" else "user"
        login_win.destroy()
        dashboard(user_role=user_role)
    else:
        messagebox.showerror("Login Failed", "Invalid Username or Password")

def toggle_password():
    if entry_pass.cget("show") == "":
        entry_pass.config(show="*")
        show_btn.config(text="Show")
    else:
        entry_pass.config(show="")
        show_btn.config(text="Hide")

# ================= LOGIN WINDOW =================
login_win = tk.Tk()
login_win.title("Hospital Management System")
login_win.geometry("450x480")
login_win.resizable(False, False)
login_win.configure(bg="#ecf0f3")

card = tk.Frame(login_win, bg="white", bd=0, relief="raised")
card.place(relx=0.5, rely=0.5, anchor="center", width=380, height=400)

tk.Label(card, text="🏥 Hospital Login", font=("Segoe UI", 20, "bold"), bg="white", fg="#2c3e50").pack(pady=20)
tk.Label(card, text="Sign in to your account", font=("Segoe UI", 11), bg="white", fg="gray").pack(pady=5)

tk.Label(card, text="Username", bg="white", anchor="w").pack(fill="x", padx=30, pady=(15, 5))
entry_user = tk.Entry(card, font=("Segoe UI", 11), relief="solid")
entry_user.pack(fill="x", padx=30, ipady=6)

tk.Label(card, text="Password", bg="white", anchor="w").pack(fill="x", padx=30, pady=(15, 5))
pass_frame = tk.Frame(card, bg="white")
pass_frame.pack(fill="x", padx=30)
entry_pass = tk.Entry(pass_frame, font=("Segoe UI", 11), show="*", relief="solid")
entry_pass.pack(side="left", fill="x", expand=True, ipady=6)
show_btn = tk.Button(pass_frame, text="Show", command=toggle_password, bg="white", relief="flat", fg="#2980b9")
show_btn.pack(side="right", padx=5)

tk.Button(card, text="LOGIN", font=("Segoe UI", 12, "bold"), bg="#2980b9", fg="white", relief="flat", command=login_user).pack(fill="x", padx=30, pady=25)

login_win.bind("<Return
