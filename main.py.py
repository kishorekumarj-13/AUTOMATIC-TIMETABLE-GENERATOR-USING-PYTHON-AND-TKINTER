import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
from datetime import datetime, timedelta
import mysql.connector
import random
import hashlib
import csv
import logging
import configparser
import json
import os
from PIL import Image, ImageTk
import re

# Configure logging
logging.basicConfig(
    filename='eduplan.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constants
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
PERIODS = ["Period 1", "Period 2", "Period 3", "Period 4", "Period 5", "Period 6"]
CLASSES = ["LKG", "UKG"] + [f"{i}th" for i in range(1, 13)]
SECTIONS = ["A", "B", "C", "D"]
SUBJECTS = ["Mathematics", "Physics", "Chemistry", "Biology", "English", "History",
            "Geography", "Computer Science", "Physical Education", "Art", "Music"]
SUBJECT_CATEGORIES = {
    "Mathematics": "math",
    "Physics": "science",
    "Chemistry": "science",
    "Biology": "science",
    "English": "language",
    "History": "social",
    "Geography": "social",
    "Computer Science": "tech",
    "Physical Education": "sports",
    "Art": "arts",
    "Music": "arts"
}
ADMIN_USERNAME = "user"
ADMIN_PASSWORD = "root@projectpurpose2013$"
DB_NAME = "eduplan_pro"
CONFIG_FILE = "eduplan_config.ini"

class ConfigManager:
    def __init__(self, config_file=CONFIG_FILE):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        if not os.path.exists(config_file):
            self.create_default_config()
        self.config.read(config_file)

    def create_default_config(self):
        self.config['DEFAULT'] = {
            'zoom_meeting_id': '',
            'zoom_password': '',
            'zoom_api_key': '',
            'school_name': 'Peace On Green Earth Public School',
            'academic_year': '2025-26',
            'theme': 'light'
        }
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def get_setting(self, section, key):
        return self.config.get(section, key, fallback='')

    def set_setting(self, section, key, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

class DatabaseManager:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        try:
            self.conn = mysql.connector.connect(host='localhost', user='user', password='root@projectpurpose2013$')
            self.cursor = self.conn.cursor()
            self.cursor.execute("CREATE DATABASE IF NOT EXISTS eduplan_pro")
            self.conn.commit()
            self.cursor.close()
            self.conn = mysql.connector.connect(host='localhost', user='user', password='root@projectpurpose2013$', database='eduplan_pro')
            self.cursor = self.conn.cursor()
            self.create_tables()
            self.insert_default_data()
        except mysql.connector.Error as err:
            logging.error(f"Database connection error: {err}")
            raise

    def create_tables(self):
        tables = {
            'users': '''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )''',
            'teachers': '''CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) UNIQUE NOT NULL,
                employee_id VARCHAR(100) UNIQUE,
                subject VARCHAR(100) NOT NULL,
                classes TEXT,
                max_periods INTEGER DEFAULT 6,
                assigned_periods INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            )''',
            'classes': '''CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                class_name VARCHAR(50) NOT NULL,
                section VARCHAR(10) NOT NULL,
                room_number VARCHAR(20),
                strength INTEGER DEFAULT 0,
                academic_year VARCHAR(20),
                is_active BOOLEAN DEFAULT 1,
                UNIQUE(class_name, section)
            )''',
            'timetables': '''CREATE TABLE IF NOT EXISTS timetables (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                class_name VARCHAR(50) NOT NULL,
                section VARCHAR(10) NOT NULL,
                day VARCHAR(20) NOT NULL,
                period VARCHAR(20) NOT NULL,
                teacher_id INTEGER,
                subject_id INTEGER,
                room_number VARCHAR(20),
                is_substitution BOOLEAN DEFAULT 0,
                FOREIGN KEY (teacher_id) REFERENCES teachers (id),
                UNIQUE(class_name, section, day, period)
            )''',
            'absences': '''CREATE TABLE IF NOT EXISTS absences (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                teacher_id INTEGER,
                absent_date DATE,
                absent_day VARCHAR(20),
                absent_period VARCHAR(20),
                reason TEXT,
                substitute_teacher_id INTEGER,
                is_approved BOOLEAN DEFAULT 0,
                FOREIGN KEY (teacher_id) REFERENCES teachers (id),
                FOREIGN KEY (substitute_teacher_id) REFERENCES teachers (id)
            )'''
        }
        
        for table_name, create_sql in tables.items():
            try:
                self.cursor.execute(create_sql)
                self.conn.commit()
            except mysql.connector.Error as e:
                logging.error(f"Error creating table {table_name}: {e}")
                raise
        
        self.cursor.execute("SHOW COLUMNS FROM teachers")
        columns = [column[0] for column in self.cursor.fetchall()]
        if 'classes' not in columns:
            try:
                self.cursor.execute("ALTER TABLE teachers ADD COLUMN classes TEXT")
                self.conn.commit()
                logging.info("Added 'classes' column to teachers table")
            except mysql.connector.Error as e:
                logging.error(f"Error adding classes column: {e}")

        self.cursor.execute("SHOW COLUMNS FROM absences")
        columns = [column[0] for column in self.cursor.fetchall()]
        if 'absent_date' not in columns:
            self.cursor.execute("ALTER TABLE absences ADD COLUMN absent_date DATE")
            self.conn.commit()
            logging.info("Added 'absent_date' column to absences table")
        if 'absent_day' not in columns:
            self.cursor.execute("ALTER TABLE absences ADD COLUMN absent_day VARCHAR(20)")
            self.conn.commit()
            logging.info("Added 'absent_day' column to absences table")
        if 'absent_period' not in columns:
            self.cursor.execute("ALTER TABLE absences ADD COLUMN absent_period VARCHAR(20)")
            self.conn.commit()
            logging.info("Added 'absent_period' column to absences table")
        if 'reason' not in columns:
            self.cursor.execute("ALTER TABLE absences ADD COLUMN reason TEXT")
            self.conn.commit()
            logging.info("Added 'reason' column to absences table")
        if 'substitute_teacher_id' not in columns:
            self.cursor.execute("ALTER TABLE absences ADD COLUMN substitute_teacher_id INTEGER")
            self.conn.commit()
            logging.info("Added 'substitute_teacher_id' column to absences table")
        if 'is_approved' not in columns:
            self.cursor.execute("ALTER TABLE absences ADD COLUMN is_approved BOOLEAN DEFAULT 0")
            self.conn.commit()
            logging.info("Added 'is_approved' column to absences table")

    def insert_default_data(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (ADMIN_USERNAME,))
            if self.cursor.fetchone()[0] == 0:
                admin_hash = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
                self.cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                                  (ADMIN_USERNAME, admin_hash, 'admin'))
            
            for class_name in CLASSES:
                for section in SECTIONS:
                    self.cursor.execute("INSERT IGNORE INTO classes (class_name, section, academic_year) VALUES (%s, %s, %s)",
                                      (class_name, section, "2025-26"))
            
            self.conn.commit()
        except mysql.connector.Error as e:
            logging.error(f"Error inserting default data: {e}")
            self.conn.rollback()
            raise

    def execute_query(self, query, params=None, fetch=False):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            if fetch:
                return self.cursor.fetchall()
            self.conn.commit()
            return self.cursor.rowcount
        except mysql.connector.Error as e:
            logging.error(f"SQL Error: {e}, Query: {query}, Params: {params}")
            self.conn.rollback()
            raise

    def close(self):
        self.cursor.close()
        self.conn.close()

class SecurityManager:
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password, hash_value):
        return SecurityManager.hash_password(password) == hash_value

    @staticmethod
    def validate_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

