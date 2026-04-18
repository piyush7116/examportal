# Online Examination Portal — Django Project
## AI-Powered Question Practice & Result Processing System

### 🗂️ Project Structure
```
examportal/
├── core/               # Django project settings & urls
├── accounts/           # User auth (Student/Teacher/Admin models)
├── student/            # Student app — exams, practice, history
├── teacher/            # Teacher app — upload questions, notifications
├── adminpanel/         # Admin app — syllabus, exams, students
├── templates/          # All HTML templates (Bootstrap 5)
│   ├── accounts/       # Login, register pages for all roles
│   ├── student/        # Student dashboard pages
│   ├── teacher/        # Teacher dashboard pages
│   ├── adminpanel/     # Admin dashboard pages
│   └── base/           # Base layout template
├── static/             # CSS, JS, images
├── manage.py
└── requirements.txt
```

---

### 🚀 Setup Instructions

#### 1. Install Python & pip
Make sure Python 3.10+ is installed.

#### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows
```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

#### 4. Run migrations
```bash
python manage.py makemigrations accounts student
python manage.py migrate
```

#### 5. Create superuser / Admin account
Two options:
- **Option A** — Use the web registration at `/admin-register/` (secret key: `ADMIN2024`)
- **Option B** — Django shell:
```bash
python manage.py shell
>>> from accounts.models import User
>>> u = User.objects.create_superuser('admin', 'admin@exam.com', 'admin123')
>>> u.role = 'admin'; u.save()
```

#### 6. Run the server
```bash
python manage.py runserver
```

#### 7. Open browser
```
http://127.0.0.1:8000/
```

---

### 👥 User Roles & Features

#### 🎓 Student
- Login with College Roll Number
- **Home** — Dashboard with stats
- **Features** — All feature cards (matches screenshot)
- **Exam Management** — Enter exam with password, timer-based exam
- **Question Practice** — Select subject → topic → practice quiz
- **History & Marks** — View all exam scores and practice sessions
- **Important Notifications** — View announcements
- **Account** — Edit profile

#### 👩‍🏫 Teacher
- Login with Employee ID
- **Home** — Dashboard
- **Send Notification** — Notify all students
- **Student Activity** — View all students' exam/practice records
- **Upload Questions** — Add practice questions by subject & topic
- **Account** — Edit profile

#### ⚙️ Admin
- Login with username/password
- **Dashboard** — Stats + quick action cards (matches screenshot)
- **Syllabus Management** — Add/Edit/Delete subjects with topics (matches screenshot)
- **Send Notifications** — Notify students
- **View Students** — All registered students
- **View Teachers** — All registered teachers
- **Create Exam** — Create exam with password, duration, marks
- **Add Questions** — Add MCQ questions to exam
- **Give Password** — Update exam passwords
- **Student Attendance** — View who took which exam

---

### 🎨 Theme
- **Colors**: Blue (Student), Yellow/Amber (Teacher), Green (Admin)
- **Framework**: Bootstrap 5.3
- **Font**: Poppins (Google Fonts)
- **Icons**: Bootstrap Icons 1.11

### 📋 Demo Credentials
| Role | Login Field | Username | Password |
|------|-------------|----------|----------|
| Admin | Username | Create via shell | your password |
| Student | Roll Number | Registered roll | your password |
| Teacher | Employee ID | Registered ID | your password |

### 🔑 Admin Registration Secret Key
`ADMIN2024`
