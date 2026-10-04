# EduPlan Pro - Automatic Timetable Generator

EduPlan Pro is a desktop-based school timetable management system developed using **Python, Tkinter, and MySQL**.

The application is designed to simplify school timetable management by providing automatic timetable generation, teacher management, teacher attendance tracking, substitution handling, timetable import/export, user authentication, and a customizable graphical interface.

## Features

### 1. User Authentication
- Admin/user login system
- User registration
- Password hashing using SHA-256
- User roles
- Active/inactive user management
- Last-login tracking

### 2. Automatic Timetable Generation
- Automatically generates timetables for classes and sections
- Supports multiple school classes
- Supports multiple sections
- Supports Monday to Saturday
- Supports six periods per day
- Considers teacher availability and teaching limits
- Helps avoid timetable conflicts

### 3. Teacher Management
- Add teachers
- Edit teacher information
- Manage employee IDs
- Assign subjects to teachers
- Assign teachers to classes
- Set maximum periods per day
- View active teachers
- Deactivate teachers

### 4. Teacher Attendance and Absence Management
- Record teacher absences
- Select absence date and day
- Select a specific period or mark a whole-day absence
- Add absence reasons
- Track absence records
- Automatically handle affected timetable periods

### 5. Automatic Teacher Substitution
When a teacher is absent, EduPlan Pro attempts to find a suitable substitute teacher.

The substitution system considers factors such as:
- Teacher availability
- Maximum daily periods
- Teacher subject category
- Existing timetable assignments
- Class level
- Current teacher workload

If a suitable substitute cannot be found, the affected timetable slot can be marked as unassigned.

### 6. Timetable Import and Export
Timetables can be:

- Exported as CSV files
- Imported from CSV files

The CSV timetable format contains:

```text
Class, Section, Day, Period, Teacher, Subject, Room
```

### 7. Class and Section Management
The application supports:

- LKG
- UKG
- Classes 1 to 12
- Sections A, B, C, and D

Sections can also be managed through the application.

### 8. Graphical User Interface

The application uses **Tkinter** to provide a desktop graphical interface.

The interface includes:

- Login screen
- Dashboard
- Class selection
- Section selection
- Timetable editor
- Teacher management
- Attendance management
- Timetable generation
- Import/export options
- About Software section
- Theme switching

### 9. Customizable Configuration

The application creates a configuration file named:

```text
eduplan_config.ini
```

Configuration options include:

- School name
- Academic year
- Theme
- Zoom meeting ID
- Zoom password
- Zoom API key

The configuration file is created automatically when the application runs.

### 10. Logging

Application activity and errors are recorded in:

```text
eduplan.log
```

The log file helps with debugging and monitoring application errors.

---

# Technologies Used

- **Python**
- **Tkinter**
- **MySQL**
- **mysql-connector-python**
- **Pillow**
- **CSV**
- **ConfigParser**
- **JSON**
- **SHA-256 hashing**

## Python Libraries

The main external Python packages required by the project are:

```text
mysql-connector-python
Pillow
```

The Python standard library is also used for modules such as:

```text
tkinter
datetime
random
hashlib
csv
logging
configparser
json
os
re
```

---

# Project Structure

```text
AUTOMATIC-TIMETABLE-GENERATOR-USING-PYTHON-AND-TKINTER/
│
├── main.py
├── prerequisite.sql
├── requirements.txt
├── README.md
├── .gitignore
└── .env.example
```

### `main.py`

Contains the main Python application, including:

- Graphical user interface
- Database management
- Authentication
- Teacher management
- Timetable generation
- Attendance management
- Substitution logic
- CSV import/export
- Configuration management

### `prerequisite.sql`

Contains the MySQL database setup and initial database information.

The SQL setup creates the:

```text
eduplan_pro
```

database and the required tables.

### `requirements.txt`

Contains the external Python packages required to run the application.

### `README.md`

Project documentation and installation instructions.

### `.gitignore`

Contains files and folders that should not be uploaded to GitHub, such as Python cache files, log files, local configuration files, environment files, and VS Code settings.

### `.env.example`

Example configuration showing how a user can provide their own database password without publishing the actual password.

---

# Database

EduPlan Pro uses **MySQL** as its database.

The application uses the following main tables:

```text
users
teachers
classes
timetables
absences
```

The database name is:

```text
eduplan_pro
```

The `users` table stores application users and their hashed passwords.

The `teachers` table stores teacher information.

The `classes` table stores class and section information.

