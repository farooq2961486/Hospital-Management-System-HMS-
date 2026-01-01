# 🏥 Hospital Management System (HMS) – Python Tkinter & SQLite

## Overview
This is a **desktop-based Hospital Management System** built using **Python**, **Tkinter**, and **SQLite**.  
It allows hospital staff to manage **patients**, **medical tests**, and **user accounts**, with role-based access including an **Admin Panel** for user management.

---

## Features

### ✅ Login
- Professional login screen with **username & password**.
- Default users:
  - `admin` / `admin123` → Full access including Admin Panel
  - `hamza` / `hamza123` → Regular user
  - `muzamil` / `muzamil123` → Regular user
- Password can be shown/hidden using the **Show/Hide** button.

### ✅ Dashboard
- View **patients and their tests** in a searchable, sortable table.
- **Departments sidebar** filters tests by department.
- Live **date and time display**.
- **Print button** to print patient/test records.

### ✅ Patient Test Management
- **Add**, **Update**, **Delete** patient test records.
- Automatically adds patient info if new.
- Validates **CNIC (13 digits)**.
- Search patient or test by name.

### ✅ Admin Panel (Admin Only)
- View all users in a table.
- Add new users with username and password.
- Delete users (default users: `admin`, `hamza`, `muzamil` cannot be deleted).

---

## Installation

1. Make sure **Python 3.10+** is installed.
2. Tkinter comes pre-installed with Python.
3. Optionally, install Pillow (for image handling if needed in future):
```bash
pip install pillow

Farooq Murad
+923078113098
