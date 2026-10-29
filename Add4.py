import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import calendar

# สีของโปรแกรม
BG = "#F4F7FB"
NAVY = "#172554"
GREEN = "#16A34A"
WHITE = "#FFFFFF"
TEXT = "#1F2937"
RED = "#DC2626"
BLUE = "#2563EB"


class MeetingRoomApp:

    def __init__(self, root):
        self.root = root
        self.root.title("MeetSpace - ระบบจองห้องประชุม")
        self.root.geometry("1200x800")
        self.root.minsize(950, 680)
        self.root.configure(bg=BG)

        # รายการจองห้องประชุม
        self.bookings = []

        # รายการจองอุปกรณ์
        self.equipment_bookings = []

        # จำนวนอุปกรณ์ทั้งหมด
        self.equipment_stock = {
            "โปรเจกเตอร์": 5,
            "ไมโครโฟน": 10,
            "ลำโพง": 4,
            "โน้ตบุ๊ก": 8,
            "สาย HDMI": 10,
            "ปลั๊กพ่วง": 10
        }

        self.department = tk.StringVar()
        self.room = tk.StringVar(value="ห้องประชุม A")
        self.people = tk.StringVar(value="1")
        self.topic = tk.StringVar()
        self.selected_date = tk.StringVar(
            value=date.today().isoformat()
        )
        self.start_time = tk.StringVar(value="09:00")
        self.end_time = tk.StringVar()

        self.capacities = {
            "ห้องประชุม A": 8,
            "ห้องประชุม B": 16,
            "ห้องประชุมใหญ่": 30,
            "ห้องสัมมนา": 50
        }

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
        self.create_menu()
        self.show_home()

    # ตั้งค่ารูปแบบ
    def set_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TCombobox",
            padding=6,
            fieldbackground=WHITE,
            background=WHITE
        )

        style.configure(
            "TSpinbox",
            padding=5,
            fieldbackground=WHITE,
            background=WHITE
        )

    # สร้างเมนู
    def create_menu(self):
        self.sidebar = tk.Frame(
            self.root, bg=NAVY, width=220
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="KB Booking",
            font=("Arial", 23, "bold"),
            bg=NAVY, fg=WHITE
        ).pack(pady=(30, 5))

        tk.Label(
            self.sidebar,
            text="ระบบจองห้องประชุม",
            font=("Arial", 10),
            bg=NAVY, fg=WHITE
        ).pack(pady=(0, 25))

        self.menu_button("หน้าหลัก", self.show_home)
        self.menu_button("จองห้องประชุม", self.show_booking)
        self.menu_button(
            "จองอุปกรณ์", self.show_equipment_booking
        )
        self.menu_button("ข้อมูลห้องประชุม", self.show_rooms)

        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)

    def menu_button(self, text, command):
        tk.Button(
            self.sidebar,
            text=text,
            command=command,
            font=("Arial", 12),
            bg=NAVY, fg=WHITE,
            activebackground="#334155",
            activeforeground=WHITE,
            relief="flat",
            anchor="w",
            padx=25, pady=14
        ).pack(fill="x", padx=10, pady=3)

    def clear_page(self):
        for widget in self.main.winfo_children():
            widget.destroy()

    def page_title(self, title, subtitle=""):
        tk.Label(
            self.main,
            text=title,
            font=("Arial", 24, "bold"),
            bg=BG, fg=NAVY
        ).pack(anchor="w", padx=30, pady=(25, 5))

        if subtitle:
            tk.Label(
                self.main,
                text=subtitle,
                font=("Arial", 11),
                bg=BG, fg="#64748B"
            ).pack(anchor="w", padx=32, pady=(0, 20))

    def make_button(self, parent, text, command, color=GREEN):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 11, "bold"),
            bg=color, fg=WHITE,
            activeforeground=WHITE,
            relief="flat",
            padx=12, pady=8
        )

    def field_label(self, parent, text):
        tk.Label(
            parent,
            text=text,
            font=("Arial", 11, "bold"),
            bg=WHITE, fg=TEXT
        ).pack(anchor="w", pady=(8, 5))

    # ---------------- หน้าหลัก ----------------

    def show_home(self):
        self.clear_page()
        self.page_title(
            "หน้าหลัก",
            "ภาพรวมการจองห้องประชุม MeetSpace"
        )

        today = date.today().isoformat()

        today_count = sum(
            1 for booking in self.bookings
            if booking["date"] == today
        )

        cards = tk.Frame(self.main, bg=BG)
        cards.pack(fill="x", padx=30)

        self.make_card(
            cards, "การจองทั้งหมด",
            len(self.bookings), BLUE
        )

        self.make_card(
            cards, "การจองวันนี้",
            today_count, GREEN
        )

        self.make_card(
            cards, "จำนวนห้องประชุม",
            len(self.capacities), "#7C3AED"
        )

        tk.Label(
            self.main,
            text="รายการจองห้องประชุม",
            font=("Arial", 16, "bold"),
            bg=BG, fg=NAVY
        ).pack(anchor="w", padx=30, pady=(25, 10))

        frame = tk.Frame(self.main, bg=WHITE)
        frame.pack(
            fill="both", expand=True,
            padx=30, pady=(0, 20)
        )

        columns = (
            "date", "time", "room",
            "department", "people", "topic"
        )

        table = ttk.Treeview(
            frame, columns=columns, show="headings"
        )

        headers = [
            ("date", "วันที่", 100),
            ("time", "เวลา", 130),
            ("room", "ห้องประชุม", 140),
            ("department", "คณะ/หน่วยงาน", 190),
            ("people", "จำนวนคน", 80),
            ("topic", "หัวข้อประชุม", 220)
        ]

        for column, title, width in headers:
            table.heading(column, text=title)
            table.column(
                column, width=width, anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            frame, orient="vertical", command=table.yview
        )
        table.configure(yscrollcommand=scrollbar.set)

        table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for booking in sorted(
            self.bookings,
            key=lambda item: (item["date"], item["start"])
        ):
            table.insert("", "end", values=(
                booking["date"],
                booking["start"] + " - " + booking["end"],
                booking["room"],
                booking["department"],
                booking["people"],
                booking["topic"]
            ))

        if not self.bookings:
            tk.Label(
                self.main,
                text="ยังไม่มีรายการจองห้องประชุม",
                bg=BG, fg="#64748B",
                font=("Arial", 11)
            ).pack(pady=10)

    def make_card(self, parent, title, value, color):
        card = tk.Frame(
            parent, bg=WHITE,
            highlightbackground="#DCE3EC",
            highlightthickness=1
        )
        card.pack(
            side="left", fill="x",
            expand=True, padx=5
        )

        tk.Label(
            card, text=title,
            font=("Arial", 11),
            bg=WHITE, fg="#64748B"
        ).pack(anchor="w", padx=15, pady=(12, 5))

        tk.Label(
            card, text=str(value),
            font=("Arial", 24, "bold"),
            bg=WHITE, fg=color
        ).pack(anchor="w", padx=15, pady=(0, 12))

    # ---------------- หน้าจองห้องประชุม ----------------

    def show_booking(self):
        self.clear_page()
        self.page_title(
            "จองห้องประชุม",
            "กรอกข้อมูลและเลือกวันที่กับเวลาที่ต้องการ"
        )

        self.department.set("")
        self.room.set("ห้องประชุม A")
        self.people.set("1")
        self.topic.set("")
        self.selected_date.set(date.today().isoformat())
        self.start_time.set("09:00")
        self.end_time.set("")

        self.year = date.today().year
        self.month = date.today().month

        content = tk.Frame(self.main, bg=BG)
        content.pack(
            fill="both", expand=True, padx=30
        )

        left = tk.Frame(
            content, bg=WHITE, padx=18, pady=15
        )
        left.pack(side="left", fill="y", padx=(0, 15))

        right = tk.Frame(
            content, bg=WHITE, padx=18, pady=15
        )
        right.pack(side="left", fill="both", expand=True)

        tk.Label(
            left, text="ข้อมูลการจอง",
            font=("Arial", 15, "bold"),
            bg=WHITE, fg=NAVY
        ).pack(anchor="w")

        self.field_label(left, "คณะ/หน่วยงาน")

        ttk.Combobox(
            left,
            textvariable=self.department,
            values=self.departments,
            state="readonly",
            width=28
        ).pack(fill="x")

        self.field_label(left, "ห้องประชุม")

        self.room_box = ttk.Combobox(
            left,
            textvariable=self.room,
            values=list(self.capacities.keys()),
            state="readonly",
            width=28
        )
        self.room_box.pack(fill="x")
        self.room_box.bind(
            "<<ComboboxSelected>>", self.room_changed
        )

        self.field_label(left, "จำนวนผู้เข้าร่วม (คน)")

        self.people_box = ttk.Spinbox(
            left, from_=1,
            to=self.capacities[self.room.get()],
            textvariable=self.people,
            width=28
        )
        self.people_box.pack(fill="x")

        self.capacity_label = tk.Label(
            left, text="",
            font=("Arial", 9), bg=WHITE
        )
        self.capacity_label.pack(
            anchor="w", pady=(5, 0)
        )

        self.people.trace_add("write", self.check_people)

        self.field_label(left, "หัวข้อประชุม")

        tk.Entry(
            left, textvariable=self.topic, width=30
        ).pack(fill="x")

        self.field_label(left, "วันที่จอง")

        self.date_label = tk.Label(
            left,
            text=self.selected_date.get(),
            font=("Arial", 11, "bold"),
            bg=WHITE, fg=BLUE
        )
        self.date_label.pack(anchor="w")

        self.make_button(
            left, "บันทึกการจอง", self.save_booking
        ).pack(fill="x", pady=(20, 8))

        self.make_button(
            left, "ล้างข้อมูล", self.reset_form, "#64748B"
        ).pack(fill="x")

        tk.Label(
            right, text="เลือกวันที่",
            font=("Arial", 15, "bold"),
            bg=WHITE, fg=NAVY
        ).pack(anchor="w")

        self.calendar_frame = tk.Frame(right, bg=WHITE)
        self.calendar_frame.pack(fill="x", pady=8)
        self.draw_calendar()

        tk.Label(
            right, text="เวลาเริ่ม",
            font=("Arial", 11, "bold"),
            bg=WHITE, fg=NAVY
        ).pack(anchor="w")

        tk.Label(
            right, textvariable=self.start_time,
            bg=WHITE, fg=GREEN
        ).pack(anchor="w")

        self.start_frame = tk.Frame(right, bg=WHITE)
        self.start_frame.pack(fill="x", pady=5)

        tk.Label(
            right, text="เวลาสิ้นสุด",
            font=("Arial", 11, "bold"),
            bg=WHITE, fg=NAVY
        ).pack(anchor="w")

        tk.Label(
            right, textvariable=self.end_time,
            bg=WHITE, fg=GREEN
        ).pack(anchor="w")

        self.end_frame = tk.Frame(right, bg=WHITE)
        self.end_frame.pack(fill="x", pady=5)

        tk.Label(
            right,
            text="สีแดงหมายถึงเวลาที่ถูกจองแล้ว",
            font=("Arial", 9),
            bg=WHITE, fg=RED
        ).pack(anchor="w", pady=5)

        self.draw_times()
        self.check_people()

    def check_people(self, *args):
        if not hasattr(self, "people_box"):
            return

        try:
            people = int(self.people.get())
        except (ValueError, tk.TclError):
            people = 0

        maximum = self.capacities[self.room.get()]

        if people < 1:
            self.people_box.configure(foreground=RED)
            self.capacity_label.config(
                text="กรุณากรอกอย่างน้อย 1 คน", fg=RED
            )
        elif people > maximum:
            self.people_box.configure(foreground=RED)
            self.capacity_label.config(
                text=f"เกินความจุ! ห้องนี้รับได้ {maximum} คน",
                fg=RED
            )
        else:
            self.people_box.configure(foreground=TEXT)
            self.capacity_label.config(
                text=f"ห้องนี้รองรับสูงสุด {maximum} คน",
                fg=GREEN
            )

    def room_changed(self, event=None):
        maximum = self.capacities[self.room.get()]
        self.people_box.configure(to=maximum)

        try:
            people = int(self.people.get())
        except (ValueError, tk.TclError):
            people = 1

        if people < 1 or people > maximum:
            self.people.set("1")

        self.end_time.set("")
        self.draw_times()
        self.check_people()

    def reset_form(self):
        self.department.set("")
        self.room.set("ห้องประชุม A")
        self.people.set("1")
        self.topic.set("")
        self.selected_date.set(date.today().isoformat())
        self.start_time.set("09:00")
        self.end_time.set("")

        self.year = date.today().year
        self.month = date.today().month

        self.date_label.config(text=self.selected_date.get())
        self.people_box.configure(
            to=self.capacities["ห้องประชุม A"]
        )

        self.draw_calendar()
        self.draw_times()
        self.check_people()

    # ---------------- ปฏิทิน ----------------

    def draw_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        header = tk.Frame(self.calendar_frame, bg=WHITE)
        header.pack(fill="x")

        self.make_button(
            header, "<", lambda: self.change_month(-1), "#64748B"
        ).pack(side="left")

        month_name = calendar.month_name[self.month]

        tk.Label(
            header,
            text=f"{month_name} {self.year}",
            font=("Arial", 12, "bold"),
            bg=WHITE, fg=NAVY
        ).pack(side="left", expand=True)

        self.make_button(
            header, ">", lambda: self.change_month(1), "#64748B"
        ).pack(side="right")

        grid = tk.Frame(self.calendar_frame, bg=WHITE)
        grid.pack(fill="x", pady=5)

        weekdays = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]

        for col, day_name in enumerate(weekdays):
            tk.Label(
                grid, text=day_name,
                bg=WHITE, fg="#64748B", width=4
            ).grid(row=0, column=col)

        weeks = calendar.monthcalendar(self.year, self.month)

        for row, week in enumerate(weeks, start=1):
            for col, day in enumerate(week):
                if day == 0:
                    continue

                date_text = (
                    f"{self.year:04d}-{self.month:02d}-{day:02d}"
                )

                selected = self.selected_date.get() == date_text

                tk.Button(
                    grid,
                    text=str(day),
                    width=3,
                    bg=GREEN if selected else "#F1F5F9",
                    fg=WHITE if selected else TEXT,
                    relief="flat",
                    command=lambda d=day: self.pick_date(d)
                ).grid(row=row, column=col, padx=2, pady=2)

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
        self.selected_date.set(
            f"{self.year:04d}-{self.month:02d}-{day:02d}"
        )

        self.date_label.config(text=self.selected_date.get())
        self.end_time.set("")
        self.draw_calendar()
        self.draw_times()

    # ---------------- ตรวจสอบเวลาจองห้อง ----------------

    def time_is_booked(self, time_text, kind):
        for booking in self.bookings:
            if booking["room"] != self.room.get():
                continue

            if booking["date"] != self.selected_date.get():
                continue

            start = booking["start"]
            end = booking["end"]

            if kind == "start":
                if start <= time_text < end:
                    return True
            else:
                if start < time_text <= end:
                    return True

        return False

    def draw_times(self):
        if not hasattr(self, "start_frame"):
            return

        for widget in self.start_frame.winfo_children():
            widget.destroy()

        for widget in self.end_frame.winfo_children():
            widget.destroy()

        times = [f"{hour:02d}:00" for hour in range(7, 23)]

        self.make_time_buttons(self.start_frame, times, "start")
        self.make_time_buttons(self.end_frame, times, "end")

    def make_time_buttons(self, parent, times, kind):
        selected_time = (
            self.start_time.get()
            if kind == "start"
            else self.end_time.get()
        )

        for index, time_text in enumerate(times):
            booked = self.time_is_booked(time_text, kind)

            invalid_end = (
                kind == "end"
                and time_text <= self.start_time.get()
            )

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
                parent,
                text=time_text,
                bg=color,
                fg=text_color,
                disabledforeground=RED if booked else "#9CA3AF",
                relief="flat",
                state=state,
                command=lambda t=time_text, k=kind:
                    self.pick_time(t, k)
            ).grid(
                row=index // 6,
                column=index % 6,
                padx=2, pady=2, sticky="ew"
            )

        for col in range(6):
            parent.columnconfigure(col, weight=1)

    def pick_time(self, time_text, kind):
        if kind == "start":
            if self.time_is_booked(time_text, "start"):
                messagebox.showwarning(
                    "เวลาไม่ว่าง", "ช่วงเวลานี้ถูกจองแล้ว"
                )
                return

            self.start_time.set(time_text)
            self.end_time.set("")

        else:
            if time_text <= self.start_time.get():
                messagebox.showwarning(
                    "เวลาไม่ถูกต้อง",
                    "เวลาสิ้นสุดต้องมากกว่าเวลาเริ่ม"
                )
                return

            if self.time_is_booked(time_text, "end"):
                messagebox.showwarning(
                    "เวลาไม่ว่าง",
                    "เวลานี้ไม่สามารถใช้เป็นเวลาสิ้นสุดได้"
                )
                return

            self.end_time.set(time_text)

        self.draw_times()

    # ---------------- บันทึกการจองห้อง ----------------

    def save_booking(self):
        department = self.department.get()
        room = self.room.get()
        topic = self.topic.get().strip()
        people_text = self.people.get()
        booking_date = self.selected_date.get()
        start = self.start_time.get()
        end = self.end_time.get()

        if not department or not topic:
            messagebox.showwarning(
                "ข้อมูลไม่ครบ",
                "กรุณาเลือกคณะ/หน่วยงานและกรอกหัวข้อประชุม"
            )
            return

        try:
            people = int(people_text)
        except ValueError:
            messagebox.showwarning(
                "จำนวนคนไม่ถูกต้อง",
                "กรุณากรอกจำนวนผู้เข้าร่วมเป็นตัวเลข"
            )
            return

        maximum = self.capacities[room]

        if people < 1 or people > maximum:
            self.check_people()
            messagebox.showwarning(
                "จำนวนคนไม่ถูกต้อง",
                f"{room} รองรับได้ 1 ถึง {maximum} คน"
            )
            return

        if not start or not end or end <= start:
            messagebox.showwarning(
                "เวลาไม่ถูกต้อง",
                "กรุณาเลือกเวลาเริ่มและเวลาสิ้นสุดให้ถูกต้อง"
            )
            return

        for booking in self.bookings:
            same_room = booking["room"] == room
            same_date = booking["date"] == booking_date

            overlap = (
                start < booking["end"]
                and end > booking["start"]
            )

            if same_room and same_date and overlap:
                messagebox.showerror(
                    "เวลาซ้ำ",
                    "ห้องนี้มีการจองในช่วงเวลาดังกล่าวแล้ว"
                )
                return

        new_booking = {
            "date": booking_date,
            "start": start,
            "end": end,
            "room": room,
            "department": department,
            "people": people,
            "topic": topic
        }

        self.bookings.append(new_booking)

        messagebox.showinfo(
            "จองสำเร็จ",
            f"จอง {room} สำเร็จ\n"
            f"วันที่ {booking_date}\n"
            f"เวลา {start} - {end}"
        )

        self.show_home()

    # ---------------- ระบบจองอุปกรณ์ ----------------

    def show_equipment_booking(self):
        self.clear_page()
        self.page_title(
            "จองอุปกรณ์",
            "เลือกอุปกรณ์และกรอกข้อมูลสำหรับการจอง"
        )

        self.eq_department = tk.StringVar()
        self.eq_name = tk.StringVar(value="โปรเจกเตอร์")
        self.eq_quantity = tk.StringVar(value="1")
        self.eq_date = tk.StringVar(value=date.today().isoformat())
        self.eq_start = tk.StringVar(value="09:00")
        self.eq_end = tk.StringVar(value="10:00")
        self.eq_purpose = tk.StringVar()

        form = tk.Frame(self.main, bg=WHITE, padx=25, pady=20)
        form.pack(fill="x", padx=30, pady=10)

        self.field_label(form, "คณะ/หน่วยงาน")
        ttk.Combobox(
            form,
            textvariable=self.eq_department,
            values=self.departments,
            state="readonly",
            width=40
        ).pack(fill="x")

        self.field_label(form, "เลือกอุปกรณ์")
        equipment_box = ttk.Combobox(
            form,
            textvariable=self.eq_name,
            values=list(self.equipment_stock.keys()),
            state="readonly",
            width=40
        )
        equipment_box.pack(fill="x")
        equipment_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.update_equipment_stock()
        )

        self.stock_label = tk.Label(
            form, text="",
            bg=WHITE, fg=GREEN,
            font=("Arial", 10)
        )
        self.stock_label.pack(anchor="w", pady=5)

        self.field_label(form, "จำนวนที่ต้องการจอง")
        ttk.Spinbox(
            form,
            from_=1,
            to=max(self.equipment_stock.values()),
            textvariable=self.eq_quantity,
            width=40
        ).pack(fill="x")

        self.field_label(form, "วันที่จอง (YYYY-MM-DD)")
        tk.Entry(
            form, textvariable=self.eq_date
        ).pack(fill="x")

        self.field_label(form, "เวลาเริ่ม (HH:MM)")
        ttk.Combobox(
            form,
            textvariable=self.eq_start,
            values=[f"{h:02d}:00" for h in range(7, 23)],
            state="readonly"
        ).pack(fill="x")

        self.field_label(form, "เวลาสิ้นสุด (HH:MM)")
        ttk.Combobox(
            form,
            textvariable=self.eq_end,
            values=[f"{h:02d}:00" for h in range(8, 24)],
            state="readonly"
        ).pack(fill="x")

        self.field_label(form, "วัตถุประสงค์")
        tk.Entry(
            form, textvariable=self.eq_purpose
        ).pack(fill="x")

        self.make_button(
            form, "บันทึกการจองอุปกรณ์",
            self.save_equipment_booking
        ).pack(fill="x", pady=(20, 5))

        self.update_equipment_stock()

        tk.Label(
            self.main,
            text="รายการจองอุปกรณ์",
            font=("Arial", 16, "bold"),
            bg=BG, fg=NAVY
        ).pack(anchor="w", padx=30, pady=(15, 5))

        columns = (
            "date", "time", "equipment",
            "quantity", "department", "purpose"
        )

        self.equipment_table = ttk.Treeview(
            self.main, columns=columns, show="headings", height=8
        )

        headers = [
            ("date", "วันที่", 100),
            ("time", "เวลา", 130),
            ("equipment", "อุปกรณ์", 140),
            ("quantity", "จำนวน", 70),
            ("department", "คณะ/หน่วยงาน", 200),
            ("purpose", "วัตถุประสงค์", 200)
        ]

        for col, title, width in headers:
            self.equipment_table.heading(col, text=title)
            self.equipment_table.column(
                col, width=width, anchor="center"
            )

        self.equipment_table.pack(
            fill="both", expand=True, padx=30, pady=(5, 20)
        )

        self.refresh_equipment_table()

    def update_equipment_stock(self):
        if not hasattr(self, "stock_label"):
            return

        name = self.eq_name.get()
        total = self.equipment_stock.get(name, 0)

        self.stock_label.config(
            text=f"จำนวนอุปกรณ์ทั้งหมด: {total} ชิ้น"
        )

    def save_equipment_booking(self):
        department = self.eq_department.get()
        equipment = self.eq_name.get()
        purpose = self.eq_purpose.get().strip()
        booking_date = self.eq_date.get().strip()
        start = self.eq_start.get()
        end = self.eq_end.get()

        if not department or not purpose or not booking_date:
            messagebox.showwarning(
                "ข้อมูลไม่ครบ",
                "กรุณากรอกคณะ/หน่วยงาน วันที่ และวัตถุประสงค์"
            )
            return

        try:
            date.fromisoformat(booking_date)
        except ValueError:
            messagebox.showwarning(
                "วันที่ไม่ถูกต้อง",
                "กรุณากรอกวันที่ในรูปแบบ YYYY-MM-DD"
            )
            return

        try:
            quantity = int(self.eq_quantity.get())
        except ValueError:
            messagebox.showwarning(
                "จำนวนไม่ถูกต้อง",
                "กรุณากรอกจำนวนเป็นตัวเลข"
            )
            return

        if quantity < 1:
            messagebox.showwarning(
                "จำนวนไม่ถูกต้อง",
                "จำนวนต้องมากกว่า 0"
            )
            return

        if not start or not end or end <= start:
            messagebox.showwarning(
                "เวลาไม่ถูกต้อง",
                "เวลาสิ้นสุดต้องมากกว่าเวลาเริ่ม"
            )
            return

        # ตรวจสอบจำนวนอุปกรณ์ที่ว่างในช่วงเวลานั้น
        total_stock = self.equipment_stock[equipment]
        already_booked = 0

        for booking in self.equipment_bookings:
            same_equipment = booking["equipment"] == equipment
            same_date = booking["date"] == booking_date

            overlap = (
                start < booking["end"]
                and end > booking["start"]
            )

            if same_equipment and same_date and overlap:
                already_booked += booking["quantity"]

        available = total_stock - already_booked

        if quantity > available:
            messagebox.showwarning(
                "อุปกรณ์ไม่เพียงพอ",
                f"อุปกรณ์เหลือ {available} ชิ้น "
                f"ในช่วงเวลาที่เลือก"
            )
            return

        booking = {
            "date": booking_date,
            "start": start,
            "end": end,
            "equipment": equipment,
            "quantity": quantity,
            "department": department,
            "purpose": purpose
        }

        self.equipment_bookings.append(booking)

        messagebox.showinfo(
            "จองสำเร็จ",
            f"จอง{equipment}สำเร็จ\n"
            f"วันที่ {booking_date}\n"
            f"เวลา {start} - {end}\n"
            f"จำนวน {quantity} ชิ้น"
        )

        self.show_equipment_booking()

    def refresh_equipment_table(self):
        for item in self.equipment_table.get_children():
            self.equipment_table.delete(item)

        for booking in self.equipment_bookings:
            self.equipment_table.insert(
                "", "end",
                values=(
                    booking["date"],
                    booking["start"] + " - " + booking["end"],
                    booking["equipment"],
                    booking["quantity"],
                    booking["department"],
                    booking["purpose"]
                )
            )

    # ---------------- ข้อมูลห้องประชุม ----------------

    def show_rooms(self):
        self.clear_page()
        self.page_title(
            "ข้อมูลห้องประชุม",
            "รายละเอียดและจำนวนผู้เข้าร่วมสูงสุด"
        )

        rooms = [
            ("ห้องประชุม A", 8, "ชั้น 2"),
            ("ห้องประชุม B", 16, "ชั้น 3"),
            ("ห้องประชุมใหญ่", 30, "ชั้น 4"),
            ("ห้องสัมมนา", 50, "ชั้น 5")
        ]

        for name, capacity, floor in rooms:
            card = tk.Frame(
                self.main,
                bg=WHITE,
                padx=20, pady=18,
                highlightbackground="#DCE3EC",
                highlightthickness=1
            )
            card.pack(fill="x", padx=30, pady=8)

            tk.Label(
                card, text=name,
                font=("Arial", 16, "bold"),
                bg=WHITE, fg=NAVY
            ).pack(anchor="w")

            tk.Label(
                card,
                text=f"รองรับ {capacity} คน | {floor}",
                font=("Arial", 11),
                bg=WHITE, fg="#64748B"
            ).pack(anchor="w", pady=(5, 0))


# เริ่มต้นโปรแกรม
if __name__ == "__main__":
    root = tk.Tk()
    app = MeetingRoomApp(root)
    root.mainloop()