class EduPlanPro:
    def __init__(self, root):
        self.root = root
        self.root.title("EduPlan Pro: Automatic Timetable Generator")
        self.root.geometry("1200x700")
        self.db = DatabaseManager()
        self.security = SecurityManager()
        self.config = ConfigManager()
        self.current_user = None
        self.current_user_id = None
        self.current_user_role = None
        self.logo_img = None
        self.theme = self.config.get_setting('DEFAULT', 'theme')
        self.bg_color = "#e3f2fd" if self.theme == 'light' else "#263238"
        self.fg_color = "#1565c0" if self.theme == 'light' else "#90caf9"
        self.root.configure(bg=self.bg_color)
        self.setup_styles()
        self.create_login_screen()
        self.update_clock()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), background=self.bg_color, foreground=self.fg_color)
        self.style.configure('Custom.TButton', padding=8, font=('Segoe UI', 10), background='#42a5f5', foreground='white')
        self.style.map('Custom.TButton', background=[('active', '#1976d2')])
        self.style.configure('TCombobox', font=('Segoe UI', 10), padding=5)
        self.style.configure('TEntry', font=('Segoe UI', 10), padding=5)
        self.style.configure('Treeview', font=('Segoe UI', 10), rowheight=25, background='#ffffff' if self.theme == 'light' else '#37474f')
        self.style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background='#bbdefb' if self.theme == 'light' else '#455a64')

    def update_clock(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(self, "clock_label"):
            self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def create_login_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(expand=True, fill=tk.BOTH)

        self.clock_label = tk.Label(main_frame, text="", font=("Segoe UI", 12, 'bold'), bg=self.bg_color, fg=self.fg_color)
        self.clock_label.pack(side=tk.TOP, anchor=tk.E, padx=10, pady=5)

        logo_container = tk.Frame(main_frame, bg=self.bg_color)
        logo_container.pack(pady=10, fill=tk.X)

        logo_frame = tk.Frame(logo_container, bg=self.bg_color)
        logo_frame.pack(expand=True)

        if self.logo_img:
            tk.Label(logo_frame, image=self.logo_img, bg=self.bg_color).pack(side=tk.LEFT)

        school_name = self.config.get_setting('DEFAULT', 'school_name')
        tk.Label(logo_frame, text=school_name, font=("Segoe UI", 18, "bold"), bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT, padx=10)

        login_frame = tk.Frame(main_frame, bg="#ffffff" if self.theme == 'light' else "#37474f", relief=tk.RAISED, bd=2, padx=20, pady=20)
        login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(login_frame, text="EduPlan Pro", font=("Segoe UI", 24, "bold"), bg="#ffffff" if self.theme == 'light' else "#37474f", fg=self.fg_color).pack(pady=10)
        tk.Label(login_frame, text="Automatic Timetable Generator", font=("Segoe UI", 12), bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").pack(pady=5)

        form_frame = tk.Frame(login_frame, bg="#ffffff" if self.theme == 'light' else "#37474f")
        form_frame.pack(pady=20)

        tk.Label(form_frame, text="Username:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=0, column=0, pady=5, sticky="e")
        self.username_entry = tk.Entry(form_frame, width=25, font=("Segoe UI", 10))
        self.username_entry.grid(row=0, column=1, pady=5, padx=10)

        tk.Label(form_frame, text="Password:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=1, column=0, pady=5, sticky="e")
        self.password_entry = tk.Entry(form_frame, width=25, show="*", font=("Segoe UI", 10))
        self.password_entry.grid(row=1, column=1, pady=5, padx=10)

        self.username_entry.bind('<Return>', lambda event: self.authenticate())
        self.password_entry.bind('<Return>', lambda event: self.authenticate())

        button_frame = tk.Frame(login_frame, bg="#ffffff" if self.theme == 'light' else "#37474f")
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Login", command=self.authenticate, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Register", command=self.show_registration_dialog, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Upload Logo", command=self.choose_logo, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="About Software", command=self.show_about_dialog, style='Custom.TButton').pack(side=tk.LEFT, padx=5)

    def authenticate(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        try:
            query = "SELECT id, username, password_hash, role FROM users WHERE username = %s AND is_active = 1"
            result = self.db.execute_query(query, (username,), fetch=True)

            if result and self.security.verify_password(password, result[0][2]):
                self.current_user = username
                self.current_user_id = result[0][0]
                self.current_user_role = result[0][3]
                self.db.execute_query("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (self.current_user_id,))
                self.create_main_dashboard()
            else:
                messagebox.showerror("Error", "Invalid username or password.")
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
            logging.error(f"Authentication error: {e}")

    def show_registration_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Register")
        dialog.geometry("400x300")
        dialog.configure(bg="#ffffff" if self.theme == 'light' else "#37474f")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Register New User", font=("Segoe UI", 16, "bold"), bg="#ffffff" if self.theme == 'light' else "#37474f", fg=self.fg_color).pack(pady=10)

        form_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        form_frame.pack(pady=20)

        tk.Label(form_frame, text="Username:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=0, column=0, pady=5, sticky="e")
        username_entry = tk.Entry(form_frame, width=20, font=("Segoe UI", 10))
        username_entry.grid(row=0, column=1, pady=5, padx=10)

        tk.Label(form_frame, text="Password:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=1, column=0, pady=5, sticky="e")
        password_entry = tk.Entry(form_frame, show="*", width=20, font=("Segoe UI", 10))
        password_entry.grid(row=1, column=1, pady=5, padx=10)

        def register():
            username = username_entry.get().strip()
            password = password_entry.get().strip()

            if not all([username, password]):
                messagebox.showerror("Error", "All fields are required.")
                return

            if len(password) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters.")
                return

            try:
                check_query = "SELECT COUNT(*) FROM users WHERE username = %s"
                if self.db.execute_query(check_query, (username,), fetch=True)[0][0] > 0:
                    messagebox.showerror("Error", "Username already exists.")
                    return

                password_hash = self.security.hash_password(password)
                self.db.execute_query("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                                    (username, password_hash, 'user'))
                messagebox.showinfo("Success", "User registered successfully!")
                dialog.destroy()
            except mysql.connector.Error as e:
                messagebox.showerror("Error", f"Registration failed: {e}")
                logging.error(f"Registration error: {e}")

        button_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Register", command=register, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, style='Custom.TButton').pack(side=tk.LEFT, padx=5)

    def show_about_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("About EduPlan Pro")
        dialog.geometry("500x400")
        dialog.configure(bg="#ffffff" if self.theme == 'light' else "#37474f")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="About EduPlan Pro", font=("Segoe UI", 16, "bold"), bg="#ffffff" if self.theme == 'light' else "#37474f", fg=self.fg_color).pack(pady=10)

        info_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        info_frame.pack(pady=10, padx=10, fill=tk.BOTH)

        info_text = """
EduPlan Pro is an advanced timetable management system designed for schools to streamline scheduling and teacher management. Key features include:

- Automatic timetable generation
- Teacher absence management with automatic substitution
- Export/import timetables in CSV format
- User-friendly interface with customizable themes

Version: 1.0.0
Developed by: Kishore, Roopa, and Mohan

Story: Kishore, Roopa, and Mohan, three passionate software engineers, created this app during a weekend hackathon in 2024. Inspired by their own experiences with school scheduling chaos, they combined Kishore's database expertise, Roopa's UI design flair, and Mohan's algorithm prowess to build EduPlan Pro. Their goal was to make timetable management easy and efficient for schools worldwide.
"""
        tk.Label(info_frame, text=info_text, font=("Segoe UI", 10), bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5", justify=tk.LEFT, wraplength=460).pack(pady=5)

        terms_frame = tk.LabelFrame(dialog, text="Terms and Conditions", font=("Segoe UI", 12, "bold"), bg="#ffffff" if self.theme == 'light' else "#37474f", fg=self.fg_color)
        terms_frame.pack(pady=10, padx=10, fill=tk.BOTH)

        terms_text = """
1. Use of this software is restricted to authorized users only.
2. Data entered into the system remains the property of the school.
3. The software is provided as-is, with no warranty for data loss.
4. Users are responsible for maintaining secure login credentials.
5. For support, contact support@xai.edu
"""
        tk.Label(terms_frame, text=terms_text, font=("Segoe UI", 10), bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5", justify=tk.LEFT, wraplength=460).pack(pady=5)

        button_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Close", command=dialog.destroy, style='Custom.TButton').pack()

    def choose_logo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if file_path:
            try:
                image = Image.open(file_path)
                image = image.resize((100, 100), Image.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(image)
                self.create_login_screen()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load logo: {e}")
                logging.error(f"Logo loading error: {e}")

    def toggle_theme(self):
        current_theme = self.config.get_setting('DEFAULT', 'theme')
        new_theme = 'dark' if current_theme == 'light' else 'light'
        self.config.set_setting('DEFAULT', 'theme', new_theme)
        self.theme = new_theme
        self.bg_color = "#e3f2fd" if self.theme == 'light' else "#263238"
        self.fg_color = "#1565c0" if self.theme == 'light' else "#90caf9"
        self.create_main_dashboard() if self.current_user else self.create_login_screen()

    def create_main_dashboard(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = tk.Frame(main_frame, bg="#bbdefb" if self.theme == 'light' else "#455a64")
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.clock_label = tk.Label(top_frame, text="", font=("Segoe UI", 12, 'bold'), bg="#bbdefb" if self.theme == 'light' else "#455a64", fg=self.fg_color)
        self.clock_label.pack(side=tk.RIGHT)
        
        logo_container = tk.Frame(top_frame, bg="#bbdefb" if self.theme == 'light' else "#455a64")
        logo_container.pack(fill=tk.X)

        logo_frame = tk.Frame(logo_container, bg="#bbdefb" if self.theme == 'light' else "#455a64")
        logo_frame.pack(expand=True)

        if self.logo_img:
            tk.Label(logo_frame, image=self.logo_img, bg="#bbdefb" if self.theme == 'light' else "#455a64").pack(side=tk.LEFT)

        school_name = self.config.get_setting('DEFAULT', 'school_name')
        tk.Label(logo_frame, text=school_name, font=("Segoe UI", 18, "bold"), bg="#bbdefb" if self.theme == 'light' else "#455a64", fg=self.fg_color).pack(side=tk.LEFT, padx=10)

        welcome_frame = tk.Frame(main_frame, bg=self.bg_color)
        welcome_frame.pack(pady=10)
        
        tk.Label(welcome_frame, text=f"Welcome to {school_name}", font=("Segoe UI", 18, "bold"),
                bg=self.bg_color, fg=self.fg_color).pack()
        tk.Label(welcome_frame, text=f"User: {self.current_user} | Role: {self.current_user_role}", 
                font=("Segoe UI", 12), bg=self.bg_color, fg="#455a64" if self.theme == 'light' else "#b0bec5").pack()

        class_frame = tk.LabelFrame(main_frame, text="Select Class", bg="#ffffff" if self.theme == 'light' else "#37474f", font=("Segoe UI", 12, "bold"), fg=self.fg_color)
        class_frame.pack(fill=tk.X, padx=10, pady=10)

        class_grid_frame = tk.Frame(class_frame, bg="#ffffff" if self.theme == 'light' else "#37474f")
        class_grid_frame.pack(pady=10)

        for i, class_name in enumerate(CLASSES):
            btn = ttk.Button(class_grid_frame, text=class_name, command=lambda c=class_name: self.show_sections(c),
                           style='Custom.TButton', width=8)
            btn.grid(row=i//7, column=i%7, padx=2, pady=2)

        action_frame = tk.LabelFrame(main_frame, text="Actions", bg="#ffffff" if self.theme == 'light' else "#37474f", font=("Segoe UI", 12, "bold"), fg=self.fg_color)
        action_frame.pack(fill=tk.X, padx=10, pady=10)

        action_grid_frame = tk.Frame(action_frame, bg="#ffffff" if self.theme == 'light' else "#37474f")
        action_grid_frame.pack(pady=10)

        actions = [
            ("Add Teacher", self.add_teacher),
            ("Manage Teachers", self.manage_teachers),
            ("Teacher Attendance", self.teacher_attendance),
            ("Auto Generate Timetable", self.auto_generate_timetable),
            ("Export Timetable", self.export_timetable),
            ("Import Timetable", self.import_timetable),
            ("About Software", self.show_about_dialog),
            ("Toggle Theme", self.toggle_theme),
            ("Logout", self.logout)
        ]

        for i, (text, cmd) in enumerate(actions):
            btn = ttk.Button(action_grid_frame, text=text, command=cmd, style='Custom.TButton', width=18)
            btn.grid(row=i//4, column=i%4, padx=5, pady=5)

    def show_sections(self, class_name):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Sections for {class_name}")
        dialog.geometry("400x300")
        dialog.configure(bg="#ffffff" if self.theme == 'light' else "#37474f")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"Sections for {class_name}", font=("Segoe UI", 16, "bold"), bg="#ffffff" if self.theme == 'light' else "#37474f", fg=self.fg_color).pack(pady=10)

        try:
            sections = self.db.execute_query("SELECT section FROM classes WHERE class_name = %s AND is_active = 1", 
                                           (class_name,), fetch=True)
            sections = [s[0] for s in sections]

            sections_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
            sections_frame.pack(pady=10)

            for i, section in enumerate(sections):
                btn = ttk.Button(sections_frame, text=f"{class_name} {section}", 
                               command=lambda s=section: [dialog.destroy(), self.open_timetable_editor(class_name, s)],
                               style='Custom.TButton', width=15)
                btn.grid(row=i//2, column=i%2, padx=5, pady=5)

            button_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
            button_frame.pack(pady=20)
            ttk.Button(button_frame, text="Add Section", command=lambda: self.add_section(class_name, dialog), 
                     style='Custom.TButton').pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", command=dialog.destroy, 
                     style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Failed to load sections: {e}")
            logging.error(f"Sections loading error: {e}")

    def add_section(self, class_name, parent_dialog=None):
        section = simpledialog.askstring("Add Section", "Enter new section (e.g., A, B, C):")
        if section:
            section = section.upper().strip()
            try:
                check_query = "SELECT COUNT(*) FROM classes WHERE class_name = %s AND section = %s"
                if self.db.execute_query(check_query, (class_name, section), fetch=True)[0][0] > 0:
                    messagebox.showerror("Error", "Section already exists.")
                    return
                self.db.execute_query("INSERT INTO classes (class_name, section, academic_year) VALUES (%s, %s, %s)",
                                    (class_name, section, self.config.get_setting('DEFAULT', 'academic_year')))
                messagebox.showinfo("Success", f"Section {section} added for {class_name}.")
                if parent_dialog:
                    parent_dialog.destroy()
                    self.show_sections(class_name)
            except mysql.connector.Error as e:
                messagebox.showerror("Error", f"Failed to add section: {e}")
                logging.error(f"Add section error: {e}")

    def add_teacher(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Teacher")
        dialog.geometry("450x500")
        dialog.configure(bg="#ffffff" if self.theme == 'light' else "#37474f")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Add New Teacher", font=("Segoe UI", 16, "bold"), bg="#ffffff" if self.theme == 'light' else "#37474f", fg=self.fg_color).pack(pady=10)

        form_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        form_frame.pack(pady=20)

        tk.Label(form_frame, text="Name:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=0, column=0, pady=5, sticky="e")
        name_entry = tk.Entry(form_frame, width=25, font=("Segoe UI", 10))
        name_entry.grid(row=0, column=1, pady=5, padx=10)

        tk.Label(form_frame, text="Employee ID:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=1, column=0, pady=5, sticky="e")
        emp_id_entry = tk.Entry(form_frame, width=25, font=("Segoe UI", 10))
        emp_id_entry.grid(row=1, column=1, pady=5, padx=10)

        tk.Label(form_frame, text="Subject:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=2, column=0, pady=5, sticky="e")
        subject_combo = ttk.Combobox(form_frame, values=SUBJECTS, width=22, font=("Segoe UI", 10))
        subject_combo.grid(row=2, column=1, pady=5, padx=10)

        tk.Label(form_frame, text="Classes (comma-separated):", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=3, column=0, pady=5, sticky="e")
        classes_entry = tk.Entry(form_frame, width=25, font=("Segoe UI", 10))
        classes_entry.grid(row=3, column=1, pady=5, padx=10)

        tk.Label(form_frame, text="Max Periods per Day:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=4, column=0, pady=5, sticky="e")
        max_periods_entry = tk.Entry(form_frame, width=25, font=("Segoe UI", 10))
        max_periods_entry.insert(0, "6")
        max_periods_entry.grid(row=4, column=1, pady=5, padx=10)

        def save_teacher():
            name = name_entry.get().strip()
            emp_id = emp_id_entry.get().strip()
            subject = subject_combo.get().strip()
            classes = classes_entry.get().strip()
            max_periods = max_periods_entry.get().strip()

            if not all([name, emp_id, subject, max_periods]):
                messagebox.showerror("Error", "Name, Employee ID, Subject, and Max Periods are required.")
                return

            try:
                max_periods = int(max_periods)
                if max_periods <= 0 or max_periods > len(PERIODS):
                    messagebox.showerror("Error", f"Max periods must be between 1 and {len(PERIODS)}.")
                    return

                if classes:
                    class_list = [c.strip() for c in classes.split(",")]
                    for c in class_list:
                        if c not in CLASSES:
                            messagebox.showerror("Error", f"Invalid class: {c}")
                            return

                check_query = "SELECT COUNT(*) FROM teachers WHERE employee_id = %s OR name = %s"
                if self.db.execute_query(check_query, (emp_id, name), fetch=True)[0][0] > 0:
                    messagebox.showerror("Error", "Teacher name or Employee ID already exists.")
                    return

                self.db.execute_query(
                    "INSERT INTO teachers (name, employee_id, subject, classes, max_periods) VALUES (%s, %s, %s, %s, %s)",
                    (name, emp_id, subject, classes, max_periods)
                )
                messagebox.showinfo("Success", "Teacher added successfully!")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Max periods must be a number.")
            except mysql.connector.Error as e:
                messagebox.showerror("Error", f"Failed to add teacher: {e}")
                logging.error(f"Add teacher error: {e}")

        button_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Save", command=save_teacher, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, style='Custom.TButton').pack(side=tk.LEFT, padx=5)

    def manage_teachers(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Manage Teachers")
        dialog.geometry("800x500")
        dialog.configure(bg="#ffffff" if self.theme == 'light' else "#37474f")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Manage Teachers", font=("Segoe UI", 16, "bold"), bg="#ffffff" if self.theme == 'light' else "#37474f", fg=self.fg_color).pack(pady=10)

        tree_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("ID", "Name", "Employee ID", "Subject", "Classes", "Max Periods")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        tree.pack(fill=tk.BOTH, expand=True)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        try:
            teachers = self.db.execute_query("SELECT id, name, employee_id, subject, classes, max_periods FROM teachers WHERE is_active = 1", fetch=True)
            for teacher in teachers:
                tree.insert("", tk.END, values=teacher)

            def delete_teacher():
                selected = tree.selection()
                if not selected:
                    messagebox.showerror("Error", "Select a teacher to delete.")
                    return
                if messagebox.askyesno("Confirm", "Are you sure you want to delete this teacher?"):
                    teacher_id = tree.item(selected[0])['values'][0]
                    self.db.execute_query("UPDATE teachers SET is_active = 0 WHERE id = %s", (teacher_id,))
                    tree.delete(selected[0])
                    messagebox.showinfo("Success", "Teacher deleted successfully.")

            def edit_teacher():
                selected = tree.selection()
                if not selected:
                    messagebox.showerror("Error", "Select a teacher to edit.")
                    return
                teacher_data = tree.item(selected[0])['values']
                self.edit_teacher_dialog(teacher_data, dialog)

            button_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
            button_frame.pack(pady=20)
            ttk.Button(button_frame, text="Edit", command=edit_teacher, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Delete", command=delete_teacher, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", command=dialog.destroy, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Failed to load teachers: {e}")
            logging.error(f"Manage teachers error: {e}")

    def edit_teacher_dialog(self, teacher_data, parent_dialog):
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Teacher")
        dialog.geometry("450x500")
        dialog.configure(bg="#ffffff" if self.theme == 'light' else "#37474f")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Edit Teacher", font=("Segoe UI", 16, "bold"), bg="#ffffff" if self.theme == 'light' else "#37474f", fg=self.fg_color).pack(pady=10)

        form_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        form_frame.pack(pady=20)

        tk.Label(form_frame, text="Name:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=0, column=0, pady=5, sticky="e")
        name_entry = tk.Entry(form_frame, width=25, font=("Segoe UI", 10))
        name_entry.insert(0, teacher_data[1])
        name_entry.grid(row=0, column=1, pady=5, padx=10)

        tk.Label(form_frame, text="Employee ID:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=1, column=0, pady=5, sticky="e")
        emp_id_entry = tk.Entry(form_frame, width=25, font=("Segoe UI", 10))
        emp_id_entry.insert(0, teacher_data[2])
        emp_id_entry.grid(row=1, column=1, pady=5, padx=10)

        tk.Label(form_frame, text="Subject:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=2, column=0, pady=5, sticky="e")
        subject_combo = ttk.Combobox(form_frame, values=SUBJECTS, width=22, font=("Segoe UI", 10))
        subject_combo.set(teacher_data[3])
        subject_combo.grid(row=2, column=1, pady=5, padx=10)

        tk.Label(form_frame, text="Classes (comma-separated):", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=3, column=0, pady=5, sticky="e")
        classes_entry = tk.Entry(form_frame, width=25, font=("Segoe UI", 10))
        classes_entry.insert(0, teacher_data[4] or "")
        classes_entry.grid(row=3, column=1, pady=5, padx=10)

        tk.Label(form_frame, text="Max Periods per Day:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=4, column=0, pady=5, sticky="e")
        max_periods_entry = tk.Entry(form_frame, width=25, font=("Segoe UI", 10))
        max_periods_entry.insert(0, str(teacher_data[5]))
        max_periods_entry.grid(row=4, column=1, pady=5, padx=10)

        def save_teacher():
            name = name_entry.get().strip()
            emp_id = emp_id_entry.get().strip()
            subject = subject_combo.get().strip()
            classes = classes_entry.get().strip()
            max_periods = max_periods_entry.get().strip()

            if not all([name, emp_id, subject, max_periods]):
                messagebox.showerror("Error", "Name, Employee ID, Subject, and Max Periods are required.")
                return

            try:
                max_periods = int(max_periods)
                if max_periods <= 0 or max_periods > len(PERIODS):
                    messagebox.showerror("Error", f"Max periods must be between 1 and {len(PERIODS)}.")
                    return

                if classes:
                    class_list = [c.strip() for c in classes.split(",")]
                    for c in class_list:
                        if c not in CLASSES:
                            messagebox.showerror("Error", f"Invalid class: {c}")
                            return

                check_query = "SELECT COUNT(*) FROM teachers WHERE (employee_id = %s OR name = %) AND id != %s"
                if self.db.execute_query(check_query, (emp_id, name, teacher_data[0]), fetch=True)[0][0] > 0:
                    messagebox.showerror("Error", "Teacher name or Employee ID already exists.")
                    return

                self.db.execute_query(
                    "UPDATE teachers SET name = %s, employee_id = %s, subject = %s, classes = %s, max_periods = %s WHERE id = %s",
                    (name, emp_id, subject, classes, max_periods, teacher_data[0])
                )
                messagebox.showinfo("Success", "Teacher updated successfully!")
                dialog.destroy()
                parent_dialog.destroy()
                self.manage_teachers()
            except ValueError:
                messagebox.showerror("Error", "Max periods must be a number.")
            except mysql.connector.Error as e:
                messagebox.showerror("Error", f"Failed to update teacher: {e}")
                logging.error(f"Edit teacher error: {e}")

        button_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Save", command=save_teacher, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, style='Custom.TButton').pack(side=tk.LEFT, padx=5)

    def teacher_attendance(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Teacher Attendance")
        dialog.geometry("800x500")
        dialog.configure(bg="#ffffff" if self.theme == 'light' else "#37474f")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Teacher Attendance", font=("Segoe UI", 16, "bold"), bg="#ffffff" if self.theme == 'light' else "#37474f", fg=self.fg_color).pack(pady=10)

        tree_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("ID", "Name", "Subject", "Date", "Day", "Period", "Status", "Reason")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        tree.pack(fill=tk.BOTH, expand=True)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        try:
            query = """
                SELECT a.id, t.name, t.subject, a.absent_date, a.absent_day, a.absent_period,
                       CASE WHEN a.is_approved THEN 'Absent' ELSE 'Pending' END, a.reason
                FROM absences a
                JOIN teachers t ON a.teacher_id = t.id
                WHERE t.is_active = 1
            """
            records = self.db.execute_query(query, fetch=True)
            for record in records:
                tree.insert("", tk.END, values=record)

            def mark_absence():
                teacher_dialog = tk.Toplevel(dialog)
                teacher_dialog.title("Mark Absence")
                teacher_dialog.geometry("400x500")
                teacher_dialog.configure(bg="#ffffff" if self.theme == 'light' else "#37474f")
                teacher_dialog.transient(dialog)
                teacher_dialog.grab_set()

                tk.Label(teacher_dialog, text="Mark Teacher Absence", font=("Segoe UI", 14, "bold"), bg="#ffffff" if self.theme == 'light' else "#37474f", fg=self.fg_color).pack(pady=10)

                form_frame = tk.Frame(teacher_dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
                form_frame.pack(pady=10)

                tk.Label(form_frame, text="Teacher:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=0, column=0, pady=5, sticky="e")
                teachers = self.db.execute_query("SELECT name FROM teachers WHERE is_active = 1", fetch=True)
                teacher_names = [t[0] for t in teachers]
                teacher_combo = ttk.Combobox(form_frame, values=teacher_names, width=22, font=("Segoe UI", 10))
                teacher_combo.grid(row=0, column=1, pady=5, padx=10)

                tk.Label(form_frame, text="Date:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=1, column=0, pady=5, sticky="e")
                date_entry = tk.Entry(form_frame, width=25, font=("Segoe UI", 10))
                date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
                date_entry.grid(row=1, column=1, pady=5, padx=10)

                tk.Label(form_frame, text="Day:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=2, column=0, pady=5, sticky="e")
                day_combo = ttk.Combobox(form_frame, values=DAYS, width=22, font=("Segoe UI", 10))
                day_combo.grid(row=2, column=1, pady=5, padx=10)

                tk.Label(form_frame, text="Period:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=3, column=0, pady=5, sticky="e")
                period_combo = ttk.Combobox(form_frame, values=PERIODS, width=22, font=("Segoe UI", 10))
                period_combo.grid(row=3, column=1, pady=5, padx=10)

                tk.Label(form_frame, text="Reason:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=4, column=0, pady=5, sticky="e")
                reason_entry = tk.Entry(form_frame, width=25, font=("Segoe UI", 10))
                reason_entry.grid(row=4, column=1, pady=5, padx=10)

                whole_day_var = tk.BooleanVar(value=False)
                def toggle_period_combo():
                    if whole_day_var.get():
                        period_combo.config(state='disabled')
                    else:
                        period_combo.config(state='normal')

                check = tk.Checkbutton(form_frame, text="Absent for whole day", variable=whole_day_var,
                                       command=toggle_period_combo, bg="#ffffff" if self.theme == 'light' else "#37474f",
                                       fg="#455a64" if self.theme == 'light' else "#b0bec5", selectcolor="#ffffff" if self.theme == 'light' else "#37474f")
                check.grid(row=5, column=0, columnspan=2, pady=5, sticky="w")

                def save_absence():
                    teacher_name = teacher_combo.get().strip()
                    absent_date = date_entry.get().strip()
                    absent_day = day_combo.get().strip()
                    absent_period = period_combo.get().strip()
                    reason = reason_entry.get().strip()
                    whole_day = whole_day_var.get()

                    if not all([teacher_name, absent_date, absent_day, reason]):
                        messagebox.showerror("Error", "Teacher, Date, Day, and Reason are required.")
                        return
                    if not whole_day and not absent_period:
                        messagebox.showerror("Error", "Period is required if not absent for whole day.")
                        return

                    try:
                        dt = datetime.strptime(absent_date, "%Y-%m-%d")
                        calculated_day = dt.strftime("%A")
                        if calculated_day != absent_day:
                            messagebox.showerror("Error", f"Selected day {absent_day} does not match the date's day {calculated_day}.")
                            return

                        if absent_day not in DAYS:
                            messagebox.showerror("Error", "Invalid day selected.")
                            return

                        teacher_result = self.db.execute_query("SELECT id FROM teachers WHERE name = %s AND is_active = 1", (teacher_name,), fetch=True)
                        if not teacher_result:
                            messagebox.showerror("Error", "Invalid teacher selected.")
                            return
                        teacher_id = teacher_result[0][0]

                        if whole_day:
                            periods = PERIODS
                        else:
                            periods = [absent_period]
                            if absent_period not in PERIODS:
                                messagebox.showerror("Error", "Invalid period selected.")
                                return

                        substituted = 0
                        for p in periods:
                            check_query = "SELECT COUNT(*) FROM absences WHERE teacher_id = %s AND absent_date = %s AND absent_day = %s AND absent_period = %s"
                            if self.db.execute_query(check_query, (teacher_id, absent_date, absent_day, p), fetch=True)[0][0] > 0:
                                continue  # Skip if already recorded

                            self.db.execute_query(
                                "INSERT INTO absences (teacher_id, absent_date, absent_day, absent_period, reason, substitute_teacher_id, is_approved) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                (teacher_id, absent_date, absent_day, p, reason, None, 1)
                            )
                            self.handle_substitution(teacher_id, absent_date, absent_day, p)
                            substituted += 1

                        message = f"Absence(s) recorded for {teacher_name} on {absent_day}"
                        if whole_day:
                            message += " for the whole day."
                        else:
                            message += f" for {absent_period}."
                        messagebox.showinfo("Success", message)
                        teacher_dialog.destroy()
                        dialog.destroy()
                        self.teacher_attendance()
                    except ValueError:
                        messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
                    except mysql.connector.Error as e:
                        messagebox.showerror("Error", f"Failed to record absence: {e}")
                        logging.error(f"Mark absence error: {e}")

                button_frame = tk.Frame(teacher_dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
                button_frame.pack(pady=20)
                ttk.Button(button_frame, text="Save", command=save_absence, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Cancel", command=teacher_dialog.destroy, style='Custom.TButton').pack(side=tk.LEFT, padx=5)

            button_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
            button_frame.pack(pady=20)
            ttk.Button(button_frame, text="Mark Absence", command=mark_absence, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", command=dialog.destroy, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Failed to load attendance: {e}")
            logging.error(f"Teacher attendance error: {e}")

    def get_class_level(self, class_name):
        if class_name in ["LKG", "UKG"]:
            return 0
        try:
            return int(class_name[:-2])
        except:
            return 0

    def handle_substitution(self, teacher_id, absent_date, absent_day, absent_period):
        try:
            # Find classes affected by the teacher's absence on the specific day and period
            query = """
                SELECT class_name, section, subject_id
                FROM timetables
                WHERE teacher_id = %s AND day = %s AND period = %s
            """
            affected_classes = self.db.execute_query(query, (teacher_id, absent_day, absent_period), fetch=True)
            if not affected_classes:
                logging.info(f"No classes assigned to teacher {teacher_id} on {absent_day}, {absent_period}.")
                return

            # Get all teachers except the absent one
            available_teachers = self.db.execute_query(
                "SELECT id, name, subject, classes, max_periods FROM teachers WHERE is_active = 1 AND id != %s",
                (teacher_id,), fetch=True
            )

            for class_name, section, subject_id in affected_classes:
                subject = SUBJECTS[subject_id - 1]
                category = SUBJECT_CATEGORIES.get(subject, "other")

                # Get busy teachers for this period
                period_teachers = self.db.execute_query(
                    "SELECT teacher_id FROM timetables WHERE day = %s AND period = %s",
                    (absent_day, absent_period), fetch=True
                )
                busy_teacher_ids = {t[0] for t in period_teachers if t[0] is not None}

                # Level 1: same subject and class, free, load < max
                suitable_teachers = [
                    t for t in available_teachers
                    if t[0] not in busy_teacher_ids and
                    t[2] == subject and
                    class_name in (t[3] or "").split(",") and
                    self.get_teacher_load(t[0], absent_day) < t[4] and
                    not self.is_teacher_absent(t[0], absent_date, absent_period)
                ]
                level = 1

                if not suitable_teachers:
                    # Level 2: same class, any subject, free, load < max
                    suitable_teachers = [
                        t for t in available_teachers
                        if t[0] not in busy_teacher_ids and
                        class_name in (t[3] or "").split(",") and
                        self.get_teacher_load(t[0], absent_day) < t[4] and
                        not self.is_teacher_absent(t[0], absent_date, absent_period)
                    ]
                    level = 2
                    if suitable_teachers:
                        logging.info(f"No same-subject substitute found for {class_name} {section}, {absent_day}, {absent_period}. Using same-class any-subject teacher.")

                if not suitable_teachers:
                    # Level 3: any, free, load < max
                    suitable_teachers = [
                        t for t in available_teachers
                        if t[0] not in busy_teacher_ids and
                        self.get_teacher_load(t[0], absent_day) < t[4] and
                        not self.is_teacher_absent(t[0], absent_date, absent_period)
                    ]
                    level = 3
                    if suitable_teachers:
                        logging.info(f"No class-qualified substitute found for {class_name} {section}, {absent_day}, {absent_period}. Using any available teacher.")

                if not suitable_teachers:
                    # Level 4: any, free, load <= max (allow at max)
                    suitable_teachers = [
                        t for t in available_teachers
                        if t[0] not in busy_teacher_ids and
                        self.get_teacher_load(t[0], absent_day) <= t[4] and
                        not self.is_teacher_absent(t[0], absent_date, absent_period)
                    ]
                    level = 4
                    if suitable_teachers:
                        logging.info(f"Assigning substitute at level 4 (allowing max load) for {class_name} {section}, {absent_day}, {absent_period}.")

                if not suitable_teachers:
                    # Level 5: reassign from lower priority class
                    level = 5
                    potential_teachers = [
                        t for t in available_teachers
                        if self.get_teacher_load(t[0], absent_day) < t[4] and
                        not self.is_teacher_absent(t[0], absent_date, absent_period)
                    ]  # no busy check

                    candidates = []
                    for t in potential_teachers:
                        query = "SELECT class_name, section FROM timetables WHERE teacher_id = %s AND day = %s AND period = %s"
                        result = self.db.execute_query(query, (t[0], absent_day, absent_period), fetch=True)
                        if result:
                            old_class, old_section = result[0]
                            old_level = self.get_class_level(old_class)
                            load_ratio = self.get_teacher_load(t[0], absent_day) / t[4] if t[4] > 0 else 0
                            same_category = 0 if SUBJECT_CATEGORIES.get(t[2], "other") == category else 1
                            candidates.append((t, old_class, old_section, old_level, load_ratio, same_category))

                    if candidates:
                        # Select the one with min old_level, then min load_ratio, then min same_category
                        candidates.sort(key=lambda x: (x[3], x[4], x[5]))
                        selected_teacher, old_class, old_section, _, _, _ = candidates[0]

                        # Unassign the old slot
                        self.db.execute_query(
                            "UPDATE timetables SET teacher_id = NULL, is_substitution = 1 WHERE class_name = %s AND section = %s AND day = %s AND period = %s",
                            (old_class, old_section, absent_day, absent_period)
                        )

                        # Assign to new slot
                        self.db.execute_query(
                            "UPDATE timetables SET teacher_id = %s, is_substitution = 1 WHERE class_name = %s AND section = %s AND day = %s AND period = %s",
                            (selected_teacher[0], class_name, section, absent_day, absent_period)
                        )

                        # Update absence
                        self.db.execute_query(
                            "UPDATE absences SET substitute_teacher_id = %s WHERE teacher_id = %s AND absent_date = %s AND absent_day = %s AND absent_period = %s",
                            (selected_teacher[0], teacher_id, absent_date, absent_day, absent_period)
                        )

                        logging.info(f"Reassigned {selected_teacher[1]} from {old_class} {old_section} to {class_name} {section} for substitution on {absent_day}, {absent_period}. {old_class} {old_section} is now unassigned.")
                        continue

                if not suitable_teachers and level != 5:
                    # No suitable substitute found
                    self.db.execute_query(
                        "UPDATE timetables SET teacher_id = NULL, is_substitution = 1 WHERE class_name = %s AND section = %s AND day = %s AND period = %s",
                        (class_name, section, absent_day, absent_period)
                    )
                    self.db.execute_query(
                        "UPDATE absences SET substitute_teacher_id = NULL WHERE teacher_id = %s AND absent_date = %s AND absent_day = %s AND absent_period = %s",
                        (teacher_id, absent_date, absent_day, absent_period)
                    )
                    logging.warning(f"No suitable substitute for {class_name} {section}, {absent_day}, {absent_period}. Slot marked as Unassigned.")
                    continue

                if level != 5:
                    # Select the teacher
                    def select_key(x):
                        load_ratio = self.get_teacher_load(x[0], absent_day) / x[4] if x[4] > 0 else 0
                        same_category = 0 if SUBJECT_CATEGORIES.get(x[2], "other") == category else 1
                        return (load_ratio, same_category)

                    selected_teacher = min(suitable_teachers, key=select_key)

                    # Update timetable
                    self.db.execute_query(
                        "UPDATE timetables SET teacher_id = %s, is_substitution = 1 WHERE class_name = %s AND section = %s AND day = %s AND period = %s",
                        (selected_teacher[0], class_name, section, absent_day, absent_period)
                    )

                    # Update absence
                    self.db.execute_query(
                        "UPDATE absences SET substitute_teacher_id = %s WHERE teacher_id = %s AND absent_date = %s AND absent_day = %s AND absent_period = %s",
                        (selected_teacher[0], teacher_id, absent_date, absent_day, absent_period)
                    )

                    # Increment assigned if new assignment (not for level 5, as it's reassignment)
                    self.db.execute_query(
                        "UPDATE teachers SET assigned_periods = assigned_periods + 1 WHERE id = %s",
                        (selected_teacher[0],)
                    )

                    logging.info(f"Assigned substitute {selected_teacher[1]} (subject: {selected_teacher[2]}) at level {level} for {class_name} {section}, {absent_day}, {absent_period}")
        except mysql.connector.Error as e:
            logging.error(f"Substitution error: {e}")
            messagebox.showerror("Error", f"Failed to handle substitution: {e}")

    def open_timetable_editor(self, class_name, section):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Timetable Editor: {class_name} {section}")
        dialog.geometry("1000x600")
        dialog.configure(bg="#ffffff" if self.theme == 'light' else "#37474f")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"Timetable for {class_name} {section}", font=("Segoe UI", 16, "bold"), bg="#ffffff" if self.theme == 'light' else "#37474f", fg=self.fg_color).pack(pady=10)

        tree_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ["Period"] + DAYS
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        tree.pack(fill=tk.BOTH, expand=True)

        tree.heading("Period", text="Period")
        tree.column("Period", width=100)
        for day in DAYS:
            tree.heading(day, text=day)
            tree.column(day, width=150)

        try:
            timetable_data = {}
            for period in PERIODS:
                timetable_data[period] = {day: "" for day in DAYS}
                for day in DAYS:
                    query = """
                        SELECT t.teacher_id, t.subject_id, t.room_number
                        FROM timetables t
                        WHERE t.class_name = %s AND t.section = %s AND t.day = %s AND t.period = %s
                    """
                    results = self.db.execute_query(query, (class_name, section, day, period), fetch=True)
                    if results:
                        teacher_id, subject_id, room = results[0]
                        teacher_name = self.db.execute_query("SELECT name FROM teachers WHERE id = %s", (teacher_id,), fetch=True)[0][0] if teacher_id else "Unassigned"
                        subject = SUBJECTS[subject_id - 1]
                        timetable_data[period][day] = f"{teacher_name} ({subject})"

            for period in PERIODS:
                tree.insert("", tk.END, values=[period] + [timetable_data[period][day] for day in DAYS])

            def edit_period(event):
                item = tree.selection()
                if not item:
                    return
                period = tree.item(item)["values"][0]
                col = tree.identify_column(event.x)
                day = columns[int(col[1:]) - 1] if col != "#0" else None
                if day == "Period":
                    return
                self.edit_timetable_entry(class_name, section, day, period, dialog)

            tree.bind("<Double-1>", edit_period)

            button_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
            button_frame.pack(pady=20)
            ttk.Button(button_frame, text="Close", command=dialog.destroy, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Failed to load timetable: {e}")
            logging.error(f"Timetable editor error: {e}")

    def edit_timetable_entry(self, class_name, section, day, period, parent_dialog):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Timetable: {class_name} {section} - {day} {period}")
        dialog.geometry("400x300")
        dialog.configure(bg="#ffffff" if self.theme == 'light' else "#37474f")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"Edit {day} {period}", font=("Segoe UI", 14, "bold"), bg="#ffffff" if self.theme == 'light' else "#37474f", fg=self.fg_color).pack(pady=10)

        form_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Teacher:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=0, column=0, pady=5, sticky="e")
        teachers = self.db.execute_query("SELECT name FROM teachers WHERE is_active = 1", fetch=True)
        teacher_names = ["Unassigned"] + [t[0] for t in teachers]
        teacher_combo = ttk.Combobox(form_frame, values=teacher_names, width=22, font=("Segoe UI", 10))
        teacher_combo.grid(row=0, column=1, pady=5, padx=10)

        tk.Label(form_frame, text="Subject:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=1, column=0, pady=5, sticky="e")
        subject_combo = ttk.Combobox(form_frame, values=SUBJECTS, width=22, font=("Segoe UI", 10))
        subject_combo.grid(row=1, column=1, pady=5, padx=10)

        tk.Label(form_frame, text="Room Number:", bg="#ffffff" if self.theme == 'light' else "#37474f", fg="#455a64" if self.theme == 'light' else "#b0bec5").grid(row=2, column=0, pady=5, sticky="e")
        room_entry = tk.Entry(form_frame, width=25, font=("Segoe UI", 10))
        room_entry.grid(row=2, column=1, pady=5, padx=10)

        def save_entry():
            teacher_name = teacher_combo.get().strip()
            subject = subject_combo.get().strip()
            room = room_entry.get().strip()

            if not subject:
                messagebox.showerror("Error", "Subject is required.")
                return

            try:
                teacher_id = None if teacher_name == "Unassigned" else self.db.execute_query("SELECT id FROM teachers WHERE name = %s", (teacher_name,), fetch=True)[0][0]
                subject_id = SUBJECTS.index(subject) + 1

                if teacher_id:
                    assigned_periods = self.db.execute_query(
                        "SELECT COUNT(*) FROM timetables WHERE teacher_id = %s AND day = %s",
                        (teacher_id, day), fetch=True
                    )[0][0]
                    max_periods = self.db.execute_query(
                        "SELECT max_periods FROM teachers WHERE id = %s", (teacher_id,), fetch=True
                    )[0][0]
                    if assigned_periods >= max_periods:
                        messagebox.showerror("Error", f"{teacher_name} has reached max periods for {day}.")
                        return

                    absent_date = datetime.now().strftime("%Y-%m-%d")
                    is_absent = self.db.execute_query(
                        "SELECT COUNT(*) FROM absences WHERE teacher_id = %s AND absent_date = %s AND absent_period = %s AND is_approved = 1",
                        (teacher_id, absent_date, period), fetch=True
                    )[0][0]
                    if is_absent:
                        messagebox.showerror("Error", f"{teacher_name} is absent on {absent_date} for {period}.")
                        return

                self.db.execute_query(
                    "INSERT INTO timetables (class_name, section, day, period, teacher_id, subject_id, room_number) VALUES (%s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE teacher_id = VALUES(teacher_id), subject_id = VALUES(subject_id), room_number = VALUES(room_number)",
                    (class_name, section, day, period, teacher_id, subject_id, room)
                )
                messagebox.showinfo("Success", "Timetable entry updated.")
                dialog.destroy()
                parent_dialog.destroy()
                self.open_timetable_editor(class_name, section)
            except mysql.connector.Error as e:
                messagebox.showerror("Error", f"Failed to update timetable: {e}")
                logging.error(f"Edit timetable error: {e}")

        button_frame = tk.Frame(dialog, bg="#ffffff" if self.theme == 'light' else "#37474f")
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Save", command=save_entry, style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, style='Custom.TButton').pack(side=tk.LEFT, padx=5)

    def get_teacher_load(self, teacher_id, day):
        query = "SELECT COUNT(*) FROM timetables WHERE teacher_id = %s AND day = %s"
        return self.db.execute_query(query, (teacher_id, day), fetch=True)[0][0]

    def is_teacher_absent(self, teacher_id, date, period=None):
        if period:
            query = "SELECT COUNT(*) FROM absences WHERE teacher_id = %s AND absent_date = %s AND absent_period = %s AND is_approved = 1"
            return self.db.execute_query(query, (teacher_id, date, period), fetch=True)[0][0] > 0
        query = "SELECT COUNT(*) FROM absences WHERE teacher_id = %s AND absent_date = %s AND is_approved = 1"
        return self.db.execute_query(query, (teacher_id, date), fetch=True)[0][0] > 0

    def is_teacher_assigned(self, teacher_id, day, period):
        query = "SELECT COUNT(*) FROM timetables WHERE teacher_id = %s AND day = %s AND period = %s"
        return self.db.execute_query(query, (teacher_id, day, period), fetch=True)[0][0] > 0

    def get_previous_period_teacher(self, class_name, section, day, period_index):
        if period_index == 0:
            return None
        prev_period = PERIODS[period_index - 1]
        query = "SELECT teacher_id FROM timetables WHERE class_name = %s AND section = %s AND day = %s AND period = %s"
        result = self.db.execute_query(query, (class_name, section, day, prev_period), fetch=True)
        return result[0][0] if result else None

    def auto_generate_timetable(self):
        if not messagebox.askyesno("Confirm", "This will overwrite existing timetables. Proceed?"):
            return

        try:
            self.db.execute_query("DELETE FROM timetables")
            self.db.execute_query("UPDATE teachers SET assigned_periods = 0")
            logging.info("Cleared existing timetables and reset teacher assignments.")

            classes = self.db.execute_query(
                "SELECT class_name, section FROM classes WHERE is_active = 1", fetch=True
            )
            teachers = self.db.execute_query(
                "SELECT id, name, subject, classes, max_periods, assigned_periods FROM teachers WHERE is_active = 1",
                fetch=True
            )

            teacher_data = [
                {
                    'id': t[0],
                    'name': t[1],
                    'subject': t[2],
                    'classes': t[3].split(",") if t[3] else [],
                    'max_periods': t[4],
                    'total_assigned': 0
                }
                for t in teachers
            ]

            for class_name, section in classes:
                for day in DAYS:
                    timetable = {period: None for period in PERIODS}
                    period_indices = list(range(len(PERIODS)))
                    random.shuffle(period_indices)

                    for period_index in period_indices:
                        period = PERIODS[period_index]
                        available_teachers = [
                            t for t in teacher_data
                            if class_name in t['classes'] and
                            t['subject'] in SUBJECTS and
                            self.get_teacher_load(t['id'], day) < t['max_periods'] and
                            not self.is_teacher_assigned(t['id'], day, period)
                        ]

                        if not available_teachers:
                            logging.warning(f"No available teachers for {class_name} {section}, {day}, {period}")
                            continue

                        available_teachers.sort(key=lambda x: x['total_assigned'])
                        prev_teacher_id = self.get_previous_period_teacher(class_name, section, day, period_index)
                        preferred_teachers = [
                            t for t in available_teachers
                            if prev_teacher_id is None or t['id'] != prev_teacher_id
                        ] or available_teachers

                        if not preferred_teachers:
                            logging.warning(f"No non-consecutive teachers available for {class_name} {section}, {day}, {period}")
                            continue

                        selected_teacher = preferred_teachers[0]
                        subject_id = SUBJECTS.index(selected_teacher['subject']) + 1

                        self.db.execute_query(
                            "INSERT INTO timetables (class_name, section, day, period, teacher_id, subject_id, room_number) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (class_name, section, day, period, selected_teacher['id'], subject_id,
                             f"Room {class_name}-{section}")
                        )
                        selected_teacher['total_assigned'] += 1
                        self.db.execute_query(
                            "UPDATE teachers SET assigned_periods = assigned_periods + 1 WHERE id = %s",
                            (selected_teacher['id'],)
                        )
                        logging.info(f"Assigned {selected_teacher['name']} ({selected_teacher['subject']}) to "
                                     f"{class_name} {section}, {day}, {period}")

            # Re-apply approved absences substitutions
            absences = self.db.execute_query(
                "SELECT teacher_id, absent_date, absent_day, absent_period FROM absences WHERE is_approved = 1", fetch=True
            )
            for teacher_id, absent_date, absent_day, absent_period in absences:
                self.handle_substitution(teacher_id, absent_date, absent_day, absent_period)

            for class_name, section in classes:
                for day in DAYS:
                    for period in PERIODS:
                        query = "SELECT COUNT(*) FROM timetables WHERE class_name = %s AND section = %s AND day = %s AND period = %s"
                        count = self.db.execute_query(query, (class_name, section, day, period), fetch=True)[0][0]
                        if count == 0:
                            logging.warning(f"Timetable incomplete for {class_name} {section}, {day}, {period}")

            messagebox.showinfo("Success", "Timetable generated successfully!")
            logging.info("Timetable generation completed successfully.")
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Failed to generate timetable: {e}")
            logging.error(f"Auto generate timetable error: {e}")

    def export_timetable(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        try:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Class", "Section", "Day", "Period", "Teacher", "Subject", "Room"])
                query = """
                    SELECT t.class_name, t.section, t.day, t.period, te.name, t.subject_id, t.room_number
                    FROM timetables t
                    LEFT JOIN teachers te ON t.teacher_id = te.id
                """
                rows = self.db.execute_query(query, fetch=True)
                writer.writerows([(row[0], row[1], row[2], row[3], row[4] or "Unassigned", SUBJECTS[int(row[5])-1], row[6]) for row in rows])
            messagebox.showinfo("Success", "Timetable exported successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export timetable: {e}")
            logging.error(f"Export timetable error: {e}")

    def import_timetable(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        try:
            with open(file_path, mode='r') as file:
                reader = csv.reader(file)
                header = next(reader)
                if header != ["Class", "Section", "Day", "Period", "Teacher", "Subject", "Room"]:
                    messagebox.showerror("Error", "Invalid CSV format.")
                    return

                self.db.execute_query("DELETE FROM timetables")
                self.db.execute_query("UPDATE teachers SET assigned_periods = 0")

                for row in reader:
                    class_name, section, day, period, teacher_name, subject, room = row
                    if day not in DAYS or period not in PERIODS or class_name not in CLASSES or section not in SECTIONS:
                        continue
                    if subject not in SUBJECTS:
                        continue

                    teacher_id = None
                    if teacher_name != "Unassigned":
                        teacher_id_result = self.db.execute_query(
                            "SELECT id FROM teachers WHERE name = %s AND is_active = 1", (teacher_name,), fetch=True
                        )
                        if not teacher_id_result:
                            continue
                        teacher_id = teacher_id_result[0][0]
                        assigned_periods = self.db.execute_query(
                            "SELECT COUNT(*) FROM timetables WHERE teacher_id = %s AND day = %s",
                            (teacher_id, day), fetch=True
                        )[0][0]
                        max_periods = self.db.execute_query(
                            "SELECT max_periods FROM teachers WHERE id = %s", (teacher_id,), fetch=True
                        )[0][0]
                        if assigned_periods >= max_periods:
                            continue

                    subject_id = SUBJECTS.index(subject) + 1
                    self.db.execute_query(
                        "INSERT INTO timetables (class_name, section, day, period, teacher_id, subject_id, room_number) VALUES (%s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE teacher_id = VALUES(teacher_id), subject_id = VALUES(subject_id), room_number = VALUES(room_number)",
                        (class_name, section, day, period, teacher_id, subject_id, room)
                    )
                    if teacher_id:
                        self.db.execute_query(
                            "UPDATE teachers SET assigned_periods = assigned_periods + 1 WHERE id = %s",
                            (teacher_id,)
                        )
            messagebox.showinfo("Success", "Timetable imported successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import timetable: {e}")
            logging.error(f"Import timetable error: {e}")

    def logout(self):
        self.current_user = None
        self.current_user_id = None
        self.current_user_role = None
        self.create_login_screen()

def main():
    root = tk.Tk()
    app = EduPlanPro(root)
    root.mainloop()

if __name__ == "__main__":
    main()
