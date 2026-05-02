# Comunication_LTD — Worker Portal Design Spec

**Date:** 2026-05-02  
**Team:** 5 CS students (cyber course final project)  
**Stack:** Python + Django + MySQL + Bootstrap

---

## Overview

A web-based workers' portal for a fictional telecom company "Comunication_LTD". Workers log in to manage the company's telecom customers. The project is submitted as two versions: one with intentional SQLi and XSS vulnerabilities (for demonstration), and one with those vulnerabilities fixed.

---

## Project Structure

```
Comunication_Ltd/
├── version_secure/
│   └── comunication_ltd/
│       ├── accounts/             # worker auth
│       ├── customers/            # customer management
│       ├── templates/            # shared HTML templates
│       ├── static/               # Bootstrap + minimal CSS
│       ├── password_config.json  # admin-managed password policy
│       └── settings.py
└── version_vulnerable/
    └── (same structure, with vulnerable SQL/XSS code)
```

Both versions share identical structure and screens. The only differences are in the SQL query style and HTML output escaping.

---

## Django Apps

### `accounts`
Handles all worker authentication:
- Login
- Admin-only worker registration
- Change password
- Forgot password / reset password

### `customers`
Handles telecom customer management:
- Add new customer
- List customers

---

## Worker Roles

Two roles stored in a `Worker` profile model (OneToOne with Django's built-in `User`):
- `admin` — can create new worker accounts, manage customers
- `worker` — can manage customers only

Role is set by the admin at worker creation time. Regular workers cannot self-register.

---

## Database Models

### `Worker` (extends Django User via OneToOne)
| Field | Type | Notes |
|---|---|---|
| user | OneToOneField(User) | username and email only — Django User password field is set to unusable |
| role | CharField | `'admin'` or `'worker'` |
| hashed_password | CharField | HMAC-SHA256(password, salt) |
| salt | CharField | random salt for this worker's password |
| login_attempts | IntegerField | failed login counter, default 0 |
| is_locked | BooleanField | locked after max attempts, default False |

### `Customer`
| Field | Type | Notes |
|---|---|---|
| id | AutoField | primary key |
| first_name | CharField | |
| last_name | CharField | |
| id_number | CharField | national ID |
| phone | CharField | |
| package | CharField | internet package name |
| created_by | ForeignKey(Worker) | which worker added this customer |

### `PasswordHistory`
| Field | Type | Notes |
|---|---|---|
| worker | ForeignKey(Worker) | |
| hashed_password | CharField | HMAC-SHA256 of the password |
| salt | CharField | salt used for this entry |
| created_at | DateTimeField | auto_now_add |

Stores the last N hashed passwords per worker (N from config). Used to enforce password history policy.

### `PasswordResetToken`
| Field | Type | Notes |
|---|---|---|
| worker | ForeignKey(Worker) | |
| token | CharField | SHA-1 hash of the random value |
| created_at | DateTimeField | auto_now_add |
| is_used | BooleanField | default False |

---

## Password Config File (`password_config.json`)

Read at runtime on every password validation call — changes take effect immediately without server restart.

```json
{
  "min_length": 10,
  "require_uppercase": true,
  "require_lowercase": true,
  "require_digits": true,
  "require_special": true,
  "history_limit": 3,
  "max_login_attempts": 3,
  "dictionary": ["password", "123456", "qwerty", "comunication", "letmein", "admin"]
}
```

---

## Screens & URL Routes

### Unauthenticated
| URL | Screen | Description |
|---|---|---|
| `/login/` | Login | Username + password, enforces attempt limit |
| `/forgot-password/` | Forgot Password | Enter username → token sent to email |
| `/reset-password/` | Reset Password | Enter the token received by email + new password |

### Authenticated (all workers)
| URL | Screen | Description |
|---|---|---|
| `/customers/` | Home / Customer List | Lists all customers, "Add Customer" button |
| `/customers/add/` | Add Customer | Form to register a new telecom customer |
| `/change-password/` | Change Password | Enter current + new password |
| `/logout/` | — | Logs out and redirects to login |

### Admin only
| URL | Screen | Description |
|---|---|---|
| `/accounts/register/` | Register Worker | Create a new worker account (admin only) |

### Navbar behavior
- **Not logged in:** Login link only
- **Logged in as worker:** Home, Change Password, Logout
- **Logged in as admin:** Home, Register Worker, Change Password, Logout

---

## Security Implementation (Part A)

### Authentication — Custom Sessions (not Django's auth backend)
- Django's built-in `authenticate()` / `login()` are NOT used — password is managed manually
- Django's `User.password` is set to unusable (`set_unusable_password()`) — it's just a container for username and email
- After verifying credentials, store `worker.id` in `request.session['worker_id']` to track the logged-in worker
- A `login_required` decorator checks `request.session['worker_id']` on protected views
- An `admin_required` decorator additionally checks `worker.role == 'admin'`

### Password Storage — HMAC + Salt
- On register or password change: generate a cryptographically random `salt` (`secrets.token_hex(16)`)
- Compute `HMAC-SHA256(password, salt)` and store both on `Worker.hashed_password` and `Worker.salt`
- On login: retrieve the worker's salt, recompute HMAC, compare hashes — never compare plaintext

### Password Validation (reads `password_config.json` at runtime)
1. Minimum length check
2. Complexity: uppercase, lowercase, digits, special characters
3. Dictionary: reject if password is in the dictionary list
4. History: HMAC the new password with each historical salt, reject if it matches any of the last `history_limit` entries

### Login Attempt Limiting
- Track failed attempts in `Worker.login_attempts`
- On each failed login: increment counter
- If counter reaches `max_login_attempts`: set `Worker.is_locked = True`, show "Account locked" message
- Successful login resets counter to 0

### Forgot Password Flow
1. Worker submits username on `/forgot-password/`
2. System looks up their email from the User model
3. Generate a random value (e.g., `secrets.token_hex(16)`)
4. SHA-1 hash the random value → store in `PasswordResetToken`
5. Send the **raw** (pre-hash) random value to the worker's email via Gmail SMTP
6. Worker receives email, copies the value, goes to `/reset-password/` and enters it in a form field
7. System SHA-1 hashes the submitted value, looks up matching token in DB, marks it used, then allows setting a new password on the same page

---

## Vulnerability Demo (Part B)

### Vulnerable Version (`version_vulnerable/`)
Uses raw SQL string concatenation — no parameterization, no output escaping.

**SQLi vulnerability locations:**
- `accounts/views.py` — Login: `"SELECT * FROM accounts_user WHERE username='" + username + "'"`
- `accounts/views.py` — Register: raw INSERT with concatenated fields
- `customers/views.py` — Add Customer: raw INSERT with concatenated fields

**Stored XSS vulnerability location:**
- `customers/templates/customer_list.html` — renders customer name as raw HTML: `{{ customer.first_name|safe }}`

### Secure Version (`version_secure/`)
Fixes both vulnerability classes:

| Vulnerability | Secure Fix |
|---|---|
| SQLi on Login | `cursor.execute("SELECT ... WHERE username = %s", [username])` |
| SQLi on Register | Parameterized INSERT |
| SQLi on Add Customer | Parameterized INSERT |
| Stored XSS on customer name | Django default auto-escaping (remove `\|safe` filter) |

---

## Frontend

- **Bootstrap 5** via CDN — no custom build step
- Generic, minimal styling — company portal look without flashy animations
- Base template with navbar inherited by all pages
- Simple form-based UI — no JavaScript-heavy components

---

## Email Configuration (Gmail SMTP)

Django `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_gmail@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password'
```

Gmail credentials stored in a `.env` file (not committed to git).

---

## Constraints & Notes

- Code quality: clean and readable for CS students — no over-engineering, no advanced patterns
- Raw SQL used intentionally for Part B demo (both versions use `cursor.execute`, the only difference is parameterization)
- Django's ORM used everywhere else (model saves, lookups outside of the demo screens)
- The vulnerable version is clearly commented to indicate which lines are intentionally insecure
