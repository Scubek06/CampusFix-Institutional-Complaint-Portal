# 🎓 CampusFix – Institutional Complaint Portal

## 📌 Overview

CampusFix is a web-based Institutional Complaint Management System designed to simplify the process of reporting, tracking, and resolving campus-related issues. The platform provides a centralized environment where students can submit complaints, monitor their status, and receive updates, while administrators can efficiently manage and resolve grievances through a dedicated dashboard.

The project aims to improve communication between students and institutional authorities by creating a transparent, accountable, and efficient complaint resolution process.

---

## 🚀 Features

### Student Module

* Student Registration & Login
* Secure Authentication
* Submit Complaints
* Categorize Complaints
* Track Complaint Status
* View Resolution Updates
* Manage Profile Information

### Admin Module

* Admin Authentication
* View All Complaints
* Update Complaint Status
* Assign and Manage Complaints
* Monitor Complaint Resolution Progress
* Generate Complaint Statistics
* User Management

### System Features

* Responsive User Interface
* Secure Database Management
* Centralized Complaint Tracking
* Real-Time Status Updates
* Efficient Grievance Redressal Workflow

---

## 🛠️ Technology Stack

### Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap

### Backend

* Python
* Flask Framework

### Database

* MySQL

### Version Control

* Git
* GitHub

### Deployment

* PythonAnywhere

---

## 📂 Project Structure

```text
CampusFix/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── complaint.html
│   └── admin_dashboard.html
│
├── app.py
├── database.sql
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/CampusFix.git
cd CampusFix
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MySQL Database

Create a MySQL database:

```sql
CREATE DATABASE campusfix;
```

Import the provided SQL file:

```bash
mysql -u root -p campusfix < database.sql
```

### 5. Update Database Configuration

Configure your database credentials in `app.py`.

```python
HOST = "localhost"
USER = "root"
PASSWORD = "your_password"
DATABASE = "campusfix"
```

### 6. Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

---

## 📊 System Workflow

1. Student registers and logs in.
2. Student submits a complaint.
3. Complaint is stored in the database.
4. Administrator reviews the complaint.
5. Status is updated throughout the resolution process.
6. Student receives updates and tracks progress.
7. Complaint is marked as resolved upon completion.

---

## 🎯 Project Objectives

* Digitize the complaint management process.
* Reduce delays in grievance handling.
* Improve transparency and accountability.
* Provide a user-friendly platform for students and administrators.
* Maintain a centralized repository of complaints.

---

## 🔒 Security Features

* User Authentication
* Session Management
* Input Validation
* Secure Database Storage
* Role-Based Access Control

---

## 📸 Screenshots

Add screenshots here:

### Home Page
<img width="1920" height="1020" alt="Testcase_HomePage" src="https://github.com/user-attachments/assets/211cf9af-b28a-44bc-bf88-cc81506bcd17" />


### Student Dashboard
<img width="1920" height="1016" alt="Testcase_Studentdashboard" src="https://github.com/user-attachments/assets/bd32bdbb-4edf-4ae8-a896-3380163e9063" />


### Admin Dashboard
<img width="1893" height="966" alt="Testcase_AdminDashboard" src="https://github.com/user-attachments/assets/d906c0ef-6d40-43ec-9d7e-df0a60b001fb" />


### New Complaint
<img width="1920" height="1020" alt="Testcase_NewComplaint" src="https://github.com/user-attachments/assets/befab9d9-2971-49ca-9939-81240f5289b6" />


---

## 🔮 Future Enhancements

* Email Notifications
* SMS Alerts
* Complaint Prioritization
* AI-Based Complaint Categorization
* Analytics Dashboard
* Mobile Application Support
* Multi-Department Integration

---

## 👨‍💻 Contributors

This project was developed as part of a B.Tech Mini Project.

| Name                    | Role           |
| ----------------------- | -------------- |
| Sirumalla Sai Srikaran  | Team Lead (TL) |
| Akhil Salendra          | Team Member    |
| Nelaveni Shruthi        | Team Member    |
| Vemulawada Mani Varshan | Team Member    |

---

## 🙏 Acknowledgement

We express our sincere gratitude to our faculty members, institution, and peers for their valuable guidance and support throughout the development of CampusFix.

---

## 📄 License

This project is developed for educational and academic purposes.

---

### ⭐ If you found this project useful, consider giving it a star on GitHub!
