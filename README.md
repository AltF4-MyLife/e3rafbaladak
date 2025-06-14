# e3rafbaladak.com - اعرف بلدك

## National Educational Initiative Platform

This is the official web platform for the Egyptian national educational initiative "اعرف بلدك" (Know Your Country). The platform aims to educate students about their country and organize school-based activities, volunteers, and national content.

## Project Overview

e3rafbaladak.com is a comprehensive platform designed to:

- Digitally organize the initiative's activities across schools
- Simplify communication between volunteers, students, and administration
- Present simplified patriotic/national educational content
- Manage schools, users, and content via admin dashboards
- Showcase student-generated media and projects

## Key Features

### 🏫 Schools Section
- School profiles with details (name, location, number of students, logo, past events)
- School coordinator dashboard for managing volunteers, reports, and activities

### 🙋 Volunteers Section
- Registration system for student volunteers
- Skills database and classification
- Automated email notifications

### 🇪🇬 National Educational Content
- Articles on constitution, geography, economy, history, diplomacy
- Interactive quizzes and competitions
- Educational videos

### 🎥 Student Media Corner
- Upload functionality for student-created content
- Public gallery with rating/commenting system
- Content moderation tools

### 📊 Admin Dashboard
- Role-based access control
- Data export capabilities (PDF/CSV)
- Platform usage statistics
- Notification system

### 📩 Support
- Technical support contact form
- Email integration

## Technical Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **Email**: Flask-Mail
- **PDF Generation**: WeasyPrint
- **Internationalization**: Support for Arabic (RTL)

## Setup Instructions

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables (see `.env.example`)
6. Initialize the database: `flask db upgrade`
7. Run the application: `python run.py`

## Project Structure

```
e3rafbaladak/
├── app/
│ ├── __init__.py
│ ├── routes/
│ │ ├── main_routes.py
│ │ ├── school_routes.py
│ │ ├── volunteer_routes.py
│ │ ├── admin_routes.py
│ │ └── content_routes.py
│ ├── models/
│ │ ├── user.py
│ │ ├── school.py
│ │ ├── volunteer.py
│ │ ├── article.py
│ │ ├── media.py
│ │ └── report.py
│ ├── templates/
│ │ ├── layout.html
│ │ ├── index.html
│ │ ├── login.html
│ │ ├── dashboard/
│ │ │ ├── admin.html
│ │ │ ├── school.html
│ │ │ └── volunteer.html
│ │ └── content/
│ │ ├── article_list.html
│ │ ├── article_view.html
│ │ ├── quiz.html
│ │ └── upload_media.html
│ ├── static/
│ │ ├── css/
│ │ ├── js/
│ │ ├── images/
│ │ └── uploads/
│ ├── forms.py
│ ├── config.py
│ ├── utils.py
│ └── email_templates/
│ └── thank_you.html
├── requirements.txt
├── run.py
└── README.md
```

## License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

## Contact

For technical support: support@e3rafbaladak.com