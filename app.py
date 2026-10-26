# นำเข้าและรันแอปพลิเคชันหลักที่รวมระบบฐานข้อมูลและการจัดการการจองไว้แล้ว
import sys
import os

# รันระบบ MeetSpace ที่รวมระบบ Login, Register, Database และ Admin Dashboard
if __name__ == "__main__":
    # นำเข้าจาก โปรเจ็ก.py
    import importlib.util
    file_path = os.path.join(os.path.dirname(__file__), "โปรเจ็ก.py")
    spec = importlib.util.spec_from_file_location("meetspace_module", file_path)
    meetspace = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(meetspace)
    meetspace.start_application()