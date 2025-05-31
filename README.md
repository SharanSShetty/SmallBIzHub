# SmallBIzHub 🏪 – Business Directory Web App

**SmallBiz** is a Django-based web application designed to help users discover, like, and interact with small businesses. The platform allows business owners to register and showcase their shops, while users can browse, search, and like businesses.

## 🚀 Features

- 🔐 Admin and User login/registration (Manual + Google OAuth2)
- 🏬 Business owner dashboard to manage their listings
- 📸 Upload multiple business images
- ✅ Admin approval system for new businesses
- 🔍 Search by business name, shop name, and address
- ❤️ Like/Unlike functionality for businesses
- 📧 Email notifications on approval/rejection and welcome messages

## 🧩 Tech Stack

- **Backend**: Python, Django
- **Frontend**: HTML, CSS, JavaScript (no frontend framework used)
- **Database**: SQLite (default Django DB)
- **Email**: Gmail SMTP for sending notifications
- **Auth**: Manual auth & Google OAuth2 integration

## 📂 Project Structure

```
mini/
├── Business/            # App for managing businesses
├── user/                # App for user authentication
├── controll/            # Admin control and business approval
├── owner/               # Templates for UI (admin, user, business)
├── manage.py            # Django entry point
└── db.sqlite3           # SQLite database
```

## 🔧 Setup Instructions

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/smallbiz.git
   cd smallbiz/mini
   ```

2. **Install dependencies**
   ```bash
   pip install django
   ```

3. **Run the server**
   ```bash
   python manage.py runserver
   ```

4. **Open in browser**
   ```
   http://127.0.0.1:8000/
   ```

## 📬 Contact

For any queries or contributions, reach out to the project owner via email.
