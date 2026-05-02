# Comunication_LTD — Worker Portal

CS Cyber Course Final Project — Django + MySQL worker portal for a fictional telecom company.

## Project Structure

```
Comunication_Ltd/
├── version_secure/      ← Part A: fully secure implementation
├── version_vulnerable/  ← Part B: intentionally vulnerable (SQLi + XSS demo)
└── docs/
    ├── developer-guide.md          ← system overview, attack explanations, code comparisons
    ├── superpowers/specs/          ← design spec
    └── superpowers/plans/          ← implementation plan
```

---

## Requirements

- Python 3.10+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- Git

---

## Setup — version_secure

### 1. Clone the repo

```bash
git clone https://github.com/shaked-shlomo/CS-Project-Communication_Ltd.git
cd CS-Project-Communication_Ltd
```

### 2. Create a virtual environment and install dependencies

```bash
cd version_secure
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values. For the default Docker setup below, use these:

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

> **Gmail setup:** To enable the forgot-password email feature, create a Gmail App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) and use it as `EMAIL_HOST_PASSWORD`.

### 4. Start the MySQL database

```bash
docker compose up -d
```

This starts a MySQL 8.0 container on port 3306. The database `comunication_ltd` is created automatically.

To stop it:
```bash
docker compose down
```

To stop and delete all data:
```bash
docker compose down -v
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create the first admin account

```bash
python manage.py create_admin
```

Enter a username, email, and a strong password when prompted.

Password requirements (set in `password_config.json`):
- Minimum 10 characters
- At least one uppercase letter, lowercase letter, digit, and special character
- Cannot be a common dictionary word

### 7. Run the development server

```bash
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) in your browser and log in with the admin account you created.

---

## Setup — version_vulnerable

The vulnerable version is identical to the secure version but uses a separate database.

```bash
cd version_vulnerable
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `DB_NAME=comunication_ltd_vuln`.

Start its database (runs on a different port to avoid conflicts):

> Update `version_vulnerable/docker-compose.yml` to use port `3307:3306`, then:

```bash
docker compose up -d
python manage.py migrate
python manage.py create_admin
python manage.py runserver 8001
```

Open [http://localhost:8001](http://localhost:8001) for the vulnerable version.

---

## Running Tests

```bash
cd version_secure
source venv/bin/activate
pytest -v
```

---

## Demonstrating the Attacks (Part B)

Run both versions side by side (`localhost:8000` = secure, `localhost:8001` = vulnerable).

### SQL Injection — Login bypass

On **localhost:8001** (vulnerable), go to the login page and enter:

| Field | Value |
|---|---|
| Username | `' OR '1'='1' --` |
| Password | *(leave empty)* |

You will be logged in without valid credentials. The same input on **localhost:8000** (secure) returns "User does not exist".

### Stored XSS — Script injection

On **localhost:8001** (vulnerable), log in and go to **Add Customer**. Enter this as the First Name:

```
<script>alert('XSS!')</script>
```

Submit, then go to **Customer List** — an alert box will fire. On **localhost:8000** (secure), the same input is displayed as plain text on the customer list page.

---

## Password Policy

All password rules are controlled by `password_config.json` — edit this file to change policy instantly (no server restart needed):

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

| Scope | Branch | Responsibilities |
|---|---|---|
| Student 1 — Backend Foundation | `feature/backend-foundation` | Models, password utilities, project setup |
| Student 2 — Auth Infrastructure | `feature/auth-infrastructure` | Decorators, context processor, base template, URLs |
| Student 3 — Login & Recovery | `feature/login-and-recovery` | Login, logout, forgot/reset password |
| Student 4 — Worker Management | `feature/worker-management` | Register worker, change password, create_admin |
| Student 5 — Customer Portal & Vuln | `feature/customers-and-vuln` | Customer list/add, full vulnerable version |
