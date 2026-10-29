import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import calendar
import psycopg2

# ==========================================
# 1. การตั้งค่าและเชื่อมต่อฐานข้อมูล (Database)
# ==========================================
DB_CONFIG = {
    "host": "localhost",
    "database": "my_database",
    "user": "postgres",
    "password": "20082007",
    "port": "5432"
}

def get_connection():
    """เชื่อมต่อกับฐานข้อมูล PostgreSQL"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        messagebox.showerror("Database Error", f"ไม่สามารถเชื่อมต่อฐานข้อมูลได้:\n{e}")
        return None

def init_db():
    """สร้างตารางและคอลัมน์ที่จำเป็นหากยังไม่มี พร้อมเพิ่มข้อมูลห้องเริ่มต้น"""
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        # 1. ตาราง users
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user'))
            );
        """)

        # 2. ตาราง locations
        cur.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                capacity INTEGER DEFAULT 10,
                description TEXT
            );
        """)

        # ตรวจสอบคอลัมน์ capacity ใน locations
        cur.execute("ALTER TABLE locations ADD COLUMN IF NOT EXISTS capacity INTEGER DEFAULT 10;")

        # 3. ตาราง bookings
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                location_id INTEGER REFERENCES locations(id) ON DELETE CASCADE,
                booking_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                department VARCHAR(255),
                people INTEGER,
                topic VARCHAR(255)
            );
        """)

        # ตรวจสอบคอลัมน์เพิ่มเติมใน bookings
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS department VARCHAR(255);")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS people INTEGER;")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS topic VARCHAR(255);")

        # 4. ตาราง equipment_bookings
        cur.execute("""
            CREATE TABLE IF NOT EXISTS equipment_bookings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                equipment_name VARCHAR(100) NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                booking_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                department VARCHAR(255),
                purpose TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # เพิ่มห้องประชุมเริ่มต้นหากยังไม่มี
        default_rooms = [
            ("ห้องประชุม A", 8, "ชั้น 2 - เหมาะสำหรับการประชุมกลุ่มย่อย"),
            ("ห้องประชุม B", 16, "ชั้น 3 - เหมาะสำหรับการประชุมทีม"),
            ("ห้องประชุมใหญ่", 30, "ชั้น 4 - รองรับการประชุมคณะหรือสัมมนาขนาดกลาง"),
            ("ห้องสัมมนา", 50, "ชั้น 5 - รองรับการอบรมสัมมนาขนาดใหญ่")
        ]
        for name, cap, desc in default_rooms:
            cur.execute("SELECT id FROM locations WHERE name = %s;", (name,))
            if not cur.fetchone():
                cur.execute("INSERT INTO locations (name, capacity, description) VALUES (%s, %s, %s);", (name, cap, desc))

        # ตรวจสอบว่ามีผู้ใช้ admin หรือไม่ ถ้ายังไม่มีให้สร้าง admin_guy เป็นตัวอย่าง
        cur.execute("SELECT id FROM users WHERE username = 'admin';")
        if not cur.fetchone():
            cur.execute("INSERT INTO users (username, password_hash, role) VALUES ('admin', '24042564', 'admin');")

        conn.commit()
        cur.close()
    except Exception as e:
        conn.rollback()
        print(f"init_db error: {e}")
    finally:
        conn.close()


# ==========================================
# 2. ธีมและสีของระบบ (Design Aesthetics)
# ==========================================
BG = "#F4F7FB"
NAVY = "#172554"
NAVY_HOVER = "#1E3A8A"
GREEN = "#16A34A"
GREEN_HOVER = "#15803D"
WHITE = "#FFFFFF"
TEXT = "#1F2937"
TEXT_MUTED = "#64748B"
RED = "#DC2626"
BLUE = "#2563EB"
AMBER = "#D97706"
BORDER = "#E2E8F0"


# ==========================================
# 3. หน้าต่างเข้าสู่ระบบและสมัครสมาชิก
# ==========================================
class LoginWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.root.title("KB Booking - เข้าสู่ระบบ")
        self.root.geometry("450x550")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # จัดกึ่งกลางหน้าจอ
        self.center_window(450, 550)

        # Card container
        card = tk.Frame(self.root, bg=WHITE, padx=35, pady=30, highlightbackground=BORDER, highlightthickness=1)
        card.pack(expand=True, fill="both", padx=30, pady=30)

        # Header
        tk.Label(card, text="KB Booking", font=("Arial", 24, "bold"), bg=WHITE, fg=NAVY).pack(pady=(5, 2))
        tk.Label(card, text="ระบบจองห้องประชุมอัจฉริยะ", font=("Arial", 11), bg=WHITE, fg=TEXT_MUTED).pack(pady=(0, 20))

        tk.Label(card, text="เข้าสู่ระบบ", font=("Arial", 16, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(5, 12))

        # Username
        tk.Label(card, text="ชื่อผู้ใช้งาน (Username)", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(5, 3))
        self.entry_user = tk.Entry(card, font=("Arial", 11), bg="#F8FAFC", relief="solid", bd=1)
        self.entry_user.pack(fill="x", ipady=6, pady=(0, 10))
        self.entry_user.insert(0, "Username")

        # Password
        tk.Label(card, text="รหัสผ่าน (Password)", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(5, 3))
        self.entry_pass = tk.Entry(card, font=("Arial", 11), show="•", bg="#F8FAFC", relief="solid", bd=1)
        self.entry_pass.pack(fill="x", ipady=6, pady=(0, 20))
        self.entry_pass.insert(0, "Password")
        self.entry_pass.bind("<Return>", lambda e: self.do_login())

        # Login button
        btn_login = tk.Button(
            card, text="เข้าสู่ระบบ (Login)", command=self.do_login,
            font=("Arial", 12, "bold"), bg=BLUE, fg=WHITE, activebackground="#1D4ED8", activeforeground=WHITE,
            relief="flat", cursor="hand2"
        )
        btn_login.pack(fill="x", ipady=8, pady=(5, 10))

        # Register button
        btn_reg = tk.Button(
            card, text="สมัครสมาชิกใหม่", command=self.open_register,
            font=("Arial", 11), bg=WHITE, fg=BLUE, activebackground="#F1F5F9",
            relief="solid", bd=1, cursor="hand2"
        )
        btn_reg.pack(fill="x", ipady=6, pady=(0, 10))

        # Test hints
        hint_frame = tk.Frame(card, bg="#F1F5F9", padx=10, pady=8)
        hint_frame.pack(fill="x", pady=(10, 0))
        tk.Label(hint_frame, text="💡 บัญชีทดสอบในระบบ:", font=("Arial", 9, "bold"), bg="#F1F5F9", fg=TEXT).pack(anchor="w")
        tk.Label(hint_frame, text="• แอดมิน: admin / 24042564", font=("Arial", 8), bg="#F1F5F9", fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(hint_frame, text="• ผู้ใช้ทั่วไป: user_jane / hashed_pass_456 (หรือสมัครใหม่)", font=("Arial", 8), bg="#F1F5F9", fg=TEXT_MUTED).pack(anchor="w")

    def center_window(self, width, height):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def do_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get()

        if not username or not password:
            messagebox.showwarning("คำเตือน", "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน", parent=self.root)
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute("SELECT id, username, role FROM users WHERE username = %s AND password_hash = %s", (username, password))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                user_id, uname, role = user
                self.root.destroy()
                self.on_login_success(user_id, uname, role)
            else:
                messagebox.showerror("เข้าสู่ระบบไม่สำเร็จ", "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", parent=self.root)
        except Exception as e:
            messagebox.showerror("Database Error", f"เกิดข้อผิดพลาด:\n{e}", parent=self.root)

    def open_register(self):
        reg = tk.Toplevel(self.root)
        reg.title("สมัครสมาชิกใหม่ - KB Booking")
        reg.geometry("400x480")
        reg.resizable(False, False)
        reg.configure(bg=BG)
        reg.grab_set()

        card = tk.Frame(reg, bg=WHITE, padx=30, pady=25, highlightbackground=BORDER, highlightthickness=1)
        card.pack(expand=True, fill="both", padx=25, pady=25)

        tk.Label(card, text="สร้างบัญชีผู้ใช้ใหม่", font=("Arial", 16, "bold"), bg=WHITE, fg=NAVY).pack(pady=(0, 15))

        tk.Label(card, text="ชื่อผู้ใช้งาน (Username):", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(5, 3))
        reg_user = tk.Entry(card, font=("Arial", 11), bg="#F8FAFC", relief="solid", bd=1)
        reg_user.pack(fill="x", ipady=5, pady=(0, 10))

        tk.Label(card, text="รหัสผ่าน (Password):", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(5, 3))
        reg_pass = tk.Entry(card, font=("Arial", 11), show="•", bg="#F8FAFC", relief="solid", bd=1)
        reg_pass.pack(fill="x", ipady=5, pady=(0, 10))

        tk.Label(card, text="ยืนยันรหัสผ่าน (Confirm Password):", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(5, 3))
        reg_pass_confirm = tk.Entry(card, font=("Arial", 11), show="•", bg="#F8FAFC", relief="solid", bd=1)
        reg_pass_confirm.pack(fill="x", ipady=5, pady=(0, 20))

        def submit():
            u = reg_user.get().strip()
            p = reg_pass.get()
            pc = reg_pass_confirm.get()

            if not u or not p:
                messagebox.showwarning("คำเตือน", "กรุณากรอกข้อมูลให้ครบถ้วน", parent=reg)
                return
            if p != pc:
                messagebox.showwarning("คำเตือน", "รหัสผ่านทั้งสองช่องไม่ตรงกัน", parent=reg)
                return

            conn = get_connection()
            if not conn:
                return

            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'user')", (u, p))
                conn.commit()
                cur.close()
                conn.close()
                messagebox.showinfo("สำเร็จ", "สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบด้วยบัญชีใหม่", parent=reg)
                reg.destroy()
                self.entry_user.delete(0, tk.END)
                self.entry_user.insert(0, u)
                self.entry_pass.delete(0, tk.END)
                self.entry_pass.focus()
            except psycopg2.IntegrityError:
                conn.rollback()
                messagebox.showerror("ผิดพลาด", "ชื่อผู้ใช้นี้มีในระบบแล้ว กรุณาใช้ชื่ออื่น", parent=reg)
            except Exception as e:
                conn.rollback()
                messagebox.showerror("ผิดพลาด", f"เกิดข้อผิดพลาด:\n{e}", parent=reg)

        btn_submit = tk.Button(
            card, text="ยืนยันการสมัครสมาชิก", command=submit,
            font=("Arial", 11, "bold"), bg=GREEN, fg=WHITE,
            activebackground=GREEN_HOVER, relief="flat", cursor="hand2"
        )
        btn_submit.pack(fill="x", ipady=7, pady=(10, 0))


# ==========================================
# 4. แอปพลิเคชันหลัก KB Booking (MeetingRoomApp)
# ==========================================
class MeetingRoomApp:
    def __init__(self, root, current_user):
        self.root = root
        self.current_user = current_user  # {"id": int, "username": str, "role": str}
        self.root.title(f"KB Booking - ระบบจองห้องประชุม ({self.current_user['username']})")
        self.root.geometry("1240x820")
        self.root.minsize(980, 700)
        self.root.configure(bg=BG)

        # ข้อมูลการจองจากฐานข้อมูล
        self.bookings = []
        self.rooms_data = {}  # {room_name: {"id": id, "capacity": cap, "description": desc}}

        # รายการจองอุปกรณ์และคลังอุปกรณ์ (Stock)
        self.equipment_bookings = []
        self.equipment_stock = {
            "โปรเจกเตอร์": 5,
            "ไมโครโฟน": 10,
            "ลำโพง": 4,
            "โน้ตบุ๊ก": 8,
            "สาย HDMI": 10,
            "ปลั๊กพ่วง": 10
        }

        # ตัวแปรแบบฟอร์มการจอง
        self.department = tk.StringVar()
        self.room = tk.StringVar()
        self.people = tk.StringVar(value="1")
        self.topic = tk.StringVar()
        self.selected_date = tk.StringVar(value=date.today().isoformat())
        self.start_time = tk.StringVar(value="09:00")
        self.end_time = tk.StringVar()

        # รายชื่อคณะและหน่วยงาน (สจล.)
        self.departments = [
            "คณะวิศวกรรมศาสตร์",
            "คณะสถาปัตยกรรม ศิลปะและการออกแบบ",
            "คณะครุศาสตร์อุตสาหกรรมและเทคโนโลยี",
            "คณะเทคโนโลยีการเกษตร",
            "คณะวิทยาศาสตร์",
            "คณะอุตสาหกรรมอาหาร",
            "คณะเทคโนโลยีสารสนเทศ",
            "คณะบริหารธุรกิจ",
            "คณะศิลปศาสตร์",
            "คณะแพทยศาสตร์",
            "คณะทันตแพทยศาสตร์",
            "คณะพยาบาลศาสตร์",
            "คณะเทคโนโลยีนวัตกรรมบูรณาการ",
            "วิทยาลัยการจัดการนวัตกรรมและอุตสาหกรรม",
            "วิทยาลัยอุตสาหกรรมการบินนานาชาติ",
            "วิทยาลัยวิศวกรรมสังคีต",
            "สถาบันโคเซ็นแห่ง สจล.",
            "สำนักงานอธิการบดี",
            "สำนักบริการคอมพิวเตอร์",
            "สำนักทะเบียนและประมวลผล",
            "หน่วยงานอื่น ๆ"
        ]

        # เดือนและปีสำหรับปฏิทิน
        self.year = date.today().year
        self.month = date.today().month

        self.set_style()
        self.load_rooms_from_db()
        self.fetch_equipment_bookings_from_db()
        self.create_menu()
        self.show_home()

    def set_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", padding=6, fieldbackground=WHITE, background=WHITE)
        style.configure("TSpinbox", padding=5, fieldbackground=WHITE, background=WHITE)
        style.configure("Treeview", rowheight=28, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#E2E8F0")

    def load_rooms_from_db(self):
        """โหลดข้อมูลห้องประชุมจากฐานข้อมูล PostgreSQL"""
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, COALESCE(capacity, 10), COALESCE(description, '') FROM locations ORDER BY id;")
            rows = cur.fetchall()
            self.rooms_data = {row[1]: {"id": row[0], "capacity": row[2], "description": row[3]} for row in rows}
            cur.close()
            conn.close()

            # ตั้งค่าเริ่มต้นของห้อง
            if self.rooms_data and not self.room.get():
                first_room = list(self.rooms_data.keys())[0]
                self.room.set(first_room)
        except Exception as e:
            print("load_rooms_from_db error:", e)

    def fetch_bookings_from_db(self):
        """ดึงรายการจองทั้งหมดจากฐานข้อมูล PostgreSQL"""
        conn = get_connection()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    b.id, 
                    u.username, 
                    l.name AS room_name, 
                    b.booking_date, 
                    b.start_time, 
                    b.end_time, 
                    b.status,
                    COALESCE(b.department, '-') AS department,
                    COALESCE(b.people, 0) AS people,
                    COALESCE(b.topic, '-') AS topic,
                    b.user_id,
                    b.location_id
                FROM bookings b
                JOIN users u ON b.user_id = u.id
                JOIN locations l ON b.location_id = l.id
                ORDER BY b.booking_date DESC, b.start_time DESC;
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            bookings = []
            for r in rows:
                b_date = r[3].isoformat() if hasattr(r[3], 'isoformat') else str(r[3])
                s_time = str(r[4])[:5]
                e_time = str(r[5])[:5]
                bookings.append({
                    "id": r[0],
                    "username": r[1],
                    "room": r[2],
                    "date": b_date,
                    "start": s_time,
                    "end": e_time,
                    "status": r[6],
                    "department": r[7],
                    "people": r[8],
                    "topic": r[9],
                    "user_id": r[10],
                    "location_id": r[11]
                })
            self.bookings = bookings
            return bookings
        except Exception as e:
            print("fetch_bookings_from_db error:", e)
            return []

    def fetch_equipment_bookings_from_db(self):
        """ดึงรายการจองอุปกรณ์ทั้งหมดจากฐานข้อมูล PostgreSQL หรือใช้ข้อมูลในหน่วยความจำ"""
        conn = get_connection()
        if not conn:
            return self.equipment_bookings
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    eb.id, 
                    COALESCE(u.username, 'ไม่ระบุ') AS username, 
                    eb.equipment_name, 
                    eb.quantity, 
                    eb.booking_date, 
                    eb.start_time, 
                    eb.end_time, 
                    COALESCE(eb.department, '-') AS department, 
                    COALESCE(eb.purpose, '-') AS purpose,
                    eb.user_id
                FROM equipment_bookings eb
                LEFT JOIN users u ON eb.user_id = u.id
                ORDER BY eb.booking_date DESC, eb.start_time DESC;
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            items = []
            for r in rows:
                b_date = r[4].isoformat() if hasattr(r[4], 'isoformat') else str(r[4])
                s_time = str(r[5])[:5]
                e_time = str(r[6])[:5]
                items.append({
                    "id": r[0],
                    "username": r[1],
                    "equipment": r[2],
                    "quantity": r[3],
                    "date": b_date,
                    "start": s_time,
                    "end": e_time,
                    "department": r[7],
                    "purpose": r[8],
                    "user_id": r[9]
                })
            self.equipment_bookings = items
            return items
        except Exception as e:
            print("fetch_equipment_bookings_from_db error:", e)
            return self.equipment_bookings

    # ================= เมนูและการนำทาง =================
    def create_menu(self):
        self.sidebar = tk.Frame(self.root, bg=NAVY, width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # โลโก้และหัวข้อ
        tk.Label(self.sidebar, text="KB Booking", font=("Arial", 22, "bold"), bg=NAVY, fg=WHITE).pack(pady=(25, 4))
        tk.Label(self.sidebar, text="ระบบจองห้องประชุม", font=("Arial", 10), bg=NAVY, fg="#93C5FD").pack(pady=(0, 20))

        # การ์ดแสดงผู้ใช้ที่ล็อกอินอยู่
        role_label = "ผู้ดูแลระบบ (Admin)" if self.current_user["role"] == "admin" else "ผู้ใช้งานทั่วไป"
        role_bg = "#3B82F6" if self.current_user["role"] == "admin" else "#10B981"

        user_card = tk.Frame(self.sidebar, bg="#1E293B", padx=12, pady=10)
        user_card.pack(fill="x", padx=12, pady=(0, 20))

        tk.Label(user_card, text=f"👤 {self.current_user['username']}", font=("Arial", 11, "bold"), bg="#1E293B", fg=WHITE).pack(anchor="w")
        tk.Label(user_card, text=role_label, font=("Arial", 9), bg=role_bg, fg=WHITE, padx=6, pady=1).pack(anchor="w", pady=(4, 0))

        # ปุ่มเมนู
        self.menu_button("🏠 หน้าหลัก", self.show_home)
        self.menu_button("📅 จองห้องประชุม", self.show_booking)
        self.menu_button("📦 จองอุปกรณ์", self.show_equipment_booking)
        self.menu_button("🏢 ข้อมูลห้องประชุม", self.show_rooms)

        # เมนูเฉพาะแอดมิน (Admin Dashboard)
        if self.current_user["role"] == "admin":
            self.menu_button("⚙️ จัดการการจอง (Admin)", self.show_admin_dashboard)

        # ปุ่มออกจากระบบ (ด้านล่าง)
        spacer = tk.Frame(self.sidebar, bg=NAVY)
        spacer.pack(fill="both", expand=True)

        tk.Button(
            self.sidebar, text="🚪 ออกจากระบบ", command=self.logout,
            font=("Arial", 11), bg="#334155", fg=WHITE, activebackground=RED, activeforeground=WHITE,
            relief="flat", anchor="w", padx=20, pady=10, cursor="hand2"
        ).pack(fill="x", padx=12, pady=15)

        # พื้นที่หน้าหลัก
        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)

    def menu_button(self, text, command):
        tk.Button(
            self.sidebar, text=text, command=command,
            font=("Arial", 11), bg=NAVY, fg=WHITE,
            activebackground=NAVY_HOVER, activeforeground=WHITE,
            relief="flat", anchor="w", padx=20, pady=12, cursor="hand2"
        ).pack(fill="x", padx=10, pady=2)

    def clear_page(self):
        for widget in self.main.winfo_children():
            widget.destroy()

    def page_title(self, title, subtitle=""):
        tk.Label(self.main, text=title, font=("Arial", 22, "bold"), bg=BG, fg=NAVY).pack(anchor="w", padx=30, pady=(20, 4))
        if subtitle:
            tk.Label(self.main, text=subtitle, font=("Arial", 11), bg=BG, fg=TEXT_MUTED).pack(anchor="w", padx=32, pady=(0, 15))

    def make_button(self, parent, text, command, color=GREEN):
        return tk.Button(
            parent, text=text, command=command,
            font=("Arial", 11, "bold"), bg=color, fg=WHITE,
            activeforeground=WHITE, relief="flat", padx=12, pady=8, cursor="hand2"
        )

    def field_label(self, parent, text):
        tk.Label(parent, text=text, font=("Arial", 11, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(8, 4))

    def logout(self):
        if messagebox.askyesno("ยืนยัน", "คุณต้องการออกจากระบบหรือไม่?", parent=self.root):
            self.root.destroy()
            start_application()

    # ================= 1. หน้าหลัก (Home) =================
    def show_home(self):
        self.clear_page()
        self.page_title("หน้าหลัก", "ภาพรวมการจองห้องประชุม KB Booking เชื่อมต่อฐานข้อมูล")

        self.fetch_bookings_from_db()
        self.fetch_equipment_bookings_from_db()

        today_str = date.today().isoformat()
        total_count = len(self.bookings)
        today_count = sum(1 for b in self.bookings if b["date"] == today_str)
        pending_count = sum(1 for b in self.bookings if b["status"] == "pending")
        approved_count = sum(1 for b in self.bookings if b["status"] == "approved")

        # กล่องสรุปจำนวน (Summary Cards)
        cards = tk.Frame(self.main, bg=BG)
        cards.pack(fill="x", padx=30, pady=(0, 15))

        self.make_card(cards, "การจองทั้งหมด", total_count, BLUE)
        self.make_card(cards, "การจองวันนี้", today_count, GREEN)
        self.make_card(cards, "รอการอนุมัติ", pending_count, AMBER)
        self.make_card(cards, "อนุมัติแล้ว", approved_count, "#059669")

        # ส่วนหัวตารางและปุ่มรีเฟรช
        table_header = tk.Frame(self.main, bg=BG)
        table_header.pack(fill="x", padx=30, pady=(10, 8))

        tk.Label(table_header, text="รายการจองห้องประชุมทั้งหมด", font=("Arial", 15, "bold"), bg=BG, fg=NAVY).pack(side="left")
        
        tk.Button(
            table_header, text="🔄 รีเฟรชข้อมูล", command=self.show_home,
            font=("Arial", 10), bg=WHITE, fg=NAVY, relief="solid", bd=1, padx=10, pady=4, cursor="hand2"
        ).pack(side="right")

        # ตารางรายการจอง
        frame = tk.Frame(self.main, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        columns = ("date", "time", "room", "user", "dept", "people", "topic", "status")
        table = ttk.Treeview(frame, columns=columns, show="headings")

        headers = [
            ("date", "วันที่", 95),
            ("time", "เวลา", 110),
            ("room", "ห้องประชุม", 130),
            ("user", "ผู้จอง", 100),
            ("dept", "คณะ/หน่วยงาน", 160),
            ("people", "จำนวน", 65),
            ("topic", "หัวข้อประชุม", 180),
            ("status", "สถานะ", 110),
        ]

        for col, title, width in headers:
            table.heading(col, text=title)
            table.column(col, width=width, anchor="center")

        table.column("topic", anchor="w")
        table.column("dept", anchor="w")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)

        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # กำหนดสีแท็กตามสถานะ
        table.tag_configure("approved", foreground="#15803D")
        table.tag_configure("pending", foreground="#D97706")
        table.tag_configure("rejected", foreground="#DC2626")

        status_text_map = {
            "approved": "✅ อนุมัติแล้ว",
            "pending": "⏳ รออนุมัติ",
            "rejected": "❌ ปฏิเสธ"
        }

        for b in sorted(self.bookings, key=lambda item: (item["date"], item["start"]), reverse=True):
            st = b["status"]
            st_display = status_text_map.get(st, st)
            table.insert("", "end", values=(
                b["date"],
                f"{b['start']} - {b['end']}",
                b["room"],
                b["username"],
                b["department"],
                f"{b['people']} คน" if b['people'] else "-",
                b["topic"],
                st_display
            ), tags=(st,))

        if not self.bookings:
            tk.Label(self.main, text="ยังไม่มีรายการจองห้องประชุมในระบบ", bg=BG, fg=TEXT_MUTED, font=("Arial", 11)).pack(pady=10)

    def make_card(self, parent, title, value, color):
        card = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        card.pack(side="left", fill="x", expand=True, padx=4)

        tk.Label(card, text=title, font=("Arial", 11), bg=WHITE, fg=TEXT_MUTED).pack(anchor="w", padx=15, pady=(12, 4))
        tk.Label(card, text=str(value), font=("Arial", 22, "bold"), bg=WHITE, fg=color).pack(anchor="w", padx=15, pady=(0, 12))

    # ================= 2. หน้าจองห้อง (Booking) =================
    def show_booking(self):
        self.clear_page()
        self.page_title("จองห้องประชุม", "กรอกข้อมูลและเลือกวันที่กับเวลาที่ต้องการ (บันทึกสู่ฐานข้อมูล)")

        # รีเซ็ตฟอร์ม
        self.department.set("")
        if self.rooms_data:
            self.room.set(list(self.rooms_data.keys())[0])
        self.people.set("1")
        self.topic.set("")
        self.selected_date.set(date.today().isoformat())
        self.start_time.set("09:00")
        self.end_time.set("")

        self.year = date.today().year
        self.month = date.today().month

        content = tk.Frame(self.main, bg=BG)
        content.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # ฝั่งซ้าย: ข้อมูลแบบฟอร์ม
        left = tk.Frame(content, bg=WHITE, padx=20, pady=18, highlightbackground=BORDER, highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 15))

        # ฝั่งขวา: ปฏิทินและเวลา
        right = tk.Frame(content, bg=WHITE, padx=20, pady=18, highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="ข้อมูลการจอง", font=("Arial", 15, "bold"), bg=WHITE, fg=NAVY).pack(anchor="w")

        # คณะ/หน่วยงาน
        self.field_label(left, "คณะ / หน่วยงาน")
        ttk.Combobox(
            left, textvariable=self.department, values=self.departments,
            state="readonly", width=28
        ).pack(fill="x")

        # ห้องประชุม
        self.field_label(left, "ห้องประชุม")
        self.room_box = ttk.Combobox(
            left, textvariable=self.room, values=list(self.rooms_data.keys()),
            state="readonly", width=28
        )
        self.room_box.pack(fill="x")
        self.room_box.bind("<<ComboboxSelected>>", self.room_changed)

        # จำนวนผู้เข้าร่วม
        self.field_label(left, "จำนวนผู้เข้าร่วม (คน)")
        max_cap = self.rooms_data.get(self.room.get(), {}).get("capacity", 20)
        self.people_box = ttk.Spinbox(
            left, from_=1, to=max_cap, textvariable=self.people, width=28
        )
        self.people_box.pack(fill="x")

        self.capacity_label = tk.Label(left, text="", font=("Arial", 9), bg=WHITE)
        self.capacity_label.pack(anchor="w", pady=(4, 0))
        if not hasattr(self, "_people_traced"):
            self.people.trace_add("write", self.check_people)
            self._people_traced = True

        # หัวข้อการประชุม
        self.field_label(left, "หัวข้อการประชุม")
        tk.Entry(left, textvariable=self.topic, font=("Arial", 10), bg="#F8FAFC", relief="solid", bd=1).pack(fill="x", ipady=4)

        # วันที่จองที่เลือก
        self.field_label(left, "วันที่เลือกจอง")
        self.date_label = tk.Label(left, text=self.selected_date.get(), font=("Arial", 12, "bold"), bg=WHITE, fg=BLUE)
        self.date_label.pack(anchor="w")

        # ปุ่มบันทึกและล้างข้อมูล
        self.make_button(left, "💾 ส่งคำขอจองห้อง", self.save_booking, GREEN).pack(fill="x", pady=(20, 8))
        self.make_button(left, "ล้างข้อมูล", self.reset_form, "#64748B").pack(fill="x")

        # --- ฝั่งขวา: ปฏิทินและเวลา ---
        tk.Label(right, text="เลือกวันที่", font=("Arial", 14, "bold"), bg=WHITE, fg=NAVY).pack(anchor="w")
        self.calendar_frame = tk.Frame(right, bg=WHITE)
        self.calendar_frame.pack(fill="x", pady=6)
        self.draw_calendar()

        # เวลาเริ่ม
        time_section = tk.Frame(right, bg=WHITE)
        time_section.pack(fill="x", pady=(10, 0))

        tk.Label(time_section, text="เลือกเวลาเริ่ม:", font=("Arial", 11, "bold"), bg=WHITE, fg=NAVY).pack(side="left")
        tk.Label(time_section, textvariable=self.start_time, font=("Arial", 11, "bold"), bg=WHITE, fg=GREEN, padx=8).pack(side="left")

        self.start_frame = tk.Frame(right, bg=WHITE)
        self.start_frame.pack(fill="x", pady=4)

        # เวลาสิ้นสุด
        end_time_section = tk.Frame(right, bg=WHITE)
        end_time_section.pack(fill="x", pady=(10, 0))

        tk.Label(end_time_section, text="เลือกเวลาสิ้นสุด:", font=("Arial", 11, "bold"), bg=WHITE, fg=NAVY).pack(side="left")
        tk.Label(end_time_section, textvariable=self.end_time, font=("Arial", 11, "bold"), bg=WHITE, fg=BLUE, padx=8).pack(side="left")

        self.end_frame = tk.Frame(right, bg=WHITE)
        self.end_frame.pack(fill="x", pady=4)

        tk.Label(
            right, text="ℹ️ ปุ่มสีแดงหมายถึงช่วงเวลาที่ถูกจองแล้ว (ตรวจสอบจากฐานข้อมูลแบบ Real-time)",
            font=("Arial", 9), bg=WHITE, fg=RED
        ).pack(anchor="w", pady=8)

        self.fetch_bookings_from_db()
        self.draw_times()
        self.check_people()

    def check_people(self, *args):
        if not hasattr(self, "people_box") or not hasattr(self, "capacity_label"):
            return
        try:
            if not self.people_box.winfo_exists() or not self.capacity_label.winfo_exists():
                return
        except Exception:
            return

        try:
            val = int(self.people.get())
        except (ValueError, tk.TclError):
            val = 0

        max_cap = self.rooms_data.get(self.room.get(), {}).get("capacity", 20)
        try:
            if val < 1:
                self.people_box.configure(foreground=RED)
                self.capacity_label.config(text="กรุณากรอกอย่างน้อย 1 คน", fg=RED)
            elif val > max_cap:
                self.people_box.configure(foreground=RED)
                self.capacity_label.config(text=f"เกินความจุ! ห้องนี้รองรับได้ {max_cap} คน", fg=RED)
            else:
                self.people_box.configure(foreground=TEXT)
                self.capacity_label.config(text=f"ห้องนี้รองรับสูงสุด {max_cap} คน", fg=GREEN)
        except Exception:
            pass

    def room_changed(self, event=None):
        max_cap = self.rooms_data.get(self.room.get(), {}).get("capacity", 20)
        self.people_box.configure(to=max_cap)
        try:
            val = int(self.people.get())
        except (ValueError, tk.TclError):
            val = 1
        if val < 1 or val > max_cap:
            self.people.set("1")

        self.end_time.set("")
        self.draw_times()
        self.check_people()

    def reset_form(self):
        self.department.set("")
        if self.rooms_data:
            self.room.set(list(self.rooms_data.keys())[0])
        self.people.set("1")
        self.topic.set("")
        self.selected_date.set(date.today().isoformat())
        self.start_time.set("09:00")
        self.end_time.set("")

        self.year = date.today().year
        self.month = date.today().month

        self.date_label.config(text=self.selected_date.get())
        max_cap = self.rooms_data.get(self.room.get(), {}).get("capacity", 20)
        self.people_box.configure(to=max_cap)

        self.draw_calendar()
        self.draw_times()
        self.check_people()

    # --- ส่วนปฏิทิน ---
    def draw_calendar(self):
        for w in self.calendar_frame.winfo_children():
            w.destroy()

        header = tk.Frame(self.calendar_frame, bg=WHITE)
        header.pack(fill="x")

        self.make_button(header, "‹", lambda: self.change_month(-1), "#64748B").pack(side="left")
        month_name = calendar.month_name[self.month]
        tk.Label(header, text=f"{month_name} {self.year}", font=("Arial", 12, "bold"), bg=WHITE, fg=NAVY).pack(side="left", expand=True)
        self.make_button(header, "›", lambda: self.change_month(1), "#64748B").pack(side="right")

        grid = tk.Frame(self.calendar_frame, bg=WHITE)
        grid.pack(fill="x", pady=4)

        weekdays = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]
        for col, day_name in enumerate(weekdays):
            tk.Label(grid, text=day_name, bg=WHITE, fg=TEXT_MUTED, width=4, font=("Arial", 9, "bold")).grid(row=0, column=col)

        weeks = calendar.monthcalendar(self.year, self.month)
        for row, week in enumerate(weeks, start=1):
            for col, day in enumerate(week):
                if day == 0:
                    continue
                date_text = f"{self.year:04d}-{self.month:02d}-{day:02d}"
                selected = (self.selected_date.get() == date_text)

                btn = tk.Button(
                    grid, text=str(day), width=3,
                    bg=GREEN if selected else "#F1F5F9",
                    fg=WHITE if selected else TEXT,
                    relief="flat", cursor="hand2",
                    command=lambda d=day: self.pick_date(d)
                )
                btn.grid(row=row, column=col, padx=2, pady=2)

    def change_month(self, amount):
        self.month += amount
        if self.month > 12:
            self.month = 1
            self.year += 1
        elif self.month < 1:
            self.month = 12
            self.year -= 1
        self.draw_calendar()

    def pick_date(self, day):
        self.selected_date.set(f"{self.year:04d}-{self.month:02d}-{day:02d}")
        self.date_label.config(text=self.selected_date.get())
        self.end_time.set("")
        self.draw_calendar()
        self.fetch_bookings_from_db()
        self.draw_times()

    # --- ส่วนเลือกเวลาและตรวจสอบจากฐานข้อมูล ---
    def time_is_booked(self, time_text, kind):
        """ตรวจสอบว่าเวลานี้ถูกจองในฐานข้อมูลหรือไม่ (ไม่นับรายการที่ถูก rejected)"""
        current_room = self.room.get()
        current_date = self.selected_date.get()

        for b in self.bookings:
            if b["status"] == "rejected":
                continue
            if b["room"] != current_room:
                continue
            if b["date"] != current_date:
                continue

            s = b["start"]
            e = b["end"]

            if kind == "start":
                if s <= time_text < e:
                    return True
            else:
                if s < time_text <= e:
                    return True
        return False

    def draw_times(self):
        if not hasattr(self, "start_frame"):
            return

        for w in self.start_frame.winfo_children():
            w.destroy()
        for w in self.end_frame.winfo_children():
            w.destroy()

        times = [f"{hour:02d}:00" for hour in range(7, 23)]
        self.make_time_buttons(self.start_frame, times, "start")
        self.make_time_buttons(self.end_frame, times, "end")

    def make_time_buttons(self, parent, times, kind):
        selected_time = self.start_time.get() if kind == "start" else self.end_time.get()

        for index, time_text in enumerate(times):
            booked = self.time_is_booked(time_text, kind)
            invalid_end = (kind == "end" and time_text <= self.start_time.get())

            if selected_time == time_text:
                color = GREEN
                text_color = WHITE
                state = "normal"
            elif booked:
                color = "#FEE2E2"
                text_color = RED
                state = "disabled"
            elif invalid_end:
                color = "#E5E7EB"
                text_color = "#9CA3AF"
                state = "disabled"
            else:
                color = "#F1F5F9"
                text_color = TEXT
                state = "normal"

            tk.Button(
                parent, text=time_text, bg=color, fg=text_color,
                disabledforeground=RED if booked else "#9CA3AF",
                relief="flat", state=state, cursor="hand2" if state == "normal" else "arrow",
                command=lambda t=time_text, k=kind: self.pick_time(t, k)
            ).grid(row=index // 8, column=index % 8, padx=2, pady=2, sticky="ew")

        for col in range(8):
            parent.columnconfigure(col, weight=1)

    def pick_time(self, time_text, kind):
        if kind == "start":
            if self.time_is_booked(time_text, "start"):
                messagebox.showwarning("เวลาไม่ว่าง", "ช่วงเวลานี้ถูกจองแล้วในระบบ", parent=self.root)
                return
            self.start_time.set(time_text)
            self.end_time.set("")
        else:
            if time_text <= self.start_time.get():
                messagebox.showwarning("เวลาไม่ถูกต้อง", "เวลาสิ้นสุดต้องมากกว่าเวลาเริ่ม", parent=self.root)
                return
            if self.time_is_booked(time_text, "end"):
                messagebox.showwarning("เวลาไม่ว่าง", "ช่วงเวลานี้ทับกับการจองอื่น", parent=self.root)
                return
            self.end_time.set(time_text)

        self.draw_times()

    def save_booking(self):
        """บันทึกข้อมูลการจองลงฐานข้อมูล PostgreSQL"""
        dept = self.department.get().strip()
        room_name = self.room.get()
        topic = self.topic.get().strip()
        b_date = self.selected_date.get()
        start = self.start_time.get()
        end = self.end_time.get()

        if not dept or not topic:
            messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณาเลือกคณะ/หน่วยงาน และกรอกหัวข้อการประชุม", parent=self.root)
            return

        try:
            people_val = int(self.people.get())
        except ValueError:
            messagebox.showwarning("ข้อมูลไม่ถูกต้อง", "กรุณากรอกจำนวนผู้เข้าร่วมเป็นตัวเลข", parent=self.root)
            return

        max_cap = self.rooms_data.get(room_name, {}).get("capacity", 20)
        if people_val < 1 or people_val > max_cap:
            messagebox.showwarning("จำนวนคนไม่ถูกต้อง", f"{room_name} รองรับได้ 1 ถึง {max_cap} คน", parent=self.root)
            return

        if not start or not end or end <= start:
            messagebox.showwarning("เวลาไม่ถูกต้อง", "กรุณาเลือกเวลาเริ่มและเวลาสิ้นสุดให้ถูกต้อง", parent=self.root)
            return

        loc_info = self.rooms_data.get(room_name)
        if not loc_info:
            messagebox.showerror("Error", "ไม่พบข้อมูลห้องประชุมในระบบ", parent=self.root)
            return
        loc_id = loc_info["id"]

        # ตรวจสอบว่ามีรายการทับซ้อนในฐานข้อมูลหรือไม่
        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id FROM bookings
                WHERE location_id = %s AND booking_date = %s AND status != 'rejected'
                  AND NOT (end_time <= %s OR start_time >= %s);
            """, (loc_id, b_date, start, end))
            overlap = cur.fetchone()

            if overlap:
                messagebox.showerror("เวลาซ้ำ", "ห้องนี้มีผู้จองในช่วงเวลาดังกล่าวแล้ว กรุณาเลือกช่วงเวลาอื่น", parent=self.root)
                cur.close()
                conn.close()
                return

            # บันทึกลงตาราง bookings
            cur.execute("""
                INSERT INTO bookings (user_id, location_id, booking_date, start_time, end_time, status, department, people, topic)
                VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s, %s);
            """, (self.current_user["id"], loc_id, b_date, start, end, dept, people_val, topic))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo(
                "จองสำเร็จ",
                f"ส่งคำขอจอง {room_name} เรียบร้อยแล้ว!\n"
                f"วันที่: {b_date}\n"
                f"เวลา: {start} - {end}\n"
                f"สถานะ: รอแอดมินอนุมัติ (Pending)",
                parent=self.root
            )
            self.show_home()

        except Exception as e:
            conn.rollback()
            conn.close()
            messagebox.showerror("Database Error", f"เกิดข้อผิดพลาดในการบันทึก:\n{e}", parent=self.root)

    # ================= 2.1 ระบบจองอุปกรณ์ (Equipment Booking) =================
    def show_equipment_booking(self):
        self.clear_page()
        self.page_title("จองอุปกรณ์", "เลือกอุปกรณ์และกรอกข้อมูลสำหรับการจอง (เชื่อมต่อฐานข้อมูล)")

        self.fetch_equipment_bookings_from_db()

        self.eq_department = tk.StringVar(value=self.departments[0] if self.departments else "")
        self.eq_name = tk.StringVar(value="โปรเจกเตอร์")
        self.eq_quantity = tk.StringVar(value="1")
        self.eq_date = tk.StringVar(value=date.today().isoformat())
        self.eq_start = tk.StringVar(value="09:00")
        self.eq_end = tk.StringVar(value="10:00")
        self.eq_purpose = tk.StringVar()

        content = tk.Frame(self.main, bg=BG)
        content.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # ฝั่งซ้าย: ฟอร์มการจองอุปกรณ์
        left = tk.Frame(content, bg=WHITE, padx=22, pady=18, highlightbackground=BORDER, highlightthickness=1, width=380)
        left.pack(side="left", fill="y", padx=(0, 15))
        left.pack_propagate(False)

        # ฝั่งขวา: สรุปคลังอุปกรณ์และตารางรายการจอง
        right = tk.Frame(content, bg=WHITE, padx=20, pady=18, highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="แบบฟอร์มจองอุปกรณ์", font=("Arial", 15, "bold"), bg=WHITE, fg=NAVY).pack(anchor="w")

        # คณะ/หน่วยงาน
        self.field_label(left, "คณะ / หน่วยงาน")
        ttk.Combobox(
            left, textvariable=self.eq_department, values=self.departments,
            state="readonly", width=28
        ).pack(fill="x")

        # เลือกอุปกรณ์
        self.field_label(left, "เลือกอุปกรณ์")
        equipment_box = ttk.Combobox(
            left, textvariable=self.eq_name, values=list(self.equipment_stock.keys()),
            state="readonly", width=28
        )
        equipment_box.pack(fill="x")
        equipment_box.bind("<<ComboboxSelected>>", lambda e: self.update_equipment_stock())

        # ป้ายแสดงสต็อกคงเหลือ
        self.stock_label = tk.Label(left, text="", bg=WHITE, fg=GREEN, font=("Arial", 9, "bold"))
        self.stock_label.pack(anchor="w", pady=(4, 2))

        # จำนวนที่ต้องการ
        self.field_label(left, "จำนวนที่ต้องการจอง (ชิ้น)")
        max_stock = self.equipment_stock.get(self.eq_name.get(), 10)
        self.eq_qty_spin = ttk.Spinbox(
            left, from_=1, to=max_stock, textvariable=self.eq_quantity, width=28
        )
        self.eq_qty_spin.pack(fill="x")

        # วันที่จอง
        self.field_label(left, "วันที่จอง (YYYY-MM-DD)")
        tk.Entry(left, textvariable=self.eq_date, font=("Arial", 10), bg="#F8FAFC", relief="solid", bd=1).pack(fill="x", ipady=3)

        # เวลาเริ่ม และ เวลาสิ้นสุด
        time_frame = tk.Frame(left, bg=WHITE)
        time_frame.pack(fill="x", pady=(6, 0))

        tk.Label(time_frame, text="เวลาเริ่ม:", font=("Arial", 10), bg=WHITE, fg=NAVY).grid(row=0, column=0, sticky="w", pady=(0, 2))
        tk.Label(time_frame, text="เวลาสิ้นสุด:", font=("Arial", 10), bg=WHITE, fg=NAVY).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0, 2))

        start_times = [f"{h:02d}:00" for h in range(7, 23)]
        end_times = [f"{h:02d}:00" for h in range(8, 24)]

        start_cb = ttk.Combobox(time_frame, textvariable=self.eq_start, values=start_times, state="readonly", width=12)
        start_cb.grid(row=1, column=0, sticky="ew")
        start_cb.bind("<<ComboboxSelected>>", lambda e: self.update_equipment_stock())

        end_cb = ttk.Combobox(time_frame, textvariable=self.eq_end, values=end_times, state="readonly", width=12)
        end_cb.grid(row=1, column=1, sticky="ew", padx=(10, 0))
        end_cb.bind("<<ComboboxSelected>>", lambda e: self.update_equipment_stock())

        # วัตถุประสงค์
        self.field_label(left, "วัตถุประสงค์การใช้งาน")
        tk.Entry(left, textvariable=self.eq_purpose, font=("Arial", 10), bg="#F8FAFC", relief="solid", bd=1).pack(fill="x", ipady=3)

        # ปุ่มบันทึก
        self.make_button(left, "💾 บันทึกการจองอุปกรณ์", self.save_equipment_booking, GREEN).pack(fill="x", pady=(18, 6))

        # ฝั่งขวา: รายการคงคลังอุปกรณ์ + ตาราง
        top_right = tk.Frame(right, bg=WHITE)
        top_right.pack(fill="x", pady=(0, 10))

        tk.Label(top_right, text="📦 คลังอุปกรณ์ทั้งหมด", font=("Arial", 14, "bold"), bg=WHITE, fg=NAVY).pack(side="left")

        # การ์ดแสดงอุปกรณ์ทั้งหมด
        stock_cards = tk.Frame(right, bg=WHITE)
        stock_cards.pack(fill="x", pady=(0, 15))

        for eq, total in self.equipment_stock.items():
            card = tk.Frame(stock_cards, bg="#F1F5F9", padx=10, pady=8, highlightbackground="#E2E8F0", highlightthickness=1)
            card.pack(side="left", padx=4, pady=2, fill="x", expand=True)
            tk.Label(card, text=eq, font=("Arial", 9, "bold"), bg="#F1F5F9", fg=TEXT).pack()
            tk.Label(card, text=f"{total} ชิ้น", font=("Arial", 11, "bold"), bg="#F1F5F9", fg=BLUE).pack()

        # ส่วนหัวตารางรายการจอง
        table_hdr = tk.Frame(right, bg=WHITE)
        table_hdr.pack(fill="x", pady=(5, 6))

        tk.Label(table_hdr, text="📋 รายการจองอุปกรณ์", font=("Arial", 14, "bold"), bg=WHITE, fg=NAVY).pack(side="left")

        btn_box = tk.Frame(table_hdr, bg=WHITE)
        btn_box.pack(side="right")

        tk.Button(
            btn_box, text="🗑️ ยกเลิกรายการที่เลือก", command=self.delete_equipment_booking,
            font=("Arial", 9), bg="#FEE2E2", fg=RED, relief="flat", padx=8, pady=3, cursor="hand2"
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_box, text="🔄 รีเฟรช", command=self.show_equipment_booking,
            font=("Arial", 9), bg=WHITE, fg=NAVY, relief="solid", bd=1, padx=8, pady=3, cursor="hand2"
        ).pack(side="left")

        # ตาราง Treeview
        columns = ("id", "date", "time", "equipment", "quantity", "user", "department", "purpose")
        self.equipment_table = ttk.Treeview(right, columns=columns, show="headings", selectmode="browse")

        headers = [
            ("id", "ID", 45),
            ("date", "วันที่", 90),
            ("time", "ช่วงเวลา", 105),
            ("equipment", "อุปกรณ์", 110),
            ("quantity", "จำนวน", 65),
            ("user", "ผู้ขอจอง", 95),
            ("department", "คณะ/หน่วยงาน", 140),
            ("purpose", "วัตถุประสงค์", 160)
        ]

        for col, title, width in headers:
            self.equipment_table.heading(col, text=title)
            self.equipment_table.column(col, width=width, anchor="center")

        self.equipment_table.column("purpose", anchor="w")
        self.equipment_table.column("department", anchor="w")

        eq_scroll = ttk.Scrollbar(right, orient="vertical", command=self.equipment_table.yview)
        self.equipment_table.configure(yscrollcommand=eq_scroll.set)

        self.equipment_table.pack(side="left", fill="both", expand=True)
        eq_scroll.pack(side="right", fill="y")

        self.update_equipment_stock()
        self.refresh_equipment_table()

    def update_equipment_stock(self):
        if not hasattr(self, "stock_label"):
            return
        name = self.eq_name.get()
        total = self.equipment_stock.get(name, 0)
        
        if hasattr(self, "eq_qty_spin"):
            self.eq_qty_spin.configure(to=total)

        b_date = self.eq_date.get().strip() if hasattr(self, "eq_date") else ""
        start = self.eq_start.get() if hasattr(self, "eq_start") else ""
        end = self.eq_end.get() if hasattr(self, "eq_end") else ""

        already_booked = 0
        if b_date and start and end:
            for b in self.equipment_bookings:
                if b["equipment"] == name and b["date"] == b_date:
                    if start < b["end"] and end > b["start"]:
                        already_booked += b["quantity"]

        avail = max(0, total - already_booked)
        self.stock_label.config(
            text=f"ทั้งหมด: {total} ชิ้น  |  ว่างในช่วงเวลานี้: {avail} ชิ้น",
            fg=GREEN if avail > 0 else RED
        )

    def save_equipment_booking(self):
        dept = self.eq_department.get().strip()
        equipment = self.eq_name.get().strip()
        purpose = self.eq_purpose.get().strip()
        booking_date = self.eq_date.get().strip()
        start = self.eq_start.get().strip()
        end = self.eq_end.get().strip()

        if not dept or not purpose or not booking_date:
            messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณากรอกคณะ/หน่วยงาน วันที่ และวัตถุประสงค์", parent=self.root)
            return

        try:
            date.fromisoformat(booking_date)
        except ValueError:
            messagebox.showwarning("วันที่ไม่ถูกต้อง", "กรุณากรอกวันที่ในรูปแบบ YYYY-MM-DD (เช่น 2026-10-29)", parent=self.root)
            return

        try:
            quantity = int(self.eq_quantity.get())
        except ValueError:
            messagebox.showwarning("จำนวนไม่ถูกต้อง", "กรุณากรอกจำนวนเป็นตัวเลข", parent=self.root)
            return

        if quantity < 1:
            messagebox.showwarning("จำนวนไม่ถูกต้อง", "จำนวนต้องมากกว่า 0", parent=self.root)
            return

        if not start or not end or end <= start:
            messagebox.showwarning("เวลาไม่ถูกต้อง", "เวลาสิ้นสุดต้องมากกว่าเวลาเริ่ม", parent=self.root)
            return

        total_stock = self.equipment_stock.get(equipment, 0)
        already_booked = 0

        for b in self.equipment_bookings:
            if b["equipment"] == equipment and b["date"] == booking_date:
                if start < b["end"] and end > b["start"]:
                    already_booked += b["quantity"]

        available = total_stock - already_booked

        if quantity > available:
            messagebox.showwarning(
                "อุปกรณ์ไม่เพียงพอ",
                f"{equipment} เหลือว่างเพียง {available} ชิ้น ในช่วงเวลาที่เลือก (ขอจอง {quantity} ชิ้น)",
                parent=self.root
            )
            return

        # บันทึกลงฐานข้อมูล PostgreSQL (หรือทำงานต่อถ้า DB ไม่พร้อม)
        conn = get_connection()
        new_id = len(self.equipment_bookings) + 1
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO equipment_bookings (user_id, equipment_name, quantity, booking_date, start_time, end_time, department, purpose)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (self.current_user["id"], equipment, quantity, booking_date, start, end, dept, purpose))
                new_id = cur.fetchone()[0]
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                conn.rollback()
                conn.close()
                print("Save equipment to DB failed, fallback to memory:", e)

        new_booking = {
            "id": new_id,
            "username": self.current_user["username"],
            "date": booking_date,
            "start": start,
            "end": end,
            "equipment": equipment,
            "quantity": quantity,
            "department": dept,
            "purpose": purpose,
            "user_id": self.current_user["id"]
        }
        self.equipment_bookings.insert(0, new_booking)

        messagebox.showinfo(
            "จองสำเร็จ",
            f"จอง {equipment} สำเร็จ!\n"
            f"วันที่: {booking_date}\n"
            f"เวลา: {start} - {end}\n"
            f"จำนวน: {quantity} ชิ้น\n"
            f"ผู้จอง: {self.current_user['username']}",
            parent=self.root
        )

        self.eq_purpose.set("")
        self.fetch_equipment_bookings_from_db()
        self.refresh_equipment_table()
        self.update_equipment_stock()

    def refresh_equipment_table(self):
        if not hasattr(self, "equipment_table"):
            return
        for item in self.equipment_table.get_children():
            self.equipment_table.delete(item)

        for b in sorted(self.equipment_bookings, key=lambda x: (x["date"], x["start"]), reverse=True):
            self.equipment_table.insert(
                "", "end",
                values=(
                    b.get("id", "-"),
                    b["date"],
                    f"{b['start']} - {b['end']}",
                    b["equipment"],
                    f"{b['quantity']} ชิ้น",
                    b.get("username", "-"),
                    b["department"],
                    b["purpose"]
                )
            )

    def delete_equipment_booking(self):
        if not hasattr(self, "equipment_table"):
            return
        selected = self.equipment_table.selection()
        if not selected:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกรายการจองอุปกรณ์ที่ต้องการยกเลิก", parent=self.root)
            return

        values = self.equipment_table.item(selected[0])["values"]
        b_id = values[0]
        b_user = values[5]

        # ตรวจสอบสิทธิ์: แอดมิน หรือ เจ้าของรายการจอง
        is_admin = self.current_user["role"] == "admin"
        is_owner = b_user == self.current_user["username"]
        if not (is_admin or is_owner):
            messagebox.showerror("ไม่มีสิทธิ์", "คุณสามารถยกเลิกได้เฉพาะรายการจองของคุณเองเท่านั้น", parent=self.root)
            return

        if not messagebox.askyesno("ยืนยัน", f"คุณต้องการยกเลิกรายการจองอุปกรณ์ ID #{b_id} ใช่หรือไม่?", parent=self.root):
            return

        conn = get_connection()
        if conn and str(b_id).isdigit():
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM equipment_bookings WHERE id = %s;", (b_id,))
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                conn.rollback()
                conn.close()
                print("Delete equipment from DB failed:", e)

        self.equipment_bookings = [b for b in self.equipment_bookings if str(b.get("id")) != str(b_id)]
        messagebox.showinfo("สำเร็จ", f"ยกเลิกรายการจอง #{b_id} เรียบร้อยแล้ว", parent=self.root)
        self.refresh_equipment_table()
        self.update_equipment_stock()

    # ================= 3. ข้อมูลห้องประชุม (Rooms) =================
    def show_rooms(self):
        self.clear_page()
        self.page_title("ข้อมูลห้องประชุม", "รายละเอียดและความจุของแต่ละห้องประชุมจากฐานข้อมูล")

        self.load_rooms_from_db()

        container = tk.Frame(self.main, bg=BG)
        container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        for room_name, info in self.rooms_data.items():
            card = tk.Frame(container, bg=WHITE, padx=22, pady=18, highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", pady=8)

            top_row = tk.Frame(card, bg=WHITE)
            top_row.pack(fill="x")

            tk.Label(top_row, text=room_name, font=("Arial", 16, "bold"), bg=WHITE, fg=NAVY).pack(side="left")
            cap_badge = tk.Label(top_row, text=f"รองรับสูงสุด {info['capacity']} คน", font=("Arial", 10, "bold"), bg="#DCFCE7", fg="#15803D", padx=8, pady=2)
            cap_badge.pack(side="right")

            desc = info["description"] if info["description"] else "ไม่มีรายละเอียดเพิ่มเติม"
            tk.Label(card, text=desc, font=("Arial", 11), bg=WHITE, fg=TEXT_MUTED).pack(anchor="w", pady=(8, 0))

    # ================= 4. หน้าจอจัดการการจอง (Admin Dashboard) =================
    def show_admin_dashboard(self):
        if self.current_user["role"] != "admin":
            messagebox.showerror("ไม่มีสิทธิ์", "หน้านี้สำหรับผู้ดูแลระบบเท่านั้น", parent=self.root)
            return

        self.clear_page()
        self.page_title("Admin Dashboard - จัดการการจอง", "อนุมัติหรือปฏิเสธคำขอจองห้องประชุม")

        self.fetch_bookings_from_db()

        # แถบปุ่มจัดการด้านบน
        action_bar = tk.Frame(self.main, bg=BG)
        action_bar.pack(fill="x", padx=30, pady=(0, 10))

        # ตารางข้อมูล Treeview
        frame = tk.Frame(self.main, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=30, pady=(0, 15))

        columns = ("id", "user", "room", "date", "time", "dept", "people", "topic", "status")
        admin_tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

        headers = [
            ("id", "ID", 50),
            ("user", "ผู้ขอจอง", 100),
            ("room", "ห้องประชุม", 120),
            ("date", "วันที่", 95),
            ("time", "เวลา", 105),
            ("dept", "คณะ/หน่วยงาน", 150),
            ("people", "จำนวน", 65),
            ("topic", "หัวข้อประชุม", 170),
            ("status", "สถานะ", 110)
        ]

        for col, title, width in headers:
            admin_tree.heading(col, text=title)
            admin_tree.column(col, width=width, anchor="center")

        admin_tree.column("topic", anchor="w")
        admin_tree.column("dept", anchor="w")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=admin_tree.yview)
        admin_tree.configure(yscrollcommand=scrollbar.set)

        admin_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        admin_tree.tag_configure("approved", foreground="#15803D")
        admin_tree.tag_configure("pending", foreground="#D97706")
        admin_tree.tag_configure("rejected", foreground="#DC2626")

        status_map = {
            "approved": "✅ อนุมัติแล้ว",
            "pending": "⏳ รออนุมัติ",
            "rejected": "❌ ปฏิเสธ"
        }

        for b in sorted(self.bookings, key=lambda x: x["id"], reverse=True):
            st = b["status"]
            admin_tree.insert("", "end", values=(
                b["id"],
                b["username"],
                b["room"],
                b["date"],
                f"{b['start']} - {b['end']}",
                b["department"],
                f"{b['people']} คน" if b['people'] else "-",
                b["topic"],
                status_map.get(st, st)
            ), tags=(st,))

        def change_booking_status(new_status):
            selected = admin_tree.selection()
            if not selected:
                messagebox.showwarning("คำเตือน", "กรุณาเลือกรายการจองที่ต้องการจัดการ", parent=self.root)
                return

            booking_id = admin_tree.item(selected[0])["values"][0]
            conn = get_connection()
            if not conn:
                return

            try:
                cur = conn.cursor()
                cur.execute("UPDATE bookings SET status = %s WHERE id = %s;", (new_status, booking_id))
                conn.commit()
                cur.close()
                conn.close()

                status_label = "อนุมัติ" if new_status == "approved" else "ปฏิเสธ"
                messagebox.showinfo("สำเร็จ", f"เปลี่ยนสถานะรายการ ID #{booking_id} เป็น '{status_label}' เรียบร้อยแล้ว", parent=self.root)
                self.show_admin_dashboard()
            except Exception as e:
                conn.rollback()
                conn.close()
                messagebox.showerror("Error", f"เกิดข้อผิดพลาด:\n{e}", parent=self.root)

        def delete_booking():
            selected = admin_tree.selection()
            if not selected:
                messagebox.showwarning("คำเตือน", "กรุณาเลือกรายการจองที่ต้องการลบ", parent=self.root)
                return

            booking_id = admin_tree.item(selected[0])["values"][0]
            if not messagebox.askyesno("ยืนยันการลบ", f"คุณต้องการลบรายการจอง ID #{booking_id} ใช่หรือไม่?", parent=self.root):
                return

            conn = get_connection()
            if not conn:
                return

            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM bookings WHERE id = %s;", (booking_id,))
                conn.commit()
                cur.close()
                conn.close()
                messagebox.showinfo("สำเร็จ", f"ลบรายการจอง ID #{booking_id} เรียบร้อยแล้ว", parent=self.root)
                self.show_admin_dashboard()
            except Exception as e:
                conn.rollback()
                conn.close()
                messagebox.showerror("Error", f"เกิดข้อผิดพลาดในการลบ:\n{e}", parent=self.root)

        # ปุ่มคำสั่งด้านล่างตาราง
        btn_container = tk.Frame(self.main, bg=BG)
        btn_container.pack(fill="x", padx=30, pady=(0, 20))

        tk.Button(
            btn_container, text="✅ อนุมัติการจอง (Approve)", command=lambda: change_booking_status("approved"),
            font=("Arial", 11, "bold"), bg=GREEN, fg=WHITE, relief="flat", padx=15, pady=8, cursor="hand2"
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_container, text="❌ ปฏิเสธการจอง (Reject)", command=lambda: change_booking_status("rejected"),
            font=("Arial", 11, "bold"), bg=RED, fg=WHITE, relief="flat", padx=15, pady=8, cursor="hand2"
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_container, text="🗑️ ลบรายการ", command=delete_booking,
            font=("Arial", 11), bg="#64748B", fg=WHITE, relief="flat", padx=12, pady=8, cursor="hand2"
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_container, text="🔄 รีเฟรช", command=self.show_admin_dashboard,
            font=("Arial", 11), bg=WHITE, fg=NAVY, relief="solid", bd=1, padx=12, pady=7, cursor="hand2"
        ).pack(side="right")


# ==========================================
# 5. ฟังก์ชันเปิดโปรแกรม
# ==========================================
def open_main_app(user_id, username, role):
    main_root = tk.Tk()
    app = MeetingRoomApp(main_root, {"id": user_id, "username": username, "role": role})
    main_root.mainloop()

def start_application():
    # ตรวจสอบและเตรียมฐานข้อมูล
    init_db()
    # เปิดหน้าต่าง Login
    login_root = tk.Tk()
    LoginWindow(login_root, open_main_app)
    login_root.mainloop()

if __name__ == "__main__":
    start_application()
