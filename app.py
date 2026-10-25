import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2

# --- ตั้งค่าการเชื่อมต่อฐานข้อมูล ---
DB_CONFIG = {
    "host": "localhost",
    "database": "my_database",
    "user": "postgres",
    "password": "20082007",
    "port": "5432"
}

def get_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        messagebox.showerror("Error", f"ไม่สามารถเชื่อมต่อฐานข้อมูลได้:\n{e}")
        return None

# --- หน้าจอ Admin (ดูและจัดการการจอง) ---
def open_admin_dashboard():
    window = tk.Toplevel(root)
    window.title("Admin Dashboard - จัดการการจอง")
    window.geometry("700x450")

    columns = ("id", "user", "location", "date", "start", "end", "status")
    tree = ttk.Treeview(window, columns=columns, show="headings", selectmode="browse")
    for col in columns:
        tree.heading(col, text=col.title())
        tree.column(col, width=90)
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def refresh_data():
        for item in tree.get_children():
            tree.delete(item)
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.id, u.username, l.name, b.booking_date, b.start_time, b.end_time, b.status
                FROM bookings b
                JOIN users u ON b.user_id = u.id
                JOIN locations l ON b.location_id = l.id
                ORDER BY b.id DESC
            """)
            for row in cursor.fetchall():
                tree.insert("", tk.END, values=row)
            conn.close()

    def change_status(new_status):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "กรุณาเลือกรายการที่ต้องการจัดการ")
            return
        
        booking_id = tree.item(selected_item[0])['values'][0]
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE bookings SET status = %s WHERE id = %s", (new_status, booking_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"เปลี่ยนสถานะเป็น {new_status} สำเร็จ")
            refresh_data()

    btn_frame = tk.Frame(window)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="อนุมัติ (Approve)", command=lambda: change_status('approved'), bg="green", fg="white").pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="ปฏิเสธ (Reject)", command=lambda: change_status('rejected'), bg="red", fg="white").pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="รีเฟรชข้อมูล", command=refresh_data).pack(side=tk.LEFT, padx=10)

    refresh_data()

# --- หน้าจอ User (ทำการจอง) ---
def open_user_dashboard(user_id):
    window = tk.Toplevel(root)
    window.title("User Dashboard - จองสถานที่")
    window.geometry("400x350")

    tk.Label(window, text="เลือกสถานที่ (ID):").pack(pady=5)
    loc_entry = tk.Entry(window)
    loc_entry.pack()
    tk.Label(window, text="(1 = Meeting Room A, 2 = Co-working Space B)").pack()

    tk.Label(window, text="วันที่ (YYYY-MM-DD):").pack(pady=5)
    date_entry = tk.Entry(window)
    date_entry.insert(0, "2024-10-30")
    date_entry.pack()

    tk.Label(window, text="เวลาเริ่ม (HH:MM):").pack(pady=5)
    start_entry = tk.Entry(window)
    start_entry.insert(0, "10:00")
    start_entry.pack()

    tk.Label(window, text="เวลาสิ้นสุด (HH:MM):").pack(pady=5)
    end_entry = tk.Entry(window)
    end_entry.insert(0, "12:00")
    end_entry.pack()

    def submit_booking():
        conn = get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO bookings (user_id, location_id, booking_date, start_time, end_time, status) VALUES (%s, %s, %s, %s, %s, 'pending')",
                (user_id, loc_entry.get(), date_entry.get(), start_entry.get(), end_entry.get())
            )
            conn.commit()
            messagebox.showinfo("Success", "ส่งคำขอจองสำเร็จ รอแอดมินอนุมัติ!")
            window.destroy()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"เกิดข้อผิดพลาด:\n{e}")
        finally:
            conn.close()

    tk.Button(window, text="ยืนยันการจอง", command=submit_booking, bg="blue", fg="white").pack(pady=20)

# --- ระบบสมัครสมาชิก (Register) ---
def open_register_window():
    reg_window = tk.Toplevel(root)
    reg_window.title("สมัครสมาชิกใหม่")
    reg_window.geometry("300x300")

    tk.Label(reg_window, text="สร้างบัญชีผู้ใช้ใหม่", font=("Arial", 14, "bold")).pack(pady=15)

    tk.Label(reg_window, text="Username:").pack()
    reg_user = tk.Entry(reg_window)
    reg_user.pack()

    tk.Label(reg_window, text="Password:").pack()
    reg_pass = tk.Entry(reg_window, show="*")
    reg_pass.pack()

    tk.Label(reg_window, text="Confirm Password:").pack()
    reg_pass_confirm = tk.Entry(reg_window, show="*")
    reg_pass_confirm.pack()

    def submit_register():
        username = reg_user.get().strip()
        password = reg_pass.get()
        confirm_password = reg_pass_confirm.get()

        if not username or not password:
            messagebox.showwarning("Warning", "กรุณากรอกข้อมูลให้ครบถ้วน", parent=reg_window)
            return
        if password != confirm_password:
            messagebox.showwarning("Warning", "รหัสผ่านไม่ตรงกัน", parent=reg_window)
            return

        conn = get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # สมัครใหม่จะได้สิทธิ์เป็น user ธรรมดา
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'user')", (username, password))
            conn.commit()
            messagebox.showinfo("Success", "สมัครสมาชิกสำเร็จ! กรุณาล็อกอิน", parent=reg_window)
            reg_window.destroy()
        except psycopg2.IntegrityError:
            conn.rollback()
            messagebox.showerror("Error", "ชื่อผู้ใช้นี้มีในระบบแล้ว กรุณาใช้ชื่ออื่น", parent=reg_window)
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", f"เกิดข้อผิดพลาด:\n{e}", parent=reg_window)
        finally:
            conn.close()

    tk.Button(reg_window, text="ยืนยันการสมัคร", command=submit_register, bg="green", fg="white").pack(pady=20)

# --- ระบบ Login ---
def login():
    username = entry_user.get()
    password = entry_pass.get()
    
    conn = get_connection()
    if not conn: return
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, role FROM users WHERE username=%s AND password_hash=%s", (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        user_id, role = user
        if role == 'admin':
            open_admin_dashboard()
        else:
            open_user_dashboard(user_id)
    else:
        messagebox.showerror("Error", "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

# --- หน้าต่างหลัก (Login UI) ---
root = tk.Tk()
root.title("ระบบจองสถานที่ (Desktop App)")
root.geometry("300x300")

tk.Label(root, text="เข้าสู่ระบบ", font=("Arial", 16, "bold")).pack(pady=20)

tk.Label(root, text="Username:").pack()
entry_user = tk.Entry(root)
entry_user.pack()
entry_user.insert(0, "admin_guy")

tk.Label(root, text="Password:").pack()
entry_pass = tk.Entry(root, show="*")
entry_pass.pack()
entry_pass.insert(0, "hashed_pass_123")

tk.Button(root, text="Login", command=login, bg="blue", fg="white", width=15).pack(pady=10)
tk.Button(root, text="สมัครสมาชิก", command=open_register_window, width=15).pack(pady=5)

root.mainloop()