The `timetables` table stores generated timetable entries.

The `absences` table stores teacher absence and substitution information.

---

# Requirements

Before running the application, install:

### 1. Python

Install Python 3.x.

Check your Python installation:

```bash
python --version
```

### 2. MySQL

Install MySQL Server and make sure the MySQL service is running.

You can use MySQL Workbench to execute the SQL setup file.

### 3. Python Dependencies

Open a terminal inside the project folder and run:

```bash
python -m pip install -r requirements.txt
```

---

# Database Setup

## Step 1 - Start MySQL

Make sure your MySQL Server is running.

## Step 2 - Open MySQL Workbench

Open MySQL Workbench and connect to your local MySQL server.

## Step 3 - Run the SQL setup

Open:

```text
prerequisite.sql
```

in MySQL Workbench.

Execute the SQL script.

This creates the required:

```text
eduplan_pro
```

database and its tables.

---

# Running the Application

After installing Python dependencies and configuring MySQL, open a terminal in the project folder.

Run:

```bash
python main.py
```

The EduPlan Pro login window should open.

---

# Default Application Login

The application contains a default administrator account:

```text
Username: admin
Password: admin123
```

After logging in, users can access the timetable management dashboard.

**For a production deployment, change the default credentials and use stronger authentication.**

---

# Using the Application

A typical workflow is:

```text
Start Application
       ↓
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
Handle Teacher Substitution
       ↓
Export Timetable
```

---

# Timetable Generation

The automatic timetable generator works with:

- Days
- Periods
- Classes
- Sections
- Teachers
- Subjects
- Teacher workload
- Teacher class assignments

The application attempts to generate a timetable while respecting the available teachers and timetable constraints.

---

# CSV Export

Generated timetables can be exported to CSV.

The exported file contains:

```text
Class
Section
Day
Period
Teacher
Subject
Room
```

This allows timetable information to be opened and processed using spreadsheet applications.

---

# CSV Import

Previously exported timetable files can also be imported.

The application validates:

- Class
- Section
- Day
- Period
- Subject
- Teacher
- Teacher workload

Invalid timetable entries are skipped.

---

# Security

This project uses SHA-256 hashing for application passwords before storing them in the database.

However, this project is intended primarily as an educational/project application.

Before deploying it in a real school environment:

- Do not publish database passwords.
- Do not commit `.env` files.
- Do not use the MySQL root account for the application.
- Create a dedicated MySQL user with limited permissions.
- Change the default application password.
- Use stronger password hashing such as Argon2 or bcrypt.
- Store database credentials securely.
- Review database permissions and input validation.

**Never upload your real MySQL password to GitHub.**

---

# Configuration and Sensitive Files

The following files are intentionally excluded from Git:

```text
.env
*.ini
*.log
```

The application may generate local configuration and log files when it runs.

Users should create their own local configuration rather than sharing credentials or private API keys.

---

# Troubleshooting

## `ModuleNotFoundError: No module named 'mysql'`

Install the MySQL connector:

```bash
python -m pip install mysql-connector-python
```

## `ModuleNotFoundError: No module named 'PIL'`

Install Pillow:

```bash
python -m pip install Pillow
```

## MySQL connection error

Check that:

1. MySQL Server is running.
2. The MySQL username is correct.
3. Your MySQL password is correct.
4. The database configuration is correct.
5. The `eduplan_pro` database is available.

## Application does not start

Try:

```bash
python main.py
```

and check the terminal output for the error.

You can also check:

```text
eduplan.log
```

for application errors.

---

# Future Improvements

Possible future improvements include:

- Web-based version
- Mobile application
- Improved timetable optimization
- Better password security
- Dedicated database user instead of MySQL root
- Cloud database support
- Email/SMS notifications
- Advanced teacher availability management
- PDF timetable generation
- Role-based permissions
- Backup and restore functionality
- Improved conflict detection
- Deployment packages for Windows

---

# Version

```text
EduPlan Pro
Version 1.0.0
```

---

# Project Purpose

EduPlan Pro was developed as a school timetable management application to reduce the manual effort involved in creating and maintaining school schedules.

The project combines a graphical user interface, database management, scheduling logic, teacher management, attendance tracking, and automatic substitution into a single desktop application.

---

# Author

Developed by:

**Kishore, Roopa, and Mohan**

---

# License

This project does not currently specify an open-source license.

If you intend to allow others to freely use, modify, and distribute the project, consider adding an appropriate open-source license such as the MIT License.