# Comunication_LTD — Worker Portal

CS Cyber Course Final Project — Django + MySQL worker portal for a fictional telecom company.

Two versions are included:
- `version_secure/` — fully secure implementation (Part A)
- `version_vulnerable/` — intentionally vulnerable for SQLi + XSS demo (Part B)

---

## Requirements

- Python 3.10+
- Docker Desktop (or Podman) — for the MySQL database
- Git

---

## Quick Start (version_secure)

### 1. Clone and enter the project

```bash
git clone https://github.com/shaked-shlomo/CS-Project-Communication_Ltd.git
cd CS-Project-Communication_Ltd/version_secure
```

### 2. Set up Python environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

The default values in `.env` work with the Docker setup below — no changes needed unless you want email support:

```
SECRET_KEY=dev-secret-key-change-in-production
DB_NAME=comunication_ltd
DB_USER=root
DB_PASSWORD=root
DB_HOST=127.0.0.1
DB_PORT=3306
EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
```

> **Email (optional):** To enable forgot-password emails, generate a Gmail App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) and set it as `EMAIL_HOST_PASSWORD`.

### 4. Start the database

```bash
docker compose up -d
```

This starts a MySQL 8.0 container on port 3306. To stop it: `docker compose down`.
To stop and wipe all data: `docker compose down -v`.

> **Podman users:** use `podman-compose up -d` instead.

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create an admin account

```bash
python manage.py create_admin
```

Enter a username, email, and password when prompted. Password must be at least 10 characters with uppercase, lowercase, digit, and special character.

### 7. Run the server

```bash
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) and log in with the admin account.

---

## Connecting to the Database Directly (optional)

**Shell inside the container:**
```bash
docker exec -it comunication_ltd_db mysql -u root -proot comunication_ltd
```

**GUI client** (TablePlus, DBeaver, MySQL Workbench):

| Field    | Value            |
|----------|------------------|
| Host     | 127.0.0.1        |
| Port     | 3306             |
| User     | root             |
| Password | root             |
| Database | comunication_ltd |

---

## Setting Up version_vulnerable (Part B)

The vulnerable version runs on a separate port and database so both can run at the same time.

```bash
cd version_vulnerable
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

In `.env`, change `DB_NAME` to `comunication_ltd_vuln`.

In `docker-compose.yml`, change the port to `3307:3306`.

Then:
```bash
docker compose up -d
python manage.py migrate
python manage.py create_admin
python manage.py runserver 8001
```

Open [http://localhost:8001](http://localhost:8001).

---

## Demonstrating the Attacks (Part B)

Run both versions at the same time: `localhost:8000` = secure, `localhost:8001` = vulnerable.

### SQL Injection

On the **vulnerable** version, go to the login page and enter:

| Field    | Value              |
|----------|--------------------|
| Username | `' OR '1'='1' --`  |
| Password | *(leave empty)*    |

You will be logged in without valid credentials. The same input on the secure version returns "User does not exist".

### Stored XSS

On the **vulnerable** version, log in and go to **Add Customer**. Enter this as the First Name:

```
<script>alert('XSS!')</script>
```

Then go to **Customer List** — an alert box fires. On the secure version, the same input displays as plain text.

---

## Running Tests

```bash
cd version_secure
source venv/bin/activate
pytest -v
```

---

## Password Policy

All rules live in `password_config.json`. Edit the file to change policy instantly — no server restart needed.

```json
{
  "min_length": 10,
  "require_uppercase": true,
  "require_lowercase": true,
  "require_digits": true,
  "require_special": true,
  "history_limit": 3,
  "max_login_attempts": 3,
  "dictionary": ["password", "123456", "qwerty", "comunication", "letmein", "admin", "welcome"]
}
```

---

## Team

| Student | Branch | Responsibilities |
|---------|--------|-----------------|
| Student 1 | `feature/backend-foundation` | Models, password utilities, project setup |
| Student 2 | `feature/auth-infrastructure` | Decorators, context processor, base template, URLs |
| Student 3 | `feature/login-and-recovery` | Login, logout, forgot/reset password |
| Student 4 | `feature/worker-management` | Register worker, change password, create_admin |
| Student 5 | `feature/customers-and-vuln` | Customer list/add, full vulnerable version |
