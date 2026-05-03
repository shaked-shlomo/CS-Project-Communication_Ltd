# Comunication_LTD — Developer Guide

**CS Cyber Course — Final Project**
**Group of 5 | Django + MySQL**

---

## Table of Contents

1. [What We Built](#1-what-we-built)
2. [Project Structure](#2-project-structure)
3. [Database Design](#3-database-design)
4. [How Authentication Works](#4-how-authentication-works)
5. [Password Policy & Config File](#5-password-policy--config-file)
6. [Forgot Password Flow](#6-forgot-password-flow)
7. [Attack: SQL Injection (SQLi)](#7-attack-sql-injection-sqli)
8. [Attack: Stored XSS](#8-attack-stored-xss)
9. [The Two Versions](#9-the-two-versions)

---

## 1. What We Built

A **workers' portal** for a fictional telecom company called **Comunication_LTD**.

The company sells internet packages to customers. Workers log in to this portal to manage those customers. There are two types of workers:

| Role | What they can do |
|---|---|
| **Admin** | Create new worker accounts, add/view customers |
| **Worker** | Add and view customers |

Customers of the telecom company are **not** users of this portal. Workers manage customer records on their behalf.

### Screens

| Screen | Who can access |
|---|---|
| Login | Everyone (unauthenticated) |
| Forgot Password | Everyone (unauthenticated) |
| Reset Password | Everyone with a valid token |
| Customer List | All logged-in workers |
| Add Customer | All logged-in workers |
| Change Password | All logged-in workers |
| Register New Worker | Admins only |

---

## 2. Project Structure

```
Comunication_Ltd/
├── version_secure/           ← The safe version (submit this as the main version)
│   └── comunication_ltd/
│       ├── accounts/         ← Worker auth: login, register, change password, forgot password
│       │   ├── views.py
│       │   ├── models.py
│       │   └── urls.py
│       ├── customers/        ← Customer management: add, list
│       │   ├── views.py
│       │   ├── models.py
│       │   └── urls.py
│       ├── templates/        ← HTML templates (shared base + per-screen)
│       ├── static/           ← Bootstrap CSS
│       ├── password_config.json
│       └── settings.py
│
├── version_vulnerable/       ← The intentionally broken version (for Part B demo)
│   └── comunication_ltd/
│       └── (same structure — only views.py files differ)
│
└── docs/
    ├── developer-guide.md    ← this file
    └── superpowers/specs/    ← design spec
```

The two versions are **identical in structure**. The only differences are in specific lines inside `views.py` and one template file. This makes it easy to compare them side by side.

---

## 3. Database Design

### What is a model?

A model is a Python class that represents a database table. Each attribute on the class is a column in that table.

```python
class Worker(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField()
    role = models.CharField(max_length=10)
```

This tells Django: create a table called `worker` with columns `username`, `email`, and `role`. When you call `worker.save()`, Django runs the `INSERT` SQL for you — you never write SQL directly for this.

Running `python manage.py migrate` is what actually creates these tables in MySQL.

---

We use **MySQL** with four tables. Here is what each one stores and why.

### `Worker` table
Stores every employee of Comunication_LTD who has access to the portal.

| Column | Type | Purpose |
|---|---|---|
| id | int | Primary key |
| username | varchar | Login username |
| email | varchar | For forgot-password emails |
| role | varchar | `'admin'` or `'worker'` |
| hashed_password | varchar | HMAC-SHA256 of their password |
| salt | varchar | Random value used in the HMAC |
| login_attempts | int | How many times they've failed to log in |
| is_locked | boolean | True if they've exceeded the attempt limit |

> **Why salt?** If two workers have the same password, their hashed values will look completely different because each salt is unique. This means if the database is stolen, an attacker can't easily spot duplicate passwords or use precomputed hash tables.

### `Customer` table
Stores the telecom company's clients managed by workers.

| Column | Type | Purpose |
|---|---|---|
| id | int | Primary key |
| first_name | varchar | Customer's first name |
| last_name | varchar | Customer's last name |
| id_number | varchar | National ID |
| phone | varchar | Phone number |
| package | varchar | Internet package name |
| created_by | int (FK) | Which worker added this customer |

### `PasswordHistory` table
Stores the last N hashed passwords for each worker so they can't reuse recent ones.

| Column | Type | Purpose |
|---|---|---|
| id | int | Primary key |
| worker | int (FK) | Which worker this belongs to |
| hashed_password | varchar | The old hashed password |
| salt | varchar | The salt used for that entry |
| created_at | datetime | When it was set |

> Each historical entry keeps its own salt because the password was originally hashed with that specific salt. To check if a new password matches an old one, we hash the new password using the old entry's salt and compare.

### `PasswordResetToken` table
Stores the one-time tokens used in the forgot-password flow.

| Column | Type | Purpose |
|---|---|---|
| id | int | Primary key |
| worker | int (FK) | Which worker requested the reset |
| token | varchar | SHA-1 hash of the random value sent by email |
| created_at | datetime | When it was generated |
| is_used | boolean | True once the worker has used it |

---

## 4. How Authentication Works

We do **not** use Django's built-in login system. We manage authentication ourselves using sessions. Here is the full flow:

### Login

```
Worker enters username + password
        ↓
Look up username in the Worker table
        ↓
  Not found? → "User does not exist"
        ↓
Compute HMAC-SHA256(entered_password, stored_salt)
        ↓
  Doesn't match stored hash? → "Incorrect password" + increment login_attempts
        ↓
  login_attempts >= max? → lock account → "Account locked"
        ↓
  Match! → store worker.id in session → redirect to home
```

### Session tracking

After a successful login we store the worker's ID in Django's session:

```python
request.session['worker_id'] = worker.id
```

Every protected view checks for this at the top:

```python
def some_view(request):
    worker_id = request.session.get('worker_id')
    if not worker_id:
        return redirect('/login/')
    worker = Worker.objects.get(id=worker_id)
    ...
```

Admin-only views additionally check the role:

```python
    if worker.role != 'admin':
        return redirect('/customers/')
```

### Password storage — HMAC + Salt

When a worker registers or changes their password:

```python
import hmac, hashlib, secrets

salt = secrets.token_hex(16)                          # random 32-char hex string
hashed = hmac.new(
    salt.encode(),
    password.encode(),
    hashlib.sha256
).hexdigest()

worker.salt = salt
worker.hashed_password = hashed
worker.save()
```

The plaintext password is **never stored** anywhere.

---

## 5. Password Policy & Config File

All password rules are stored in `password_config.json`:

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

This file is **read from disk every time** a password is validated — not cached at startup. So changing a value takes effect immediately on the next request.

### Validation logic (runs on register + change password)

```python
import json, re

def load_config():
    with open('password_config.json') as f:
        return json.load(f)

def validate_password(password, worker=None):
    config = load_config()
    errors = []

    if len(password) < config['min_length']:
        errors.append(f"Password must be at least {config['min_length']} characters.")

    if config['require_uppercase'] and not re.search(r'[A-Z]', password):
        errors.append("Password must contain an uppercase letter.")

    if config['require_lowercase'] and not re.search(r'[a-z]', password):
        errors.append("Password must contain a lowercase letter.")

    if config['require_digits'] and not re.search(r'\d', password):
        errors.append("Password must contain a digit.")

    if config['require_special'] and not re.search(r'[^a-zA-Z0-9]', password):
        errors.append("Password must contain a special character.")

    if password.lower() in [w.lower() for w in config['dictionary']]:
        errors.append("Password is too common.")

    # History check
    if worker:
        history = PasswordHistory.objects.filter(worker=worker).order_by('-created_at')[:config['history_limit']]
        for entry in history:
            old_hash = hmac.new(entry.salt.encode(), password.encode(), hashlib.sha256).hexdigest()
            if old_hash == entry.hashed_password:
                errors.append("You cannot reuse a recent password.")
                break

    return errors
```

---

## 6. Forgot Password Flow

```
1. Worker goes to /forgot-password/ and enters their username
2. System finds their email from the Worker table
3. System generates a random value:
       raw_token = secrets.token_hex(20)
4. System SHA-1 hashes it and stores the hash in PasswordResetToken:
       stored_token = hashlib.sha1(raw_token.encode()).hexdigest()
5. System emails the raw_token to the worker's email address
6. Worker opens email, copies the raw value, goes to /reset-password/
7. Worker enters the raw value into the form
8. System SHA-1 hashes what they typed:
       submitted_hash = hashlib.sha1(submitted.encode()).hexdigest()
9. System looks for a matching, unused token in the DB
10. Match found → mark token as used → allow worker to set a new password
```

> **Why SHA-1 here?** The assignment specifies it. In a real system you would use a longer random token without hashing at all (the randomness is the security, not the hash). But SHA-1 is demonstrated here as required by the rubric.

---

## 7. Attack: SQL Injection (SQLi)

### What is it?

SQL Injection happens when user input is pasted directly into a SQL query as a string, and the database interprets part of that input as SQL commands.

Our login query in the **vulnerable version** looks like this:

```python
# VULNERABLE — do not use in production
query = "SELECT * FROM accounts_worker WHERE username = '" + username + "'"
cursor.execute(query)
```

If the worker types a normal username like `alice`, the query becomes:
```sql
SELECT * FROM accounts_worker WHERE username = 'alice'
```
Fine. But what if the attacker types this as their username:

```
' OR '1'='1
```

The query becomes:
```sql
SELECT * FROM accounts_worker WHERE username = '' OR '1'='1'
```

`'1'='1'` is always true, so this returns **every row** in the table. The attacker is now logged in as the first worker in the database — without knowing any password.

### Where this appears in the vulnerable version

| Screen | What can be attacked |
|---|---|
| Login (`accounts/views.py`) | Bypass authentication entirely |
| Register (`accounts/views.py`) | Inject into the INSERT query |
| Add Customer (`customers/views.py`) | Inject into the INSERT query |

### The fix — Parameterized queries

Instead of building the SQL string yourself, you pass the values separately:

```python
# SECURE — parameterized query
query = "SELECT * FROM accounts_worker WHERE username = %s"
cursor.execute(query, [username])
```

The database driver handles escaping. The `%s` is a placeholder — the user's input is **never interpreted as SQL**. Even if they type `' OR '1'='1`, it's treated as a literal string to search for, not as SQL code.

### Side-by-side code comparison

**Vulnerable login (version_vulnerable):**
```python
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # VULNERABLE: string concatenation — open to SQL injection
        query = "SELECT * FROM accounts_worker WHERE username = '" + username + "'"
        cursor.execute(query)
        row = cursor.fetchone()
        ...
```

**Secure login (version_secure):**
```python
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # SECURE: parameterized query — input is never interpreted as SQL
        query = "SELECT * FROM accounts_worker WHERE username = %s"
        cursor.execute(query, [username])
        row = cursor.fetchone()
        ...
```

The only difference is one line. That one line is the entire vulnerability.

---

## 8. Attack: Stored XSS

### What is it?

XSS (Cross-Site Scripting) happens when user input is saved to the database and then displayed on a page as raw HTML, allowing an attacker to inject JavaScript that runs in other users' browsers.

The word **"Stored"** means the attack payload is stored in the database, not just passed in the URL. This makes it more dangerous because it affects every user who loads the page.

### The attack

A worker opens "Add Customer" and types this as the customer's first name:

```
<script>alert('You have been hacked!')</script>
```

This gets saved to the `Customer` table as-is. Later, when any worker opens the customer list, the page renders:

```html
<td><script>alert('You have been hacked!')</script></td>
```

The browser sees a `<script>` tag and **executes it**. Every worker who views the customer list triggers the script.

In a real attack, instead of `alert()`, the script could steal session cookies, redirect to a phishing page, or silently exfiltrate data.

### Where this appears in the vulnerable version

In `customers/templates/customer_list.html`:

```html
<!-- VULNERABLE: |safe tells Django to skip encoding — raw HTML is rendered -->
<td>{{ customer.first_name|safe }}</td>
<td>{{ customer.last_name|safe }}</td>
```

### The fix — Encoding special characters

Before putting text on the page, encode the characters that have special meaning in HTML:

| Character | Encoded as | Meaning |
|---|---|---|
| `<` | `&lt;` | Less-than sign (not a tag opener) |
| `>` | `&gt;` | Greater-than sign (not a tag closer) |
| `"` | `&quot;` | Double quote (not an attribute delimiter) |
| `&` | `&amp;` | Ampersand (not the start of an entity) |

So `<script>alert('hacked!')</script>` becomes:
```
&lt;script&gt;alert('hacked!')&lt;/script&gt;
```

The browser displays this as plain text on screen. It never executes it.

Django does this automatically by default. The only reason the vulnerable version is vulnerable is because we explicitly told Django to skip encoding with `|safe`.

### Side-by-side template comparison

**Vulnerable (version_vulnerable) — `customer_list.html`:**
```html
<!-- VULNERABLE: |safe disables encoding — script tags will execute -->
<td>{{ customer.first_name|safe }}</td>
```

**Secure (version_secure) — `customer_list.html`:**
```html
<!-- SECURE: Django auto-escaping encodes special characters into HTML entities -->
<!-- e.g. < becomes &lt;  >  becomes &gt;  — browser displays text, never executes it -->
<td>{{ customer.first_name }}</td>
```

Removing `|safe` is the entire fix. Django's default behavior is safe — the vulnerability was introduced by overriding it.

---

## 9. The Two Versions

### What is different

| File | Vulnerable version | Secure version |
|---|---|---|
| `accounts/views.py` | Login, Register use string-concatenated SQL | Login, Register use parameterized SQL |
| `customers/views.py` | Add Customer uses string-concatenated SQL | Add Customer uses parameterized SQL |
| `customers/templates/customer_list.html` | `{{ name\|safe }}` — raw HTML output | `{{ name }}` — auto-escaped output |

### What is the same

Everything else is identical between the two versions:
- Password hashing (HMAC + Salt)
- Password policy enforcement (config file)
- Login attempt limiting
- Forgot password flow (SHA-1 token + email)
- Database models
- URL routes
- Bootstrap UI
- Admin/worker role logic

### How to demo Part B to the grader

**SQLi demo (on the vulnerable version):**
1. Go to `/login/`
2. In the username field type: `' OR '1'='1' --`
3. Leave the password field empty
4. You will be logged in without valid credentials

**Stored XSS demo (on the vulnerable version):**
1. Log in normally
2. Go to Add Customer
3. In the First Name field type: `<script>alert('XSS')</script>`
4. Submit the form
5. Go to the Customer List page
6. An alert box will pop up in the browser

**Proving the fix (on the secure version):**
1. Repeat the same steps on `version_secure`
2. The SQLi attempt will fail — the query returns no results
3. The XSS payload will appear as plain text on the customer list, never executing
