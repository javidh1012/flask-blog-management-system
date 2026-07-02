# 📝 Flask Blog Management System

A full-featured Blog Management System built using **Flask** and **MongoDB** with role-based authentication, blog management, comment moderation, and an analytics dashboard.

---

# 📌 Features

## Authentication

- User Registration
- User Login & Logout
- Secure Password Hashing
- Session Management using Flask-Login

---

## Blog Management

- Create Blog Posts
- Read Blog Posts
- Edit Existing Posts
- Delete Posts
- Rich Text Editing using CKEditor
- Upload Blog Images via Image URL

---

## Comment System

- Add Comments
- Edit Comments
- Delete Comments

---

## Role-Based Access Control

The application supports three permission levels.

### 👑 Admin

- Full system access
- Create blog posts
- Edit blog posts
- Delete blog posts
- Edit comments
- Delete comments

---

### 🛡 Moderator

- Edit comments
- Delete comments

---

### ✍ User with Posting Privilege

Users can create blog posts only if their **can_post** permission is enabled.

This privilege is manually assigned through MongoDB.

---

## Dashboard

The project contains an analytics dashboard displaying:

- Total Users
- Total Blog Posts
- Total Comments
- Registered User List
- Email Provider Distribution
- Top Comment Author
- Most Commented Blog Post
- Blog Post Trend Over Time

Charts are generated using **Pandas** and **Matplotlib**.

---

# 🛠 Technologies Used

## Backend

- Python
- Flask
- Flask-Login
- Flask-WTF
- WTForms
- Flask-Bootstrap
- Flask-CKEditor
- PyMongo
- MongoDB
- Werkzeug Security
- python-dotenv

## Frontend

- HTML5
- CSS3
- Bootstrap 5
- Jinja2 Templates

## Data Analysis

- Pandas
- Matplotlib

---

# 📂 Project Structure

```
project/
│
├── app.py
├── forms.py
├── templates/
├── static/
├── .env
├── requirements.txt
└── README.md
```

---

# Database Collections

The application uses three MongoDB collections.

```
users
blogposts
comments
```

---

# User Roles

| Role | Create Post | Edit Post | Delete Post | Edit Comment | Delete Comment |
|-------|-------------|-----------|--------------|--------------|----------------|
| Admin | ✅ | ✅ | ✅ | ✅ | ✅ |
| Moderator | ❌ | ❌ | ❌ | ✅ | ✅ |
| User (can_post=True) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Normal User | ❌ | ❌ | ❌ | ❌ | ❌ |

---

# Installation

Clone the repository

```bash
git clone https://github.com/yourusername/blog-management-system.git
```

Move into the project directory

```bash
cd blog-management-system
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate the environment

Windows

```bash
.venv\Scripts\activate
```

Linux/Mac

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run MongoDB locally.

Create a `.env` file

```env
FLASK_KEY=your_secret_key
```

Run the application

```bash
python app.py
```

Open

```
http://127.0.0.1:5001
```

---

# Future Improvements

- User Profile Page
- Search Functionality
- Categories & Tags
- Like System
- User Profile Pictures
- Email Verification
- Password Reset
- Admin Panel for Role Management
- Dark Mode
- Pagination

---

# Author

**SK Mohamed Javidh**

---

## 🤝 Contributing

Contributions are welcome and greatly appreciated!

Feel free to fork this repository, customize it for your own projects, fix bugs, improve features, or add new functionality. If you make improvements, consider opening a Pull Request so everyone can benefit from your contributions.

If you encounter any issues or have suggestions, please open an issue in the repository.

Happy coding! 🚀


