<div align="center">

# 🗓️ EduPlan Pro

### Automatic School Timetable Generator

A desktop application for generating school timetables, managing teachers, tracking absences, and handling substitutions automatically.

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange)
![MySQL](https://img.shields.io/badge/Database-MySQL-4479A1?logo=mysql&logoColor=white)
![Version](https://img.shields.io/badge/version-1.0.0-green)

</div>

---

## 📑 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Database](#-database)
- [Installation](#-installation)
- [Usage](#-usage)
- [CSV Format](#-csv-format)
- [Configuration and Logging](#-configuration-and-logging)
- [Security Notes](#-security-notes)
- [Troubleshooting](#-troubleshooting)
- [Future Improvements](#-future-improvements)
- [Author](#-author)
- [License](#-license)

---

## 📖 About

**EduPlan Pro** is a desktop-based school timetable management system built with **Python, Tkinter, and MySQL**. It reduces the manual effort of creating and maintaining school schedules by combining a graphical interface, database management, scheduling logic, teacher management, attendance tracking, and automatic substitution in a single application.

---

## ✨ Features

### 🔐 User Authentication
- Admin/user login and registration
- Password hashing with SHA-256
- User roles and active/inactive user management
- Last-login tracking

### ⚙️ Automatic Timetable Generation
- Generates timetables for multiple classes and sections
- Supports **Monday to Saturday**, **6 periods per day**
- Considers teacher availability and teaching limits
- Helps avoid timetable conflicts

### 👩‍🏫 Teacher Management
- Add, edit, and deactivate teachers
- Manage employee IDs
- Assign subjects and classes to teachers
- Set maximum periods per day

### 📋 Attendance and Absence Management
- Record absences with date, day, and reason
- Mark a specific period or a whole-day absence
- Automatically handles affected timetable periods

### 🔄 Automatic Substitution
When a teacher is absent, EduPlan Pro finds a suitable substitute by considering:
- Teacher availability
- Maximum daily periods
- Subject category
- Existing timetable assignments
- Class level
- Current workload

If no suitable substitute is found, the slot is marked as **unassigned**.

### 📤 Import / Export
- Export timetables to **CSV**
- Import timetables from CSV (invalid entries are skipped)

### 🏫 Class and Section Management
- Supports **LKG, UKG, and Classes 1 to 12**
- Sections **A, B, C, D** (manageable from the app)

### 🖥️ Graphical Interface
Login screen, dashboard, class and section selection, timetable editor, teacher management, attendance management, import/export options, About section, and theme switching.

---

## 🛠️ Tech Stack

| Category | Tools |
|----------|-------|
| Language | Python 3.x |
| GUI | Tkinter |
| Database | MySQL |
| External Libraries | `mysql-connector-python`, `Pillow` |
| Standard Library | `tkinter`, `datetime`, `random`, `hashlib`, `csv`, `logging`, `configparser`, `json`, `os`, `re` |

---

## 📁 Project Structure

```
AUTOMATIC-TIMETABLE-GENERATOR-USING-PYTHON-AND-TKINTER/
│
├── main.py             # Main application (GUI, database, auth, scheduling, substitution)
├── prerequisite.sql    # MySQL database and table setup
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
├── .gitignore          # Files excluded from Git
└── .env.example        # Example for database credentials
```

---

## 🗄️ Database

Database name: **`eduplan_pro`**

| Table | Purpose |
|-------|---------|
| `users` | Application users and hashed passwords |
| `teachers` | Teacher information |
| `classes` | Class and section information |
| `timetables` | Generated timetable entries |
| `absences` | Teacher absences and substitution information |

---

## 🚀 Installation

### Prerequisites

- **Python 3.x**: check with `python --version`
- **MySQL Server** (running), and optionally **MySQL Workbench**

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

**2. Install dependencies**
```bash
python -m pip install -r requirements.txt
```

**3. Set up the database**
1. Start your MySQL Server.
2. Open MySQL Workbench and connect to your local server.
3. Open `prerequisite.sql` and execute it. This creates the `eduplan_pro` database and its tables.

**4. Configure your database password**

Copy `.env.example` to `.env` and add your own MySQL password.

**5. Run the application**
```bash
python main.py
```

---

## 📌 Usage

**Default login**

| Username | Password |
|----------|----------|
| `admin` | `admin123` |

> ⚠️ Change the default credentials after your first login.

**Typical workflow**

```
Login / Register
      ↓
Open Dashboard
      ↓
Add Teachers
      ↓
Manage Classes and Sections
      ↓
Generate Timetable
      ↓
View / Edit Timetable
      ↓
Manage Teacher Attendance
      ↓
Handle Substitutions
      ↓
Export Timetable
```

---

## 📄 CSV Format

Exported and imported timetables use this format:

```csv
Class,Section,Day,Period,Teacher,Subject,Room
```

During import, the application validates the class, section, day, period, subject, teacher, and teacher workload. Invalid rows are skipped.

---

## ⚙️ Configuration and Logging

- **`eduplan_config.ini`** is created automatically on first run. It stores the school name, academic year, and theme.
- **`eduplan.log`** records application activity and errors, which is useful for debugging.

Both files, along with `.env`, are excluded from Git.

---

## 🔒 Security Notes

This is primarily an **educational/project application**. Before using it in a real school:

- Do not publish database passwords or commit `.env` files
- Do not use the MySQL `root` account; create a dedicated user with limited permissions
- Change the default admin password
- Use stronger password hashing such as **Argon2** or **bcrypt**
- Store database credentials securely
- Review database permissions and input validation

---

## 🧰 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'mysql'` | `python -m pip install mysql-connector-python` |
| `ModuleNotFoundError: No module named 'PIL'` | `python -m pip install Pillow` |
| MySQL connection error | Check that the server is running, the username and password are correct, and the `eduplan_pro` database exists |
| Application does not start | Run `python main.py` and read the terminal output, then check `eduplan.log` |

---

## 🔮 Future Improvements

- [ ] Web-based version
- [ ] Mobile application
- [ ] Improved timetable optimization
- [ ] Stronger password security
- [ ] Dedicated database user
- [ ] Cloud database support
- [ ] Email/SMS notifications
- [ ] Advanced teacher availability management
- [ ] PDF timetable generation
- [ ] Role-based permissions
- [ ] Backup and restore
- [ ] Improved conflict detection
- [ ] Windows deployment package

---

## 👨‍💻 Author

**Kishore Kumar J**

---

## 📜 License

This project does not currently specify a license. If you want others to freely use, modify, and distribute it, consider adding one such as the [MIT License](https://choosealicense.com/licenses/mit/).

---

<div align="center">

⭐ If you found this project useful, consider giving it a star!

</div>
