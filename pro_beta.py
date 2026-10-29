import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
import calendar
import psycopg2
import hashlib

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
        print("Database connection error:", e)
        return None

def init_db():
    """สร้างตารางและคอลัมน์ที่จำเป็น พร้อมเพิ่มข้อมูลเริ่มต้น"""
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

        # 2. ตาราง locations (ห้องประชุม)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                capacity INTEGER DEFAULT 10,
                description TEXT
            );
        """)
        cur.execute("ALTER TABLE locations ADD COLUMN IF NOT EXISTS capacity INTEGER DEFAULT 10;")
        cur.execute("ALTER TABLE locations ADD COLUMN IF NOT EXISTS description TEXT;")

        # 3. ตาราง equipment (คลังอุปกรณ์สำหรับแอดมินแก้ไข/เพิ่ม/ลด)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                id SERIAL PRIMARY KEY,
                name VARCHAR(150) UNIQUE NOT NULL,
                total_stock INTEGER NOT NULL DEFAULT 5,
                description TEXT
            );
        """)

        # 4. ตาราง bookings (การจองห้อง)
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
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS department VARCHAR(255);")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS people INTEGER;")
        cur.execute("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS topic VARCHAR(255);")

        # 5. ตาราง equipment_bookings (การจองอุปกรณ์)
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
                status VARCHAR(20) DEFAULT 'approved' CHECK (status IN ('pending', 'approved', 'rejected')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("ALTER TABLE equipment_bookings ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'approved';")

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

        # เพิ่มอุปกรณ์เริ่มต้นหากยังไม่มี
        default_equipments = [
            ("โปรเจกเตอร์", 5, "ความคมชัด Full HD พร้อมรีโมทควบคุม"),
            ("ไมโครโฟน", 10, "ไมโครโฟนไร้สาย Wireless Microphone"),
            ("ลำโพง", 4, "ลำโพงพกพาพร้อมแอมป์ขยายเสียง"),
            ("โน้ตบุ๊ก", 8, "โน้ตบุ๊กสำหรับนำเสนองาน Windows 11"),
            ("สาย HDMI", 10, "สายเชื่อมต่อสัญญาณภาพความยาว 5 เมตร"),
            ("ปลั๊กพ่วง", 10, "ปลั๊กไฟพ่วงมาตรฐานความปลอดภัย 5 ช่อง")
        ]
        for name, stock, desc in default_equipments:
            cur.execute("SELECT id FROM equipment WHERE name = %s;", (name,))
            if not cur.fetchone():
                cur.execute("INSERT INTO equipment (name, total_stock, description) VALUES (%s, %s, %s);", (name, stock, desc))

        # ตรวจสอบ admin
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
PURPLE = "#7C3AED"


# ==========================================
# 2.1 ตัวช่วยวาด QR Code บน Canvas (Pure Tkinter)
# ==========================================
def draw_qr_on_canvas(canvas, payload, size=200):
    """สร้างและวาดรูป QR Code เสมือนจริงบน Tkinter Canvas โดยไม่ต้องใช้ไลบรารีภายนอก"""
    canvas.delete("all")
    dim = 25  # ตารางขนาด 25x25 โมดูล (Version 2 QR Code)
    box = size / dim

    # สร้าง matrix 25x25 (0 = ขาว, 1 = ดำ)
    matrix = [[0 for _ in range(dim)] for _ in range(dim)]

    def draw_finder(top_r, top_c):
        for r in range(7):
            for c in range(7):
                if r in (0, 6) or c in (0, 6) or (2 <= r <= 4 and 2 <= c <= 4):
                    matrix[top_r + r][top_c + c] = 1

    # 1. วาด Finder Pattern 3 มุม
    draw_finder(0, 0)
    draw_finder(0, dim - 7)
    draw_finder(dim - 7, 0)

    # 2. วาด Timing Pattern
    for i in range(8, dim - 8):
        matrix[6][i] = 1 if i % 2 == 0 else 0
        matrix[i][6] = 1 if i % 2 == 0 else 0

    # 3. วาด Alignment Pattern (มุมขวาล่าง)
    for r in range(dim - 9, dim - 4):
        for c in range(dim - 9, dim - 4):
            if r in (dim - 9, dim - 5) or c in (dim - 9, dim - 5) or (r == dim - 7 and c == dim - 7):
                matrix[r][c] = 1

    # 4. แปลง payload เป็นไบต์ด้วย hash เพื่อจำลองการเข้ารหัสข้อมูลในช่องว่าง
    h = hashlib.sha256(payload.encode("utf-8")).digest()
    bit_idx = 0
    total_bits = len(h) * 8

    for r in range(dim):
        for c in range(dim):
            # ข้ามบริเวณ Finder Pattern
            in_tl = r < 8 and c < 8
            in_tr = r < 8 and c >= dim - 8
            in_bl = r >= dim - 8 and c < 8
            in_align = (dim - 9 <= r <= dim - 4) and (dim - 9 <= c <= dim - 4)
            in_timing = (r == 6 or c == 6)

            if not (in_tl or in_tr or in_bl or in_align or in_timing):
                byte_val = h[(bit_idx // 8) % len(h)]
                bit = (byte_val >> (bit_idx % 8)) & 1
                matrix[r][c] = bit
                bit_idx += 1

    # วาดลงบน Canvas
    for r in range(dim):
        for c in range(dim):
            if matrix[r][c] == 1:
                x1 = c * box
                y1 = r * box
                x2 = x1 + box
                y2 = y1 + box
                canvas.create_rectangle(x1, y1, x2, y2, fill="black", outline="black")


# ==========================================
# 3. หน้าต่างเข้าสู่ระบบและสมัครสมาชิก
# ==========================================
class LoginWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.root.title("KB Booking (Beta) - เข้าสู่ระบบ")
        self.root.geometry("460x570")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.center_window(460, 570)

        card = tk.Frame(self.root, bg=WHITE, padx=35, pady=30, highlightbackground=BORDER, highlightthickness=1)
        card.pack(expand=True, fill="both", padx=30, pady=30)

        # Header
        top_badge = tk.Label(card, text="BETA VERSION", font=("Arial", 9, "bold"), bg="#EDE9FE", fg=PURPLE, padx=8, pady=2)
        top_badge.pack(pady=(0, 5))

        tk.Label(card, text="KB Booking", font=("Arial", 24, "bold"), bg=WHITE, fg=NAVY).pack(pady=(2, 2))
        tk.Label(card, text="ระบบจองห้องประชุมและอุปกรณ์อัจฉริยะ", font=("Arial", 10), bg=WHITE, fg=TEXT_MUTED).pack(pady=(0, 16))

        tk.Label(card, text="เข้าสู่ระบบ", font=("Arial", 15, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(0, 10))

        # Username
        tk.Label(card, text="ชื่อผู้ใช้งาน (Username)", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(4, 2))
        self.entry_user = tk.Entry(card, font=("Arial", 11), bg="#F8FAFC", relief="solid", bd=1)
        self.entry_user.pack(fill="x", ipady=5, pady=(0, 10))
        self.entry_user.insert(0, "admin")

        # Password
        tk.Label(card, text="รหัสผ่าน (Password)", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(4, 2))
        self.entry_pass = tk.Entry(card, font=("Arial", 11), show="•", bg="#F8FAFC", relief="solid", bd=1)
        self.entry_pass.pack(fill="x", ipady=5, pady=(0, 16))
        self.entry_pass.insert(0, "24042564")
        self.entry_pass.bind("<Return>", lambda e: self.do_login())

        # Login button
        btn_login = tk.Button(
            card, text="เข้าสู่ระบบ (Login)", command=self.do_login,
            font=("Arial", 12, "bold"), bg=BLUE, fg=WHITE, activebackground="#1D4ED8", activeforeground=WHITE,
            relief="flat", cursor="hand2"
        )
        btn_login.pack(fill="x", ipady=7, pady=(0, 8))

        # Register button
        btn_reg = tk.Button(
            card, text="สมัครสมาชิกใหม่", command=self.open_register,
            font=("Arial", 10), bg=WHITE, fg=BLUE, activebackground="#F1F5F9",
            relief="solid", bd=1, cursor="hand2"
        )
        btn_reg.pack(fill="x", ipady=5, pady=(0, 10))

        hint_frame = tk.Frame(card, bg="#F1F5F9", padx=10, pady=6)
        hint_frame.pack(fill="x", pady=(5, 0))
        tk.Label(hint_frame, text="💡 บัญชีทดสอบในระบบ:", font=("Arial", 8, "bold"), bg="#F1F5F9", fg=TEXT).pack(anchor="w")
        tk.Label(hint_frame, text="• แอดมิน: admin / 24042564", font=("Arial", 8), bg="#F1F5F9", fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(hint_frame, text="• ผู้ใช้ทั่วไป: สมัครใหม่ได้ทันที", font=("Arial", 8), bg="#F1F5F9", fg=TEXT_MUTED).pack(anchor="w")

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
            # โหมด Offline Fallback สำหรับการทดสอบ
            if username == "admin" and password == "24042564":
                self.root.destroy()
                self.on_login_success(1, "admin", "admin")
                return
            elif username and password:
                self.root.destroy()
                self.on_login_success(999, username, "user")
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

        tk.Label(card, text="ยืนยันรหัสผ่าน:", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(5, 3))
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
                messagebox.showerror("รหัสผ่านไม่ตรงกัน", "รหัสผ่านและยืนยันรหัสผ่านต้องตรงกัน", parent=reg)
                return

            conn = get_connection()
            if not conn:
                messagebox.showinfo("สำเร็จ (Offline)", f"สร้างบัญชี {u} สำเร็จ!", parent=reg)
                reg.destroy()
                return

            try:
                cur = conn.cursor()
                cur.execute("SELECT id FROM users WHERE username = %s;", (u,))
                if cur.fetchone():
                    messagebox.showerror("ข้อผิดพลาด", "ชื่อผู้ใช้นี้มีอยู่ในระบบแล้ว", parent=reg)
                    cur.close()
                    conn.close()
                    return

                cur.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'user');", (u, p))
                conn.commit()
                cur.close()
                conn.close()

                messagebox.showinfo("สำเร็จ", "สมัครสมาชิกเรียบร้อยแล้ว! สามารถเข้าสู่ระบบได้ทันที", parent=reg)
                reg.destroy()
            except Exception as e:
                conn.rollback()
                conn.close()
                messagebox.showerror("Error", f"เกิดข้อผิดพลาด:\n{e}", parent=reg)

        tk.Button(
            card, text="ยืนยันการสมัคร", command=submit,
            font=("Arial", 11, "bold"), bg=GREEN, fg=WHITE, relief="flat", cursor="hand2"
        ).pack(fill="x", ipady=7)


# ==========================================
# 4. แอปพลิเคชันหลัก KB Booking (Beta)
# ==========================================
class MeetingRoomApp:
    def __init__(self, root, current_user):
        self.root = root
        self.current_user = current_user  # {"id": int, "username": str, "role": str}
        self.root.title(f"KB Booking (Beta) - ระบบจองห้องประชุม ({self.current_user['username']})")
        self.root.geometry("1260x830")
        self.root.minsize(1000, 720)
        self.root.configure(bg=BG)

        # ข้อมูลห้องประชุมและอุปกรณ์
        self.bookings = []
        self.rooms_data = {}        # {name: {"id": id, "capacity": cap, "description": desc}}
        self.equipment_stock = {}   # {name: total_stock}
        self.equipment_data = {}    # {name: {"id": id, "total_stock": stock, "description": desc}}
        self.equipment_bookings = []

        # ตัวแปรแบบฟอร์มการจองห้อง
        self.department = tk.StringVar()
        self.room = tk.StringVar()
        self.people = tk.StringVar(value="1")
        self.topic = tk.StringVar()
        self.selected_date = tk.StringVar(value=date.today().isoformat())
        self.start_time = tk.StringVar(value="09:00")
        self.end_time = tk.StringVar()

        # รายชื่อคณะ/หน่วยงาน
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

        self.year = date.today().year
        self.month = date.today().month

        self.set_style()
        self.load_rooms_from_db()
        self.load_equipment_from_db()
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

    # ================= ดึงข้อมูลจากฐานข้อมูล =================
    def load_rooms_from_db(self):
        """โหลดข้อมูลห้องประชุมจากฐานข้อมูล PostgreSQL"""
        conn = get_connection()
        if not conn:
            # Fallback หากไม่มี DB
            self.rooms_data = {
                "ห้องประชุม A": {"id": 1, "capacity": 8, "description": "ชั้น 2 - เหมาะสำหรับการประชุมกลุ่มย่อย"},
                "ห้องประชุม B": {"id": 2, "capacity": 16, "description": "ชั้น 3 - เหมาะสำหรับการประชุมทีม"},
                "ห้องประชุมใหญ่": {"id": 3, "capacity": 30, "description": "ชั้น 4 - รองรับการประชุมคณะ"},
                "ห้องสัมมนา": {"id": 4, "capacity": 50, "description": "ชั้น 5 - รองรับการอบรมสัมมนา"}
            }
            if not self.room.get() and self.rooms_data:
                self.room.set(list(self.rooms_data.keys())[0])
            return

        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, COALESCE(capacity, 10), COALESCE(description, '') FROM locations ORDER BY id;")
            rows = cur.fetchall()
            self.rooms_data = {row[1]: {"id": row[0], "capacity": row[2], "description": row[3]} for row in rows}
            cur.close()
            conn.close()

            if self.rooms_data and not self.room.get():
                self.room.set(list(self.rooms_data.keys())[0])
        except Exception as e:
            print("load_rooms_from_db error:", e)

    def load_equipment_from_db(self):
        """โหลดรายการคลังอุปกรณ์จากฐานข้อมูล PostgreSQL"""
        conn = get_connection()
        default_stock = {
            "โปรเจกเตอร์": {"id": 1, "total_stock": 5, "description": "ความคมชัด Full HD พร้อมรีโมท"},
            "ไมโครโฟน": {"id": 2, "total_stock": 10, "description": "ไมโครโฟนไร้สาย Wireless"},
            "ลำโพง": {"id": 3, "total_stock": 4, "description": "ลำโพงพกพาพร้อมแอมป์"},
            "โน้ตบุ๊ก": {"id": 4, "total_stock": 8, "description": "โน้ตบุ๊ก Windows 11 Core i5"},
            "สาย HDMI": {"id": 5, "total_stock": 10, "description": "สาย HDMI ความยาว 5 เมตร"},
            "ปลั๊กพ่วง": {"id": 6, "total_stock": 10, "description": "ปลั๊กพ่วงมาตรฐาน 5 ช่อง"}
        }
        if not conn:
            self.equipment_data = default_stock
            self.equipment_stock = {k: v["total_stock"] for k, v in default_stock.items()}
            return

        try:
            cur = conn.cursor()
            cur.execute("SELECT id, name, total_stock, COALESCE(description, '') FROM equipment ORDER BY id;")
            rows = cur.fetchall()
            cur.close()
            conn.close()

            if rows:
                self.equipment_data = {r[1]: {"id": r[0], "total_stock": r[2], "description": r[3]} for r in rows}
                self.equipment_stock = {r[1]: r[2] for r in rows}
            else:
                self.equipment_data = default_stock
                self.equipment_stock = {k: v["total_stock"] for k, v in default_stock.items()}
        except Exception as e:
            print("load_equipment_from_db error:", e)
            self.equipment_data = default_stock
            self.equipment_stock = {k: v["total_stock"] for k, v in default_stock.items()}

    def fetch_bookings_from_db(self):
        """ดึงรายการจองห้องประชุมทั้งหมด"""
        conn = get_connection()
        if not conn:
            return self.bookings
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
            return self.bookings

    def fetch_equipment_bookings_from_db(self):
        """ดึงรายการจองอุปกรณ์ทั้งหมด"""
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
                    eb.user_id,
                    COALESCE(eb.status, 'approved') AS status
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
                    "user_id": r[9],
                    "status": r[10]
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
        tk.Label(self.sidebar, text="KB Booking", font=("Arial", 22, "bold"), bg=NAVY, fg=WHITE).pack(pady=(22, 2))
        sub_frame = tk.Frame(self.sidebar, bg=NAVY)
        sub_frame.pack(pady=(0, 16))
        tk.Label(sub_frame, text="ระบบจองห้องประชุม", font=("Arial", 10), bg=NAVY, fg="#93C5FD").pack(side="left")
        tk.Label(sub_frame, text="BETA", font=("Arial", 8, "bold"), bg=PURPLE, fg=WHITE, padx=5, pady=1).pack(side="left", padx=5)

        # การ์ดแสดงผู้ใช้ที่ล็อกอินอยู่
        role_label = "ผู้ดูแลระบบ (Admin)" if self.current_user["role"] == "admin" else "ผู้ใช้งานทั่วไป"
        role_bg = "#3B82F6" if self.current_user["role"] == "admin" else "#10B981"

        user_card = tk.Frame(self.sidebar, bg="#1E293B", padx=12, pady=10)
        user_card.pack(fill="x", padx=12, pady=(0, 18))

        tk.Label(user_card, text=f"👤 {self.current_user['username']}", font=("Arial", 11, "bold"), bg="#1E293B", fg=WHITE).pack(anchor="w")
        tk.Label(user_card, text=role_label, font=("Arial", 9), bg=role_bg, fg=WHITE, padx=6, pady=1).pack(anchor="w", pady=(4, 0))

        # ปุ่มเมนู
        self.menu_button("🏠 หน้าหลัก", self.show_home)
        self.menu_button("📅 จองห้องประชุม", self.show_booking)
        self.menu_button("📦 จองอุปกรณ์", self.show_equipment_booking)
        self.menu_button("🏢 ข้อมูลห้องประชุม", self.show_rooms)

        # เมนูเฉพาะแอดมิน
        if self.current_user["role"] == "admin":
            self.menu_button("⚙️ จัดการการจอง (Admin)", self.show_admin_dashboard)

        spacer = tk.Frame(self.sidebar, bg=NAVY)
        spacer.pack(fill="both", expand=True)

        tk.Button(
            self.sidebar, text="🚪 ออกจากระบบ", command=self.logout,
            font=("Arial", 11), bg="#334155", fg=WHITE, activebackground=RED, activeforeground=WHITE,
            relief="flat", anchor="w", padx=20, pady=10, cursor="hand2"
        ).pack(fill="x", padx=12, pady=15)

        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)

    def menu_button(self, text, command):
        tk.Button(
            self.sidebar, text=text, command=command,
            font=("Arial", 11), bg=NAVY, fg=WHITE,
            activebackground=NAVY_HOVER, activeforeground=WHITE,
            relief="flat", anchor="w", padx=20, pady=11, cursor="hand2"
        ).pack(fill="x", padx=10, pady=2)

    def clear_page(self):
        for widget in self.main.winfo_children():
            widget.destroy()

    def page_title(self, title, subtitle=""):
        header = tk.Frame(self.main, bg=BG)
        header.pack(fill="x", padx=30, pady=(22, 10))
        tk.Label(header, text=title, font=("Arial", 20, "bold"), bg=BG, fg=NAVY).pack(anchor="w")
        if subtitle:
            tk.Label(header, text=subtitle, font=("Arial", 10), bg=BG, fg=TEXT_MUTED).pack(anchor="w", pady=(2, 0))

    def make_button(self, parent, text, command, color=GREEN):
        return tk.Button(
            parent, text=text, command=command,
            font=("Arial", 11, "bold"), bg=color, fg=WHITE,
            activebackground="#15803D", activeforeground=WHITE,
            relief="flat", cursor="hand2", padx=12, pady=7
        )

    def field_label(self, parent, text):
        tk.Label(
            parent, text=text, font=("Arial", 10, "bold"),
            bg=WHITE, fg=NAVY
        ).pack(anchor="w", pady=(8, 3))

    def logout(self):
        if messagebox.askyesno("ยืนยัน", "ต้องการออกจากระบบใช่หรือไม่?", parent=self.root):
            self.root.destroy()
            start_application()

    # ================= 1. หน้าหลัก (Home) =================
    def show_home(self):
        self.clear_page()
        self.page_title("หน้าหลัก", "ภาพรวมการจองห้องประชุมและอุปกรณ์ KB Booking (Beta)")

        self.fetch_bookings_from_db()
        self.fetch_equipment_bookings_from_db()

        today_str = date.today().isoformat()
        total_count = len(self.bookings)
        today_count = sum(1 for b in self.bookings if b["date"] == today_str)
        pending_count = sum(1 for b in self.bookings if b["status"] == "pending")
        eq_count = len(self.equipment_bookings)

        cards = tk.Frame(self.main, bg=BG)
        cards.pack(fill="x", padx=30, pady=(0, 15))

        self.make_card(cards, "การจองห้องทั้งหมด", total_count, BLUE)
        self.make_card(cards, "การจองห้องวันนี้", today_count, GREEN)
        self.make_card(cards, "ห้องรออนุมัติ", pending_count, AMBER)
        self.make_card(cards, "การจองอุปกรณ์", eq_count, PURPLE)

        table_header = tk.Frame(self.main, bg=BG)
        table_header.pack(fill="x", padx=30, pady=(10, 8))

        tk.Label(table_header, text="รายการจองห้องประชุมทั้งหมด", font=("Arial", 15, "bold"), bg=BG, fg=NAVY).pack(side="left")

        btn_box = tk.Frame(table_header, bg=BG)
        btn_box.pack(side="right")

        tk.Button(
            btn_box, text="🔄 รีเฟรช", command=self.show_home,
            font=("Arial", 10), bg=WHITE, fg=NAVY, relief="solid", bd=1, padx=10, pady=4, cursor="hand2"
        ).pack(side="left")

        frame = tk.Frame(self.main, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        columns = ("date", "time", "room", "user", "dept", "people", "topic", "status", "action")
        table = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

        headers = [
            ("date", "วันที่", 95),
            ("time", "เวลา", 105),
            ("room", "ห้องประชุม", 130),
            ("user", "ผู้จอง", 95),
            ("dept", "คณะ/หน่วยงาน", 160),
            ("people", "จำนวน", 65),
            ("topic", "หัวข้อประชุม", 170),
            ("status", "สถานะ", 110),
            ("action", "QR / ตรวจสอบ", 100)
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

        table.tag_configure("approved", foreground="#15803D")
        table.tag_configure("pending", foreground="#D97706")
        table.tag_configure("rejected", foreground="#DC2626")

        status_text_map = {
            "approved": "✅ อนุมัติแล้ว",
            "pending": "⏳ รออนุมัติ",
            "rejected": "❌ ปฏิเสธ"
        }

        self.table_booking_map = {}
        for b in sorted(self.bookings, key=lambda item: (item["date"], item["start"]), reverse=True):
            st = b["status"]
            st_display = status_text_map.get(st, st)
            item_id = table.insert("", "end", values=(
                b["date"],
                f"{b['start']} - {b['end']}",
                b["room"],
                b["username"],
                b["department"],
                f"{b['people']} คน" if b['people'] else "-",
                b["topic"],
                st_display,
                "🔍 ดู QR Code"
            ), tags=(st,))
            self.table_booking_map[item_id] = b

        def on_table_double_click(event):
            sel = table.selection()
            if sel and sel[0] in self.table_booking_map:
                b_info = self.table_booking_map[sel[0]]
                self.show_booking_qr_modal(b_info, is_equipment=False)

        table.bind("<Double-1>", on_table_double_click)

        if not self.bookings:
            tk.Label(self.main, text="ยังไม่มีรายการจองห้องประชุมในระบบ", bg=BG, fg=TEXT_MUTED, font=("Arial", 11)).pack(pady=10)

    def make_card(self, parent, title, value, color):
        card = tk.Frame(parent, bg=WHITE, padx=18, pady=14, highlightbackground=BORDER, highlightthickness=1)
        card.pack(side="left", fill="x", expand=True, padx=5)
        tk.Label(card, text=title, font=("Arial", 10), bg=WHITE, fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(card, text=str(value), font=("Arial", 22, "bold"), bg=WHITE, fg=color).pack(anchor="w", pady=(4, 0))

    # ================= 2. จองห้องประชุม (Room Booking) =================
    def show_booking(self):
        self.clear_page()
        self.page_title("จองห้องประชุม", "กรอกข้อมูลและเลือกวันที่กับเวลาที่ต้องการ (ห้ามเลือกย้อนหลังจากวันปัจจุบัน)")

        self.department.set("")
        if self.rooms_data:
            self.room.set(list(self.rooms_data.keys())[0])
        self.people.set("1")
        self.topic.set("")
        self.selected_date.set(date.today().isoformat())
        self.start_time.set("09:00")
        self.end_time.set("10:00")

        self.year = date.today().year
        self.month = date.today().month

        content = tk.Frame(self.main, bg=BG)
        content.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # ฝั่งซ้าย: ข้อมูลแบบฟอร์ม
        left = tk.Frame(content, bg=WHITE, padx=20, pady=18, highlightbackground=BORDER, highlightthickness=1, width=370)
        left.pack(side="left", fill="y", padx=(0, 15))
        left.pack_propagate(False)

        # ฝั่งขวา: ปฏิทินและเวลา
        right = tk.Frame(content, bg=WHITE, padx=20, pady=18, highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="ข้อมูลการจองห้อง", font=("Arial", 15, "bold"), bg=WHITE, fg=NAVY).pack(anchor="w")

        self.field_label(left, "คณะ / หน่วยงาน")
        ttk.Combobox(
            left, textvariable=self.department, values=self.departments,
            state="readonly", width=28
        ).pack(fill="x")

        self.field_label(left, "ห้องประชุม")
        self.room_box = ttk.Combobox(
            left, textvariable=self.room, values=list(self.rooms_data.keys()),
            state="readonly", width=28
        )
        self.room_box.pack(fill="x")
        self.room_box.bind("<<ComboboxSelected>>", self.room_changed)

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

        self.field_label(left, "หัวข้อการประชุม")
        tk.Entry(left, textvariable=self.topic, font=("Arial", 10), bg="#F8FAFC", relief="solid", bd=1).pack(fill="x", ipady=4)

        self.field_label(left, "วันที่เลือกจอง")
        self.date_label = tk.Label(left, text=self.selected_date.get(), font=("Arial", 12, "bold"), bg=WHITE, fg=BLUE)
        self.date_label.pack(anchor="w")

        # ป้ายแจ้งเตือนการเลือกวันย้อนหลัง
        tk.Label(left, text="* ไม่สามารถจองย้อนหลังจากวันปัจจุบันได้", font=("Arial", 8), bg=WHITE, fg=AMBER).pack(anchor="w", pady=(2, 0))

        self.make_button(left, "💾 ส่งคำขอจองห้อง (รับ QR)", self.save_booking, GREEN).pack(fill="x", pady=(18, 8))
        self.make_button(left, "ล้างข้อมูล", self.reset_form, "#64748B").pack(fill="x")

        # --- ฝั่งขวา: ปฏิทินและเวลา ---
        cal_hdr = tk.Frame(right, bg=WHITE)
        cal_hdr.pack(fill="x")
        tk.Label(cal_hdr, text="เลือกวันที่", font=("Arial", 14, "bold"), bg=WHITE, fg=NAVY).pack(side="left")
        tk.Label(cal_hdr, text="(เฉพาะตั้งแต่วันนี้เป็นต้นไป)", font=("Arial", 9), bg=WHITE, fg=TEXT_MUTED).pack(side="left", padx=8)

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
            right, text="ℹ️ ปุ่มสีแดงหมายถึงช่วงเวลาที่ถูกจองแล้ว (ตรวจสอบแบบเรียลไทม์)",
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
        self.end_time.set("10:00")

        self.year = date.today().year
        self.month = date.today().month

        self.date_label.config(text=self.selected_date.get())
        max_cap = self.rooms_data.get(self.room.get(), {}).get("capacity", 20)
        self.people_box.configure(to=max_cap)

        self.draw_calendar()
        self.draw_times()
        self.check_people()

    def draw_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        header = tk.Frame(self.calendar_frame, bg=WHITE)
        header.pack(fill="x", pady=(0, 6))

        tk.Button(
            header, text="◀ ก่อนหน้า", command=lambda: self.change_month(-1),
            font=("Arial", 9), bg=WHITE, fg=NAVY, relief="flat", cursor="hand2"
        ).pack(side="left")

        month_names = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
                       "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
        title_text = f"{month_names[self.month]} {self.year + 543}"
        tk.Label(header, text=title_text, font=("Arial", 11, "bold"), bg=WHITE, fg=NAVY).pack(side="left", expand=True)

        tk.Button(
            header, text="ถัดไป ▶", command=lambda: self.change_month(1),
            font=("Arial", 9), bg=WHITE, fg=NAVY, relief="flat", cursor="hand2"
        ).pack(side="right")

        table = tk.Frame(self.calendar_frame, bg=WHITE)
        table.pack()

        days = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]
        for c, day_name in enumerate(days):
            tk.Label(
                table, text=day_name, width=5, font=("Arial", 9, "bold"),
                bg="#F8FAFC", fg=NAVY, pady=4
            ).grid(row=0, column=c, padx=1, pady=1)

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(self.year, self.month)
        today = date.today()

        for r, week in enumerate(month_days):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(table, text="", width=5, bg=WHITE).grid(row=r + 1, column=c, padx=1, pady=1)
                else:
                    day_date = date(self.year, self.month, day)
                    is_past = day_date < today
                    is_selected = (self.selected_date.get() == day_date.isoformat())

                    if is_past:
                        # วันที่ย้อนหลัง: สีเทา ไม่สามารถกดได้
                        btn = tk.Label(
                            table, text=str(day), width=5,
                            font=("Arial", 9), bg="#F1F5F9", fg="#94A3B8",
                            pady=4
                        )
                    else:
                        bg_col = "#DBEAFE" if is_selected else WHITE
                        fg_col = BLUE if is_selected else TEXT
                        btn = tk.Button(
                            table, text=str(day), width=5,
                            font=("Arial", 9, "bold" if is_selected else "normal"),
                            bg=bg_col, fg=fg_col, relief="flat", cursor="hand2",
                            activebackground="#BFDBFE",
                            command=lambda d=day: self.pick_date(d)
                        )
                    btn.grid(row=r + 1, column=c, padx=1, pady=1)

    def change_month(self, amount):
        self.month += amount
        if self.month < 1:
            self.month = 12
            self.year -= 1
        elif self.month > 12:
            self.month = 1
            self.year += 1
        self.draw_calendar()

    def pick_date(self, day):
        """เลือกวันที่ พร้อมตรวจสอบไม่ให้เลือกย้อนหลัง"""
        picked = date(self.year, self.month, day)
        if picked < date.today():
            messagebox.showwarning("วันที่ไม่ถูกต้อง", "ไม่สามารถเลือกวันที่ย้อนหลังจากวันปัจจุบันได้", parent=self.root)
            return

        self.selected_date.set(picked.isoformat())
        self.date_label.config(text=self.selected_date.get())
        self.fetch_bookings_from_db()
        self.draw_calendar()
        self.draw_times()

    def time_is_booked(self, time_text, kind):
        current_room = self.room.get()
        current_date = self.selected_date.get()

        for booking in self.bookings:
            if booking["room"] == current_room and booking["date"] == current_date:
                if booking.get("status") == "rejected":
                    continue
                start = booking["start"]
                end = booking["end"]
                if kind == "start" and (start <= time_text < end):
                    return True
                if kind == "end" and (start < time_text <= end):
                    return True
        return False

    def draw_times(self):
        start_times = [f"{h:02d}:00" for h in range(7, 23)]
        end_times = [f"{h:02d}:00" for h in range(8, 24)]
        self.make_time_buttons(self.start_frame, start_times, "start")
        self.make_time_buttons(self.end_frame, end_times, "end")

    def make_time_buttons(self, parent, times, kind):
        for widget in parent.winfo_children():
            widget.destroy()

        cols = 8
        for i, time_text in enumerate(times):
            booked = self.time_is_booked(time_text, kind)
            is_start = (kind == "start" and self.start_time.get() == time_text)
            is_end = (kind == "end" and self.end_time.get() == time_text)

            if booked:
                color = RED
                text_color = WHITE
                cursor = "arrow"
            elif is_start:
                color = GREEN
                text_color = WHITE
                cursor = "hand2"
            elif is_end:
                color = BLUE
                text_color = WHITE
                cursor = "hand2"
            else:
                color = "#F1F5F9"
                text_color = TEXT
                cursor = "hand2"

            state = "disabled" if booked else "normal"
            btn = tk.Button(
                parent, text=time_text, width=6,
                font=("Arial", 9, "bold" if (is_start or is_end) else "normal"),
                bg=color, fg=text_color, activebackground="#E2E8F0",
                relief="flat", cursor=cursor, state=state,
                command=lambda t=time_text, k=kind: self.pick_time(t, k)
            )
            btn.grid(row=i // cols, column=i % cols, padx=2, pady=2)

    def pick_time(self, time_text, kind):
        if kind == "start":
            self.start_time.set(time_text)
            if self.end_time.get() and self.end_time.get() <= time_text:
                self.end_time.set("")
        else:
            if not self.start_time.get() or time_text <= self.start_time.get():
                messagebox.showwarning("เวลาไม่ถูกต้อง", "เวลาสิ้นสุดต้องมากกว่าเวลาเริ่ม", parent=self.root)
                return
            self.end_time.set(time_text)
        self.draw_times()

    def save_booking(self):
        """บันทึกการจองห้องประชุม พร้อมตรวจสอบวันย้อนหลัง และเปิดหน้า QR Code บัตรยืนยัน"""
        dept = self.department.get().strip()
        room_name = self.room.get()
        topic = self.topic.get().strip()
        b_date = self.selected_date.get()
        start = self.start_time.get()
        end = self.end_time.get()

        if not dept or not topic:
            messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณาเลือกคณะ/หน่วยงาน และกรอกหัวข้อการประชุม", parent=self.root)
            return

        # ตรวจสอบวันที่ไม่ให้ย้อนหลังเด็ดขาด
        try:
            book_dt = date.fromisoformat(b_date)
            if book_dt < date.today():
                messagebox.showwarning("วันที่ไม่ถูกต้อง", "ไม่สามารถจองย้อนหลังจากวันปัจจุบันได้", parent=self.root)
                return
        except ValueError:
            messagebox.showwarning("วันที่ไม่ถูกต้อง", "รูปแบบวันที่ไม่ถูกต้อง", parent=self.root)
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

        conn = get_connection()
        booking_id = len(self.bookings) + 1
        if conn:
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

                cur.execute("""
                    INSERT INTO bookings (user_id, location_id, booking_date, start_time, end_time, status, department, people, topic)
                    VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s, %s)
                    RETURNING id;
                """, (self.current_user["id"], loc_id, b_date, start, end, dept, people_val, topic))
                booking_id = cur.fetchone()[0]
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                if conn:
                    conn.rollback()
                    conn.close()
                print("Save booking DB error, fallback to memory:", e)

        new_booking = {
            "id": booking_id,
            "username": self.current_user["username"],
            "room": room_name,
            "date": b_date,
            "start": start,
            "end": end,
            "status": "pending",
            "department": dept,
            "people": people_val,
            "topic": topic,
            "user_id": self.current_user["id"],
            "location_id": loc_id
        }
        self.bookings.insert(0, new_booking)

        # เปิดหน้าต่าง QR Code สแกนตรวจสอบ
        self.show_booking_qr_modal(new_booking, is_equipment=False)
        self.show_home()

    # ================= 2.1 ระบบจองอุปกรณ์ (Equipment Booking) =================
    def show_equipment_booking(self):
        self.clear_page()
        self.page_title("จองอุปกรณ์", "เลือกอุปกรณ์และกรอกข้อมูลสำหรับการจอง (ห้ามเลือกย้อนหลังจากวันปัจจุบัน)")

        self.load_equipment_from_db()
        self.fetch_equipment_bookings_from_db()

        self.eq_department = tk.StringVar(value=self.departments[0] if self.departments else "")
        first_eq = list(self.equipment_stock.keys())[0] if self.equipment_stock else "โปรเจกเตอร์"
        self.eq_name = tk.StringVar(value=first_eq)
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

        self.field_label(left, "คณะ / หน่วยงาน")
        ttk.Combobox(
            left, textvariable=self.eq_department, values=self.departments,
            state="readonly", width=28
        ).pack(fill="x")

        self.field_label(left, "เลือกอุปกรณ์")
        equipment_box = ttk.Combobox(
            left, textvariable=self.eq_name, values=list(self.equipment_stock.keys()),
            state="readonly", width=28
        )
        equipment_box.pack(fill="x")
        equipment_box.bind("<<ComboboxSelected>>", lambda e: self.update_equipment_stock())

        self.stock_label = tk.Label(left, text="", bg=WHITE, fg=GREEN, font=("Arial", 9, "bold"))
        self.stock_label.pack(anchor="w", pady=(4, 2))

        self.field_label(left, "จำนวนที่ต้องการจอง (ชิ้น)")
        max_stock = self.equipment_stock.get(self.eq_name.get(), 10)
        self.eq_qty_spin = ttk.Spinbox(
            left, from_=1, to=max_stock, textvariable=self.eq_quantity, width=28
        )
        self.eq_qty_spin.pack(fill="x")

        self.field_label(left, "วันที่จอง (YYYY-MM-DD)")
        tk.Entry(left, textvariable=self.eq_date, font=("Arial", 10), bg="#F8FAFC", relief="solid", bd=1).pack(fill="x", ipady=3)
        tk.Label(left, text="* ต้องเป็นตั้งแต่วันปัจจุบันเป็นต้นไป", font=("Arial", 8), bg=WHITE, fg=AMBER).pack(anchor="w", pady=(1, 0))

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

        self.field_label(left, "วัตถุประสงค์การใช้งาน")
        tk.Entry(left, textvariable=self.eq_purpose, font=("Arial", 10), bg="#F8FAFC", relief="solid", bd=1).pack(fill="x", ipady=3)

        self.make_button(left, "💾 ส่งคำขอจองอุปกรณ์ (รับ QR)", self.save_equipment_booking, GREEN).pack(fill="x", pady=(18, 6))

        # ฝั่งขวา: คลังอุปกรณ์ + ตาราง
        top_right = tk.Frame(right, bg=WHITE)
        top_right.pack(fill="x", pady=(0, 8))

        tk.Label(top_right, text="📦 คลังอุปกรณ์ในระบบ", font=("Arial", 14, "bold"), bg=WHITE, fg=NAVY).pack(side="left")

        # ปุ่มจัดการคลังอุปกรณ์สำหรับ Admin
        if self.current_user["role"] == "admin":
            admin_eq_btn = tk.Button(
                top_right, text="⚙️ จัดการ/เพิ่มอุปกรณ์ (Admin)", command=self.open_manage_equipment_modal,
                font=("Arial", 9, "bold"), bg=PURPLE, fg=WHITE, relief="flat", padx=10, pady=3, cursor="hand2"
            )
            admin_eq_btn.pack(side="right")

        stock_cards = tk.Frame(right, bg=WHITE)
        stock_cards.pack(fill="x", pady=(0, 12))

        for eq, total in self.equipment_stock.items():
            card = tk.Frame(stock_cards, bg="#F1F5F9", padx=8, pady=6, highlightbackground="#E2E8F0", highlightthickness=1)
            card.pack(side="left", padx=3, pady=2, fill="x", expand=True)
            tk.Label(card, text=eq, font=("Arial", 9, "bold"), bg="#F1F5F9", fg=TEXT).pack()
            tk.Label(card, text=f"{total} ชิ้น", font=("Arial", 11, "bold"), bg="#F1F5F9", fg=BLUE).pack()

        table_hdr = tk.Frame(right, bg=WHITE)
        table_hdr.pack(fill="x", pady=(5, 6))

        tk.Label(table_hdr, text="📋 รายการจองอุปกรณ์", font=("Arial", 13, "bold"), bg=WHITE, fg=NAVY).pack(side="left")

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

        columns = ("id", "date", "time", "equipment", "quantity", "user", "department", "purpose", "status", "action")
        self.equipment_table = ttk.Treeview(right, columns=columns, show="headings", selectmode="browse")

        headers = [
            ("id", "ID", 40),
            ("date", "วันที่", 85),
            ("time", "เวลา", 95),
            ("equipment", "อุปกรณ์", 100),
            ("quantity", "จำนวน", 60),
            ("user", "ผู้ขอจอง", 90),
            ("department", "คณะ/หน่วยงาน", 130),
            ("purpose", "วัตถุประสงค์", 140),
            ("status", "สถานะ", 90),
            ("action", "QR / ตรวจสอบ", 90)
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

        self.equipment_table.tag_configure("approved", foreground="#15803D")
        self.equipment_table.tag_configure("pending", foreground="#D97706")
        self.equipment_table.tag_configure("rejected", foreground="#DC2626")

        self.update_equipment_stock()
        self.refresh_equipment_table()

        def on_eq_double_click(event):
            sel = self.equipment_table.selection()
            if sel and hasattr(self, "eq_table_map") and sel[0] in self.eq_table_map:
                eq_info = self.eq_table_map[sel[0]]
                self.show_booking_qr_modal(eq_info, is_equipment=True)

        self.equipment_table.bind("<Double-1>", on_eq_double_click)

    def update_equipment_stock(self):
        if not hasattr(self, "stock_label"):
            return
        name = self.eq_name.get()
        total = self.equipment_stock.get(name, 0)

        if hasattr(self, "eq_qty_spin"):
            self.eq_qty_spin.configure(to=max(1, total))

        b_date = self.eq_date.get().strip() if hasattr(self, "eq_date") else ""
        start = self.eq_start.get() if hasattr(self, "eq_start") else ""
        end = self.eq_end.get() if hasattr(self, "eq_end") else ""

        already_booked = 0
        if b_date and start and end:
            for b in self.equipment_bookings:
                if b["equipment"] == name and b["date"] == b_date and b.get("status") != "rejected":
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

        # ตรวจสอบวันที่ห้ามย้อนหลังจากวันปัจจุบัน
        try:
            b_dt = date.fromisoformat(booking_date)
            if b_dt < date.today():
                messagebox.showwarning("วันที่ไม่ถูกต้อง", "ไม่สามารถจองย้อนหลังจากวันปัจจุบันได้", parent=self.root)
                return
        except ValueError:
            messagebox.showwarning("วันที่ไม่ถูกต้อง", "กรุณากรอกวันที่ในรูปแบบ YYYY-MM-DD", parent=self.root)
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
            if b["equipment"] == equipment and b["date"] == booking_date and b.get("status") != "rejected":
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

        conn = get_connection()
        new_id = len(self.equipment_bookings) + 1
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO equipment_bookings (user_id, equipment_name, quantity, booking_date, start_time, end_time, department, purpose, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                    RETURNING id;
                """, (self.current_user["id"], equipment, quantity, booking_date, start, end, dept, purpose))
                new_id = cur.fetchone()[0]
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                if conn:
                    conn.rollback()
                    conn.close()
                print("Save equipment DB error:", e)

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
            "status": "pending",
            "user_id": self.current_user["id"]
        }
        self.equipment_bookings.insert(0, new_booking)

        self.eq_purpose.set("")
        self.refresh_equipment_table()
        self.update_equipment_stock()

        # เปิดหน้าต่าง QR Code สแกนตรวจสอบ
        self.show_booking_qr_modal(new_booking, is_equipment=True)

    def refresh_equipment_table(self):
        if not hasattr(self, "equipment_table"):
            return
        for item in self.equipment_table.get_children():
            self.equipment_table.delete(item)

        status_map = {
            "approved": "✅ อนุมัติ",
            "pending": "⏳ รออนุมัติ",
            "rejected": "❌ ปฏิเสธ"
        }

        self.eq_table_map = {}
        for b in sorted(self.equipment_bookings, key=lambda x: (x["date"], x["start"]), reverse=True):
            st = b.get("status", "approved")
            item_id = self.equipment_table.insert(
                "", "end",
                values=(
                    b.get("id", "-"),
                    b["date"],
                    f"{b['start']} - {b['end']}",
                    b["equipment"],
                    f"{b['quantity']} ชิ้น",
                    b.get("username", "-"),
                    b["department"],
                    b["purpose"],
                    status_map.get(st, st),
                    "🔍 ดู QR Code"
                ),
                tags=(st,)
            )
            self.eq_table_map[item_id] = b

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
                print("Delete equipment DB error:", e)

        self.equipment_bookings = [b for b in self.equipment_bookings if str(b.get("id")) != str(b_id)]
        messagebox.showinfo("สำเร็จ", f"ยกเลิกรายการจอง #{b_id} เรียบร้อยแล้ว", parent=self.root)
        self.refresh_equipment_table()
        self.update_equipment_stock()

    # ================= 3. ข้อมูลห้องประชุม & แอดมินแก้ไขข้อมูลห้อง =================
    def show_rooms(self):
        self.clear_page()
        self.page_title("ข้อมูลห้องประชุม", "รายละเอียดและความจุของแต่ละห้องประชุม พร้อมฟังก์ชันจัดการสำหรับแอดมิน")

        self.load_rooms_from_db()

        container = tk.Frame(self.main, bg=BG)
        container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # แถบคำสั่งเพิ่มห้องใหม่สำหรับแอดมิน
        if self.current_user["role"] == "admin":
            action_bar = tk.Frame(container, bg=BG)
            action_bar.pack(fill="x", pady=(0, 10))

            tk.Button(
                action_bar, text="➕ เพิ่มห้องประชุมใหม่ (Add Room)", command=self.open_add_room_modal,
                font=("Arial", 10, "bold"), bg=GREEN, fg=WHITE, relief="flat", padx=12, pady=6, cursor="hand2"
            ).pack(side="left")

            tk.Label(action_bar, text="💡 แอดมินสามารถคลิก '✏️ แก้ไข' หรือ '🗑️ ลบ' ในแต่ละห้องได้", font=("Arial", 9), bg=BG, fg=TEXT_MUTED).pack(side="left", padx=15)

        for room_name, info in self.rooms_data.items():
            card = tk.Frame(container, bg=WHITE, padx=20, pady=16, highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", pady=6)

            top_row = tk.Frame(card, bg=WHITE)
            top_row.pack(fill="x")

            tk.Label(top_row, text=f"🏢 {room_name}", font=("Arial", 15, "bold"), bg=WHITE, fg=NAVY).pack(side="left")
            cap_badge = tk.Label(top_row, text=f"รองรับสูงสุด {info['capacity']} คน", font=("Arial", 9, "bold"), bg="#DCFCE7", fg="#15803D", padx=8, pady=2)
            cap_badge.pack(side="left", padx=10)

            # ปุ่มแก้ไขและลบสำหรับแอดมิน
            if self.current_user["role"] == "admin":
                btn_box = tk.Frame(top_row, bg=WHITE)
                btn_box.pack(side="right")

                tk.Button(
                    btn_box, text="✏️ แก้ไข", command=lambda rn=room_name: self.open_edit_room_modal(rn),
                    font=("Arial", 9), bg="#EFF6FF", fg=BLUE, relief="solid", bd=1, padx=8, pady=2, cursor="hand2"
                ).pack(side="left", padx=(0, 5))

                tk.Button(
                    btn_box, text="🗑️ ลบ", command=lambda rn=room_name: self.delete_room(rn),
                    font=("Arial", 9), bg="#FEE2E2", fg=RED, relief="solid", bd=1, padx=8, pady=2, cursor="hand2"
                ).pack(side="left")

            desc = info["description"] if info["description"] else "ไม่มีรายละเอียดเพิ่มเติม"
            tk.Label(card, text=desc, font=("Arial", 10), bg=WHITE, fg=TEXT_MUTED).pack(anchor="w", pady=(6, 0))

    def open_add_room_modal(self):
        """หน้าต่างป๊อปอัปให้แอดมินเพิ่มห้องประชุมใหม่ลงฐานข้อมูล"""
        modal = tk.Toplevel(self.root)
        modal.title("เพิ่มห้องประชุมใหม่ - KB Booking")
        modal.geometry("450x380")
        modal.resizable(False, False)
        modal.configure(bg=BG)
        modal.grab_set()

        card = tk.Frame(modal, bg=WHITE, padx=25, pady=20, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(card, text="➕ เพิ่มห้องประชุมใหม่", font=("Arial", 15, "bold"), bg=WHITE, fg=NAVY).pack(anchor="w", pady=(0, 10))

        tk.Label(card, text="ชื่อห้องประชุม:", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(4, 2))
        entry_name = tk.Entry(card, font=("Arial", 10), bg="#F8FAFC", relief="solid", bd=1)
        entry_name.pack(fill="x", ipady=4, pady=(0, 8))

        tk.Label(card, text="ความจุผู้เข้าร่วมสูงสุด (คน):", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(4, 2))
        spin_cap = ttk.Spinbox(card, from_=1, to=500, width=15)
        spin_cap.set(15)
        spin_cap.pack(anchor="w", pady=(0, 8))

        tk.Label(card, text="รายละเอียด/ชั้น/อุปกรณ์ประจำห้อง:", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(4, 2))
        entry_desc = tk.Entry(card, font=("Arial", 10), bg="#F8FAFC", relief="solid", bd=1)
        entry_desc.pack(fill="x", ipady=4, pady=(0, 16))

        def save():
            name = entry_name.get().strip()
            desc = entry_desc.get().strip()
            try:
                cap = int(spin_cap.get())
            except ValueError:
                messagebox.showerror("Error", "กรุณากรอกความจุเป็นตัวเลข", parent=modal)
                return

            if not name:
                messagebox.showwarning("คำเตือน", "กรุณาระบุชื่อห้องประชุม", parent=modal)
                return

            conn = get_connection()
            new_id = len(self.rooms_data) + 1
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM locations WHERE name = %s;", (name,))
                    if cur.fetchone():
                        messagebox.showerror("ข้อผิดพลาด", f"มีห้องประชุม '{name}' ในระบบแล้ว", parent=modal)
                        cur.close()
                        conn.close()
                        return
                    cur.execute(
                        "INSERT INTO locations (name, capacity, description) VALUES (%s, %s, %s) RETURNING id;",
                        (name, cap, desc)
                    )
                    new_id = cur.fetchone()[0]
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as e:
                    if conn:
                        conn.rollback()
                        conn.close()
                    print("Add room DB error:", e)

            self.rooms_data[name] = {"id": new_id, "capacity": cap, "description": desc}
            messagebox.showinfo("สำเร็จ", f"เพิ่มห้อง '{name}' เรียบร้อยแล้ว!", parent=modal)
            modal.destroy()
            self.show_rooms()

        tk.Button(
            card, text="💾 บันทึกห้องใหม่สู่ฐานข้อมูล", command=save,
            font=("Arial", 11, "bold"), bg=GREEN, fg=WHITE, relief="flat", cursor="hand2"
        ).pack(fill="x", ipady=6)

    def open_edit_room_modal(self, room_name):
        """หน้าต่างป๊อปอัปให้แอดมินแก้ไขข้อมูลห้องประชุมและอัปเดตลงฐานข้อมูล"""
        info = self.rooms_data.get(room_name)
        if not info:
            return

        modal = tk.Toplevel(self.root)
        modal.title(f"แก้ไขข้อมูล - {room_name}")
        modal.geometry("450x380")
        modal.resizable(False, False)
        modal.configure(bg=BG)
        modal.grab_set()

        card = tk.Frame(modal, bg=WHITE, padx=25, pady=20, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(card, text=f"✏️ แก้ไขข้อมูลห้องประชุม", font=("Arial", 15, "bold"), bg=WHITE, fg=NAVY).pack(anchor="w", pady=(0, 10))

        tk.Label(card, text="ชื่อห้องประชุม:", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(4, 2))
        entry_name = tk.Entry(card, font=("Arial", 10), bg="#F8FAFC", relief="solid", bd=1)
        entry_name.pack(fill="x", ipady=4, pady=(0, 8))
        entry_name.insert(0, room_name)

        tk.Label(card, text="ความจุผู้เข้าร่วมสูงสุด (คน):", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(4, 2))
        spin_cap = ttk.Spinbox(card, from_=1, to=500, width=15)
        spin_cap.set(info["capacity"])
        spin_cap.pack(anchor="w", pady=(0, 8))

        tk.Label(card, text="รายละเอียด/ชั้น/อุปกรณ์ประจำห้อง:", font=("Arial", 10, "bold"), bg=WHITE, fg=TEXT).pack(anchor="w", pady=(4, 2))
        entry_desc = tk.Entry(card, font=("Arial", 10), bg="#F8FAFC", relief="solid", bd=1)
        entry_desc.pack(fill="x", ipady=4, pady=(0, 16))
        entry_desc.insert(0, info.get("description", ""))

        def update():
            new_name = entry_name.get().strip()
            new_desc = entry_desc.get().strip()
            try:
                new_cap = int(spin_cap.get())
            except ValueError:
                messagebox.showerror("Error", "กรุณากรอกความจุเป็นตัวเลข", parent=modal)
                return

            if not new_name:
                messagebox.showwarning("คำเตือน", "กรุณาระบุชื่อห้องประชุม", parent=modal)
                return

            conn = get_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE locations SET name = %s, capacity = %s, description = %s WHERE id = %s;",
                        (new_name, new_cap, new_desc, info["id"])
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as e:
                    if conn:
                        conn.rollback()
                        conn.close()
                    print("Update room DB error:", e)

            # อัปเดตโครงสร้างข้อมูลใน memory
            del self.rooms_data[room_name]
            self.rooms_data[new_name] = {"id": info["id"], "capacity": new_cap, "description": new_desc}
            messagebox.showinfo("สำเร็จ", "อัปเดตข้อมูลห้องประชุมในฐานข้อมูลเรียบร้อยแล้ว", parent=modal)
            modal.destroy()
            self.show_rooms()

        tk.Button(
            card, text="💾 บันทึกการแก้ไข", command=update,
            font=("Arial", 11, "bold"), bg=BLUE, fg=WHITE, relief="flat", cursor="hand2"
        ).pack(fill="x", ipady=6)

    def delete_room(self, room_name):
        info = self.rooms_data.get(room_name)
        if not info:
            return

        if not messagebox.askyesno("ยืนยันการลบ", f"คุณต้องการลบ '{room_name}' ออกจากฐานข้อมูลใช่หรือไม่?", parent=self.root):
            return

        conn = get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM locations WHERE id = %s;", (info["id"],))
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                conn.rollback()
                conn.close()
                print("Delete room DB error:", e)

        del self.rooms_data[room_name]
        messagebox.showinfo("สำเร็จ", f"ลบห้อง '{room_name}' เรียบร้อยแล้ว", parent=self.root)
        self.show_rooms()

    # ================= 3.1 แอดมินจัดการคลังอุปกรณ์ =================
    def open_manage_equipment_modal(self):
        """หน้าต่างป๊อปอัปให้แอดมินเพิ่ม/แก้ไข/ลบอุปกรณ์ และอัปเดตไปยังฐานข้อมูล"""
        modal = tk.Toplevel(self.root)
        modal.title("จัดการคลังอุปกรณ์ (Admin) - KB Booking")
        modal.geometry("620x520")
        modal.resizable(False, False)
        modal.configure(bg=BG)
        modal.grab_set()

        card = tk.Frame(modal, bg=WHITE, padx=22, pady=18, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(card, text="⚙️ จัดการคลังอุปกรณ์ (Admin)", font=("Arial", 15, "bold"), bg=WHITE, fg=NAVY).pack(anchor="w")
        tk.Label(card, text="เพิ่มอุปกรณ์ใหม่ หรือเลือกแก้ไขจำนวนสต็อกเพื่ออัปเดตสู่ฐานข้อมูล", font=("Arial", 9), bg=WHITE, fg=TEXT_MUTED).pack(anchor="w", pady=(0, 10))

        # ตารางแสดงอุปกรณ์ทั้งหมด
        tree_frame = tk.Frame(card, bg=WHITE)
        tree_frame.pack(fill="x", pady=(0, 15))

        tree = ttk.Treeview(tree_frame, columns=("id", "name", "stock", "desc"), show="headings", height=5)
        tree.heading("id", text="ID")
        tree.heading("name", text="ชื่ออุปกรณ์")
        tree.heading("stock", text="จำนวนสต็อก")
        tree.heading("desc", text="รายละเอียด")

        tree.column("id", width=40, anchor="center")
        tree.column("name", width=130)
        tree.column("stock", width=90, anchor="center")
        tree.column("desc", width=250)

        tree.pack(side="left", fill="x", expand=True)

        def populate_tree():
            for it in tree.get_children():
                tree.delete(it)
            for name, d in self.equipment_data.items():
                tree.insert("", "end", values=(d["id"], name, f"{d['total_stock']} ชิ้น", d.get("description", "-")))

        populate_tree()

        # ฟอร์มเพิ่ม/แก้ไข
        form_frame = tk.LabelFrame(card, text=" ฟอร์มเพิ่มหรือแก้ไขอุปกรณ์ ", font=("Arial", 10, "bold"), bg=WHITE, fg=NAVY, padx=12, pady=10)
        form_frame.pack(fill="x", pady=(0, 10))

        tk.Label(form_frame, text="ชื่ออุปกรณ์:", font=("Arial", 9, "bold"), bg=WHITE, fg=TEXT).grid(row=0, column=0, sticky="w", pady=4)
        entry_eq_name = tk.Entry(form_frame, font=("Arial", 10), bg="#F8FAFC", relief="solid", bd=1, width=22)
        entry_eq_name.grid(row=0, column=1, sticky="w", padx=6, pady=4)

        tk.Label(form_frame, text="จำนวนสต็อกทั้งหมด:", font=("Arial", 9, "bold"), bg=WHITE, fg=TEXT).grid(row=0, column=2, sticky="w", padx=(10, 0), pady=4)
        spin_eq_stock = ttk.Spinbox(form_frame, from_=0, to=200, width=10)
        spin_eq_stock.set(5)
        spin_eq_stock.grid(row=0, column=3, sticky="w", padx=6, pady=4)

        tk.Label(form_frame, text="รายละเอียด:", font=("Arial", 9, "bold"), bg=WHITE, fg=TEXT).grid(row=1, column=0, sticky="w", pady=4)
        entry_eq_desc = tk.Entry(form_frame, font=("Arial", 10), bg="#F8FAFC", relief="solid", bd=1, width=35)
        entry_eq_desc.grid(row=1, column=1, columnspan=3, sticky="ew", padx=6, pady=4)

        selected_eq_id = tk.StringVar(value="")

        def on_select(e):
            sel = tree.selection()
            if sel:
                vals = tree.item(sel[0])["values"]
                selected_eq_id.set(str(vals[0]))
                entry_eq_name.delete(0, "end")
                entry_eq_name.insert(0, vals[1])
                spin_eq_stock.set(int(str(vals[2]).replace(" ชิ้น", "")))
                entry_eq_desc.delete(0, "end")
                entry_eq_desc.insert(0, "" if vals[3] == "-" else vals[3])

        tree.bind("<<TreeviewSelect>>", on_select)

        btn_row = tk.Frame(card, bg=WHITE)
        btn_row.pack(fill="x")

        def add_equipment():
            name = entry_eq_name.get().strip()
            desc = entry_eq_desc.get().strip()
            try:
                stock = int(spin_eq_stock.get())
            except ValueError:
                messagebox.showerror("Error", "จำนวนสต็อกต้องเป็นตัวเลข", parent=modal)
                return

            if not name:
                messagebox.showwarning("คำเตือน", "กรุณากรอกชื่ออุปกรณ์", parent=modal)
                return

            conn = get_connection()
            new_id = len(self.equipment_stock) + 1
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO equipment (name, total_stock, description) VALUES (%s, %s, %s) RETURNING id;",
                        (name, stock, desc)
                    )
                    new_id = cur.fetchone()[0]
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as e:
                    if conn:
                        conn.rollback()
                        conn.close()
                    messagebox.showerror("Database Error", f"ไม่สามารถเพิ่มอุปกรณ์ได้:\n{e}", parent=modal)
                    return

            self.equipment_stock[name] = stock
            self.equipment_data[name] = {"id": new_id, "total_stock": stock, "description": desc}
            populate_tree()
            self.update_equipment_stock()
            messagebox.showinfo("สำเร็จ", f"เพิ่มอุปกรณ์ '{name}' เรียบร้อยแล้ว", parent=modal)

        def update_equipment():
            eq_id = selected_eq_id.get()
            if not eq_id:
                messagebox.showwarning("คำเตือน", "กรุณาคลิกเลือกอุปกรณ์จากตารางที่ต้องการแก้ไข", parent=modal)
                return

            name = entry_eq_name.get().strip()
            desc = entry_eq_desc.get().strip()
            try:
                stock = int(spin_eq_stock.get())
            except ValueError:
                messagebox.showerror("Error", "จำนวนสต็อกต้องเป็นตัวเลข", parent=modal)
                return

            conn = get_connection()
            if conn and eq_id.isdigit():
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE equipment SET name = %s, total_stock = %s, description = %s WHERE id = %s;",
                        (name, stock, desc, int(eq_id))
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as e:
                    if conn:
                        conn.rollback()
                        conn.close()
                    messagebox.showerror("Database Error", f"ไม่สามารถอัปเดตอุปกรณ์ได้:\n{e}", parent=modal)
                    return

            self.load_equipment_from_db()
            populate_tree()
            self.update_equipment_stock()
            messagebox.showinfo("สำเร็จ", f"อัปเดตอุปกรณ์ '{name}' สู่ฐานข้อมูลเรียบร้อยแล้ว", parent=modal)

        def delete_equipment():
            eq_id = selected_eq_id.get()
            if not eq_id:
                messagebox.showwarning("คำเตือน", "กรุณาคลิกเลือกอุปกรณ์จากตารางที่ต้องการลบ", parent=modal)
                return

            name = entry_eq_name.get().strip()
            if not messagebox.askyesno("ยืนยันการลบ", f"ต้องการลบอุปกรณ์ '{name}' ใช่หรือไม่?", parent=modal):
                return

            conn = get_connection()
            if conn and eq_id.isdigit():
                try:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM equipment WHERE id = %s;", (int(eq_id),))
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as e:
                    conn.rollback()
                    conn.close()
                    print("Delete eq DB error:", e)

            self.load_equipment_from_db()
            populate_tree()
            self.update_equipment_stock()
            messagebox.showinfo("สำเร็จ", f"ลบอุปกรณ์เรียบร้อยแล้ว", parent=modal)

        tk.Button(
            btn_row, text="➕ เพิ่มเป็นอุปกรณ์ใหม่", command=add_equipment,
            font=("Arial", 10, "bold"), bg=GREEN, fg=WHITE, relief="flat", padx=10, pady=6, cursor="hand2"
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_row, text="✏️ บันทึกการแก้ไข", command=update_equipment,
            font=("Arial", 10, "bold"), bg=BLUE, fg=WHITE, relief="flat", padx=10, pady=6, cursor="hand2"
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_row, text="🗑️ ลบอุปกรณ์", command=delete_equipment,
            font=("Arial", 10), bg="#FEE2E2", fg=RED, relief="flat", padx=10, pady=6, cursor="hand2"
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_row, text="ปิดหน้าต่าง", command=modal.destroy,
            font=("Arial", 10), bg="#64748B", fg=WHITE, relief="flat", padx=10, pady=6, cursor="hand2"
        ).pack(side="right")

    # ================= 4. QR Code ยืนยันการจอง และระบบสแกนตรวจสอบ =================
    def show_booking_qr_modal(self, booking_data, is_equipment=False):
        """หน้าต่างแสดงบัตรยืนยันการจองพร้อมรูปภาพ QR Code สำหรับให้แอดมินสแกนตรวจสอบ"""
        modal = tk.Toplevel(self.root)
        modal.title("บัตรยืนยันการจองและ QR Code - KB Booking")
        modal.geometry("520x680")
        modal.resizable(False, False)
        modal.configure(bg=BG)
        modal.grab_set()

        card = tk.Frame(modal, bg=WHITE, padx=25, pady=20, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        # Header Badge
        header_frame = tk.Frame(card, bg=WHITE)
        header_frame.pack(fill="x", pady=(0, 10))

        tk.Label(header_frame, text="KB Booking E-Ticket", font=("Arial", 16, "bold"), bg=WHITE, fg=NAVY).pack(side="left")
        status_tag = tk.Label(header_frame, text="✅ บันทึกสำเร็จ", font=("Arial", 9, "bold"), bg="#DCFCE7", fg="#15803D", padx=8, pady=2)
        status_tag.pack(side="right")

        # QR Code Canvas
        target_name = booking_data.get("equipment") if is_equipment else booking_data.get("room")
        qr_payload = f"KBBooking|ID:{booking_data.get('id')}|Type:{'EQ' if is_equipment else 'ROOM'}|Target:{target_name}|Date:{booking_data.get('date')}|Time:{booking_data.get('start')}-{booking_data.get('end')}|User:{booking_data.get('username')}"

        qr_box = tk.Frame(card, bg="#F8FAFC", padx=10, pady=10, highlightbackground="#E2E8F0", highlightthickness=1)
        qr_box.pack(pady=(0, 15))

        qr_canvas = tk.Canvas(qr_box, width=180, height=180, bg="white", highlightthickness=0)
        qr_canvas.pack()
        draw_qr_on_canvas(qr_canvas, qr_payload, size=180)

        tk.Label(qr_box, text=f"Scan Code: #B00{booking_data.get('id')}", font=("Arial", 9, "bold"), bg="#F8FAFC", fg=TEXT_MUTED).pack(pady=(4, 0))

        # ข้อมูลสรุปการจอง
        info_frame = tk.Frame(card, bg="#F8FAFC", padx=16, pady=12, highlightbackground="#E2E8F0", highlightthickness=1)
        info_frame.pack(fill="x", pady=(0, 15))

        def add_info_row(label, val):
            r = tk.Frame(info_frame, bg="#F8FAFC")
            r.pack(fill="x", pady=2)
            tk.Label(r, text=f"{label}:", font=("Arial", 9, "bold"), bg="#F8FAFC", fg=TEXT_MUTED, width=14, anchor="w").pack(side="left")
            tk.Label(r, text=str(val), font=("Arial", 9, "bold"), bg="#F8FAFC", fg=NAVY).pack(side="left")

        add_info_row("รหัสการจอง", f"#{booking_data.get('id')}")
        add_info_row("วันที่จอง", booking_data.get("date"))
        add_info_row("ช่วงเวลา", f"{booking_data.get('start')} - {booking_data.get('end')} น.")
        add_info_row("สถานที่/อุปกรณ์", f"{target_name} ({booking_data.get('quantity', '')} ชิ้น)" if is_equipment else target_name)
        add_info_row("ผู้ขอจอง", booking_data.get("username", self.current_user["username"]))
        add_info_row("คณะ/หน่วยงาน", booking_data.get("department", "-"))
        add_info_row("หัวข้อ/จุดประสงค์", booking_data.get("topic") or booking_data.get("purpose") or "-")

        # ปุ่มคำสั่งสำหรับแอดมินสแกนตรวจสอบ
        btn_action = tk.Button(
            card, text="🔍 สำหรับแอดมิน: สแกนตรวจสอบ / จับเวลาการใช้งาน",
            command=lambda: [modal.destroy(), self.open_admin_qr_verification_modal(booking_data, is_equipment)],
            font=("Arial", 11, "bold"), bg=BLUE, fg=WHITE, relief="flat", cursor="hand2", padx=10, pady=8
        )
        btn_action.pack(fill="x", pady=(0, 6))

        tk.Button(
            card, text="ปิดหน้าต่าง", command=modal.destroy,
            font=("Arial", 10), bg=WHITE, fg=TEXT_MUTED, relief="solid", bd=1, cursor="hand2", pady=5
        ).pack(fill="x")

    def open_admin_qr_verification_modal(self, booking_data, is_equipment=False):
        """หน้าต่างตรวจสอบ QR Code สำหรับแอดมิน: กดอนุมัติ/ปฏิเสธได้ทันที และมีตัวจับเวลาการใช้งาน (Live Timer)"""
        modal = tk.Toplevel(self.root)
        modal.title("แอดมินสแกนตรวจสอบ & ตัวจับเวลาการใช้งาน - KB Booking")
        modal.geometry("640x720")
        modal.resizable(False, False)
        modal.configure(bg=BG)
        modal.grab_set()

        card = tk.Frame(modal, bg=WHITE, padx=25, pady=20, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        # หัวข้อ
        top_bar = tk.Frame(card, bg=WHITE)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="📷 ผลการสแกนตรวจสอบ (Admin Verification)", font=("Arial", 15, "bold"), bg=WHITE, fg=NAVY).pack(side="left")
        status_var = tk.StringVar(value=booking_data.get("status", "pending"))

        def get_status_badge_text():
            s = status_var.get()
            if s == "approved":
                return "✅ อนุมัติแล้ว"
            if s == "rejected":
                return "❌ ปฏิเสธ"
            return "⏳ รออนุมัติ (Pending)"

        def get_status_color():
            s = status_var.get()
            if s == "approved":
                return "#15803D"
            if s == "rejected":
                return "#DC2626"
            return "#D97706"

        badge_label = tk.Label(top_bar, text=get_status_badge_text(), font=("Arial", 10, "bold"), bg="#FEF3C7", fg=get_status_color(), padx=10, pady=3)
        badge_label.pack(side="right")

        # กล่องข้อมูลที่สแกนได้
        info_box = tk.LabelFrame(card, text=" ข้อมูลที่ปรากฏใน QR Code ", font=("Arial", 10, "bold"), bg=WHITE, fg=NAVY, padx=15, pady=10)
        info_box.pack(fill="x", pady=(0, 15))

        target_name = booking_data.get("equipment") if is_equipment else booking_data.get("room")
        details = [
            ("🏷️ รหัสการจอง", f"#{booking_data.get('id')} ({'อุปกรณ์' if is_equipment else 'ห้องประชุม'})"),
            ("📅 วันที่จอง", booking_data.get("date")),
            ("⏰ ช่วงเวลา", f"{booking_data.get('start')} - {booking_data.get('end')} น."),
            ("🏢 สถานที่ / อุปกรณ์", f"{target_name} ({booking_data.get('quantity', '')} ชิ้น)" if is_equipment else target_name),
            ("👤 ผู้ขอจอง", booking_data.get("username", "-")),
            ("🏛️ คณะ / หน่วยงาน", booking_data.get("department", "-")),
            ("📝 หัวข้อ / วัตถุประสงค์", booking_data.get("topic") or booking_data.get("purpose") or "-")
        ]

        for i, (k, v) in enumerate(details):
            r = tk.Frame(info_box, bg=WHITE)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=f"{k}:", font=("Arial", 9, "bold"), bg=WHITE, fg=TEXT_MUTED, width=22, anchor="w").pack(side="left")
            tk.Label(r, text=str(v), font=("Arial", 9, "bold"), bg=WHITE, fg=TEXT).pack(side="left")

        # แถบปุ่ม อนุมัติ / ปฏิเสธ สำหรับแอดมิน
        action_row = tk.Frame(card, bg=WHITE)
        action_row.pack(fill="x", pady=(0, 15))

        def update_status(new_st):
            b_id = booking_data.get("id")
            conn = get_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    table_name = "equipment_bookings" if is_equipment else "bookings"
                    cur.execute(f"UPDATE {table_name} SET status = %s WHERE id = %s;", (new_st, b_id))
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as e:
                    if conn:
                        conn.rollback()
                        conn.close()
                    print("Update status DB error:", e)

            booking_data["status"] = new_st
            status_var.set(new_st)
            badge_label.config(text=get_status_badge_text(), fg=get_status_color())
            st_th = "อนุมัติ" if new_st == "approved" else "ปฏิเสธ"
            messagebox.showinfo("สำเร็จ", f"เปลี่ยนสถานะรายการ #{b_id} เป็น '{st_th}' เรียบร้อยแล้ว", parent=modal)

        tk.Button(
            action_row, text="✅ อนุมัติทันที (Approve)", command=lambda: update_status("approved"),
            font=("Arial", 10, "bold"), bg=GREEN, fg=WHITE, relief="flat", padx=12, pady=6, cursor="hand2"
        ).pack(side="left", padx=(0, 8), fill="x", expand=True)

        tk.Button(
            action_row, text="❌ ปฏิเสธคำขอ (Reject)", command=lambda: update_status("rejected"),
            font=("Arial", 10, "bold"), bg=RED, fg=WHITE, relief="flat", padx=12, pady=6, cursor="hand2"
        ).pack(side="left", fill="x", expand=True)

        # ================= ตัวจับเวลาการใช้งาน (Live Usage Timer) =================
        timer_box = tk.LabelFrame(card, text=" ⏱️ ระบบจับเวลาการใช้งานห้อง/อุปกรณ์ (Live Session Timer) ", font=("Arial", 10, "bold"), bg="#F8FAFC", fg=NAVY, padx=15, pady=12)
        timer_box.pack(fill="both", expand=True, pady=(0, 10))

        # ตัวแปรสถานะ Timer
        timer_seconds = tk.IntVar(value=0)
        timer_running = tk.BooleanVar(value=False)
        timer_job = [None]

        timer_display = tk.Label(timer_box, text="00:00:00", font=("Consolas", 32, "bold"), bg="#1E293B", fg="#38BDF8", padx=20, pady=8)
        timer_display.pack(pady=(4, 6))

        timer_status_label = tk.Label(timer_box, text="⚪ รอการเริ่มใช้งาน", font=("Arial", 10, "bold"), bg="#F8FAFC", fg=TEXT_MUTED)
        timer_status_label.pack(pady=(0, 8))

        def update_clock():
            if timer_running.get():
                timer_seconds.set(timer_seconds.get() + 1)
                sec = timer_seconds.get()
                h = sec // 3600
                m = (sec % 3600) // 60
                s = sec % 60
                timer_display.config(text=f"{h:02d}:{m:02d}:{s:02d}")
                timer_job[0] = modal.after(1000, update_clock)

        def start_timer():
            if not timer_running.get():
                timer_running.set(True)
                timer_status_label.config(text="🟢 กำลังนับเวลาใช้งานห้อง/อุปกรณ์...", fg=GREEN)
                update_clock()

        def pause_timer():
            if timer_running.get():
                timer_running.set(False)
                if timer_job[0]:
                    modal.after_cancel(timer_job[0])
                timer_status_label.config(text="⏸️ พักการนับเวลาชั่วคราว", fg=AMBER)

        def reset_timer():
            pause_timer()
            timer_seconds.set(0)
            timer_display.config(text="00:00:00")
            timer_status_label.config(text="⚪ รีเซ็ตเวลาเรียบร้อยแล้ว", fg=TEXT_MUTED)

        def finish_session():
            pause_timer()
            sec = timer_seconds.get()
            m = sec // 60
            timer_status_label.config(text=f"🏁 เสร็จสิ้นการใช้งาน! รวมเวลา: {m} นาที ({sec} วินาที)", fg=PURPLE)
            messagebox.showinfo("สิ้นสุดการใช้งาน", f"บันทึกการใช้งานห้อง/อุปกรณ์เสร็จสิ้น\nรวมเวลาใช้งาน: {m} นาที {sec % 60} วินาที", parent=modal)

        ctrl_row = tk.Frame(timer_box, bg="#F8FAFC")
        ctrl_row.pack(fill="x", pady=4)

        tk.Button(
            ctrl_row, text="▶️ เริ่มนับเวลา", command=start_timer,
            font=("Arial", 10, "bold"), bg=GREEN, fg=WHITE, relief="flat", padx=10, pady=5, cursor="hand2"
        ).pack(side="left", padx=3, fill="x", expand=True)

        tk.Button(
            ctrl_row, text="⏸️ พักเวลา", command=pause_timer,
            font=("Arial", 10), bg=AMBER, fg=WHITE, relief="flat", padx=10, pady=5, cursor="hand2"
        ).pack(side="left", padx=3, fill="x", expand=True)

        tk.Button(
            ctrl_row, text="🔄 รีเซ็ต", command=reset_timer,
            font=("Arial", 10), bg="#64748B", fg=WHITE, relief="flat", padx=10, pady=5, cursor="hand2"
        ).pack(side="left", padx=3, fill="x", expand=True)

        tk.Button(
            ctrl_row, text="🏁 จบการใช้งาน", command=finish_session,
            font=("Arial", 10, "bold"), bg=PURPLE, fg=WHITE, relief="flat", padx=10, pady=5, cursor="hand2"
        ).pack(side="left", padx=3, fill="x", expand=True)

        def on_close():
            if timer_job[0]:
                modal.after_cancel(timer_job[0])
            modal.destroy()

        modal.protocol("WM_DELETE_WINDOW", on_close)

    # ================= 5. หน้าจอจัดการการจอง (Admin Dashboard) =================
    def show_admin_dashboard(self):
        if self.current_user["role"] != "admin":
            messagebox.showerror("ไม่มีสิทธิ์", "หน้านี้สำหรับผู้ดูแลระบบเท่านั้น", parent=self.root)
            return

        self.clear_page()
        self.page_title("Admin Dashboard - จัดการการจอง", "อนุมัติหรือปฏิเสธคำขอ สแกนตรวจสอบ QR Code และจับเวลาการใช้งาน")

        self.fetch_bookings_from_db()

        action_bar = tk.Frame(self.main, bg=BG)
        action_bar.pack(fill="x", padx=30, pady=(0, 10))

        tk.Button(
            action_bar, text="📷 สแกน QR / ตรวจสอบคำขอที่เลือก", command=self.admin_scan_selected_booking,
            font=("Arial", 10, "bold"), bg=BLUE, fg=WHITE, relief="flat", padx=12, pady=6, cursor="hand2"
        ).pack(side="left", padx=(0, 10))

        frame = tk.Frame(self.main, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=30, pady=(0, 15))

        columns = ("id", "user", "room", "date", "time", "dept", "people", "topic", "status")
        self.admin_tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

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
            self.admin_tree.heading(col, text=title)
            self.admin_tree.column(col, width=width, anchor="center")

        self.admin_tree.column("topic", anchor="w")
        self.admin_tree.column("dept", anchor="w")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.admin_tree.yview)
        self.admin_tree.configure(yscrollcommand=scrollbar.set)

        self.admin_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.admin_tree.tag_configure("approved", foreground="#15803D")
        self.admin_tree.tag_configure("pending", foreground="#D97706")
        self.admin_tree.tag_configure("rejected", foreground="#DC2626")

        status_map = {
            "approved": "✅ อนุมัติแล้ว",
            "pending": "⏳ รออนุมัติ",
            "rejected": "❌ ปฏิเสธ"
        }

        self.admin_booking_map = {}
        for b in sorted(self.bookings, key=lambda x: x["id"], reverse=True):
            st = b["status"]
            item_id = self.admin_tree.insert("", "end", values=(
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
            self.admin_booking_map[item_id] = b

        self.admin_tree.bind("<Double-1>", lambda e: self.admin_scan_selected_booking())

        def change_booking_status(new_status):
            selected = self.admin_tree.selection()
            if not selected:
                messagebox.showwarning("คำเตือน", "กรุณาเลือกรายการจองที่ต้องการจัดการ", parent=self.root)
                return

            booking_id = self.admin_tree.item(selected[0])["values"][0]
            conn = get_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("UPDATE bookings SET status = %s WHERE id = %s;", (new_status, booking_id))
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as e:
                    if conn:
                        conn.rollback()
                        conn.close()
                    print("Update booking status DB error:", e)

            for b in self.bookings:
                if b["id"] == booking_id:
                    b["status"] = new_status
                    break

            status_label = "อนุมัติ" if new_status == "approved" else "ปฏิเสธ"
            messagebox.showinfo("สำเร็จ", f"เปลี่ยนสถานะรายการ ID #{booking_id} เป็น '{status_label}' เรียบร้อยแล้ว", parent=self.root)
            self.show_admin_dashboard()

        def delete_booking():
            selected = self.admin_tree.selection()
            if not selected:
                messagebox.showwarning("คำเตือน", "กรุณาเลือกรายการจองที่ต้องการลบ", parent=self.root)
                return

            booking_id = self.admin_tree.item(selected[0])["values"][0]
            if not messagebox.askyesno("ยืนยันการลบ", f"คุณต้องการลบรายการจอง ID #{booking_id} ใช่หรือไม่?", parent=self.root):
                return

            conn = get_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM bookings WHERE id = %s;", (booking_id,))
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception as e:
                    if conn:
                        conn.rollback()
                        conn.close()
                    print("Delete booking DB error:", e)

            self.bookings = [b for b in self.bookings if b["id"] != booking_id]
            messagebox.showinfo("สำเร็จ", f"ลบรายการจอง ID #{booking_id} เรียบร้อยแล้ว", parent=self.root)
            self.show_admin_dashboard()

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

    def admin_scan_selected_booking(self):
        """แอดมินคลิกตรวจสอบ QR Code และเปิดตัวจับเวลาสำหรับรายการที่เลือก"""
        if not hasattr(self, "admin_tree"):
            return
        selected = self.admin_tree.selection()
        if not selected:
            messagebox.showwarning("คำเตือน", "กรุณาคลิกเลือกรายการจองที่ต้องการตรวจสอบ", parent=self.root)
            return

        item_id = selected[0]
        if item_id in self.admin_booking_map:
            b_info = self.admin_booking_map[item_id]
            self.open_admin_qr_verification_modal(b_info, is_equipment=False)


# ==========================================
# 6. ฟังก์ชันเปิดโปรแกรม
# ==========================================
def open_main_app(user_id, username, role):
    main_root = tk.Tk()
    app = MeetingRoomApp(main_root, {"id": user_id, "username": username, "role": role})
    main_root.mainloop()

def start_application():
    init_db()
    login_root = tk.Tk()
    LoginWindow(login_root, open_main_app)
    login_root.mainloop()

if __name__ == "__main__":
    start_application()
