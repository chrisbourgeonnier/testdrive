# 🚗 TestDrive – A Classic & Prestige Car Test-Drive Booking System

**Overview**  
TestDrive is an embedded booking platform for **Richmonds**, allowing users to browse classic and prestige vehicles, request test drives, and manage bookings — all while preserving the Richmonds brand’s exclusive feel.  
It integrates an interactive calendar system, user accounts, an admin dashboard, automated inventory import from Richmonds.com.au, and a robust email notification system.

***

## 📌 Key Features

✅ **Browse vehicle catalog** — view high-resolution photos, specs, and availability for all classic and prestige models.  
✅ **Guest checkout** — book a test drive without account signup and receive email confirmation.  
✅ **User accounts & profiles** — registered users can update info, view booking history, and book faster.  
✅ **Real-time calendar integration** — see open slots and booked appointments via **FullCalendar.js**.  
✅ **Admin dashboard** — manage vehicles, bookings, and staff assignments.  
✅ **Automated inventory sync** — scrape and sync vehicles from Richmonds.com.au on demand.  
✅ **Email notifications** — send booking confirmations, updates, and staff alerts.  
✅ **Secure & scalable** — built on Python 3.12, Django 5.x, PostgreSQL/SQLite; supports AWS deployment.

***

## 💻 Tech Stack

- **Backend:** Python 3.12 + Django 5.2  
- **Database:** PostgreSQL (production) / SQLite (development)  
- **Frontend:** HTML5, CSS3, JavaScript, Django Templates, FullCalendar.js  
- **Scraping:** BeautifulSoup4, Requests  
- **Hosting:** AWS EC2, S3, Elastic Beanstalk, Lambda (optional)  
- **Other:** pip, virtualenv, pytest, django-simple-captcha

***

## 🚀 Getting Started

These steps will get the TestDrive platform running locally for development and testing.

### 1️⃣ **Clone the repository**
```bash
git clone https://github.com/yourusername/testdrive.git
cd testdrive
```

***

### 2️⃣ **Set up a virtual environment**
It’s recommended to use `venv` or `virtualenv` to isolate your environment.

```bash
python -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate      # On Windows PowerShell
```

***

### 3️⃣ **Install dependencies**
All required packages are listed in `requirements.txt`.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

***

### 4️⃣ **Configure environment variables**
Create a `.env` file in the project root with your local configuration:

```env
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_email_password_or_app_key
STAFF_NOTIFICATION_EMAIL=staff_notification@example.com
ALLOWED_HOSTS=127.0.0.1,localhost
SECRET_KEY=your_secret_key
```

*(If deploying to AWS, move sensitive variables into your cloud environment configs.)*

***

### 5️⃣ **Run migrations**
Create the database schema (SQLite by default in dev).

```bash
python manage.py migrate
```

***

### 6️⃣ **Create a superuser**
This account can log into the Django admin interface.

```bash
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

***

### 7️⃣ **Collect static files** (optional for local, required for prod)
```bash
python manage.py collectstatic
```

***

### 8️⃣ **Run the development server**
```bash
python manage.py runserver
```
Now visit the site at: **http://127.0.0.1:8000/**

***

## 🛠 How to Use

**Public Site**  
- **Home Page:** Displays list of available vehicles (`/`).
- **Vehicle Detail:** Click a vehicle to see its info, photo, and booking link.
- **Book a Test Drive:** Opens a form with FullCalendar slot picker and captcha.

**User Accounts**  
- **Login/Register:** Provided via `/accounts/login/` and `/accounts/register/`
- Registered users have pre-filled booking forms and access to booking history (future enhancements).

**Admin Site**  
- Visit `/admin/` and log in as a superuser.
- Manage **Vehicles** (manual or via **Update Inventory** button — scrapes Richmonds.com.au).
- Manage **Bookings** (list view or **See Calendar** button to view in FullCalendar).
- Bulk confirm, cancel, or complete bookings — automated emails are sent.

***

## 🔄 Import Vehicle Inventory

The admin dashboard has an **Update Inventory 🔃** button in Vehicles that runs:

```bash
python manage.py import_vehicles
```
This scrapes Richmonds.com.au’s inventory and updates/creates vehicles locally.

***

## 📩 Email Notifications

Emails are sent automatically when:
- A booking is created (customer + staff)
- Booking statuses are updated (confirmed, rescheduled, canceled)

Uses **SMTP Gmail** by default (configured in `.env`).

***

## 🧪 Running Tests

To run all tests:
```bash
pytest
```

Run a specific test module:
```bash
pytest vehicles/tests.py
pytest bookings/tests.py
```

***

## 📦 Deployment Notes

**Production Recommendations:**
- Use PostgreSQL instead of SQLite (update `DATABASES` in `settings.py`)
- Set `DEBUG = False` and configure `ALLOWED_HOSTS`
- Store secrets in `.env` or environment variables (never commit them)
- Use `collectstatic` to gather CSS/JS before deployment

***

## 📄 License
This is a study project developed for educational purposes — **not** for commercial use. Richmonds was not involved in the design of this app.

***
