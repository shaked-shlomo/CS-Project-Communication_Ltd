# Comunication_LTD Worker Portal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Django + MySQL workers' portal for Comunication_LTD with two submitted versions — one fully secure, one with intentional SQLi and Stored XSS vulnerabilities for academic demonstration.

**Architecture:** Two standalone Django projects (`version_secure/` and `version_vulnerable/`) with identical screen structures. Each has two Django apps — `accounts` (worker auth) and `customers` (customer management). Authentication is handled manually via Django sessions and a custom `Worker` model — no Django auth backend is used. Raw SQL via `cursor.execute` is used on the three demo screens so the vulnerable/secure difference is explicit; the ORM is used everywhere else.

**Tech Stack:** Python 3, Django 4.2, MySQL, mysqlclient, python-dotenv, Bootstrap 5 (CDN), pytest-django

**Design note:** The `Worker` model is standalone (no OneToOne with Django's `User`). This is simpler for CS students and avoids confusion with Django's built-in auth system, which we are intentionally not using.

---

## File Map

```
version_secure/
├── manage.py
├── requirements.txt
├── pytest.ini
├── conftest.py
├── .env                          ← DB + email credentials (not committed)
├── .env.example                  ← template committed to git
├── password_config.json
├── comunication_ltd/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/
│   ├── models.py                 ← Worker, PasswordHistory, PasswordResetToken
│   ├── utils.py                  ← hash_password, verify_password, validate_password, email helpers
│   ├── decorators.py             ← login_required, admin_required
│   ├── context_processors.py     ← injects 'worker' into every template
│   ├── views.py                  ← login, logout, register, change_password, forgot_password, reset_password
│   ├── urls.py
│   └── tests/
│       ├── test_utils.py
│       └── test_views.py
├── customers/
│   ├── models.py                 ← Customer
│   ├── views.py                  ← customer_list, add_customer
│   ├── urls.py
│   └── tests/
│       └── test_views.py
├── templates/
│   ├── base.html
│   ├── accounts/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── change_password.html
│   │   ├── forgot_password.html
│   │   └── reset_password.html
│   └── customers/
│       ├── customer_list.html
│       └── add_customer.html
└── static/
    └── css/
        └── style.css

version_vulnerable/              ← identical copy; only 4 lines differ
```

---

## Task 1: Project Setup

**Files:**
- Create: `version_secure/requirements.txt`
- Create: `version_secure/comunication_ltd/settings.py` (replace generated)
- Create: `version_secure/.env.example`
- Create: `version_secure/password_config.json`
- Create: `version_secure/pytest.ini`

- [ ] **Step 1: Create MySQL database**

Open MySQL and run:
```sql
CREATE DATABASE comunication_ltd CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

- [ ] **Step 2: Create the Django project**

```bash
cd /Users/shaked/Developer/Comunication_Ltd
python3 -m venv version_secure/venv
source version_secure/venv/bin/activate
pip install Django==4.2.7 mysqlclient==2.2.0 python-dotenv==1.0.0 pytest==7.4.3 pytest-django==4.7.0
cd version_secure
django-admin startproject comunication_ltd .
python manage.py startapp accounts
python manage.py startapp customers
```

- [ ] **Step 3: Write `requirements.txt`**

```
Django==4.2.7
mysqlclient==2.2.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-django==4.7.0
```

- [ ] **Step 4: Write `.env.example`**

```
SECRET_KEY=your-secret-key-here
DB_NAME=comunication_ltd
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
```

- [ ] **Step 5: Create `.env`** (copy `.env.example`, fill in real values — do NOT commit this file)

- [ ] **Step 6: Replace `comunication_ltd/settings.py` with**

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'accounts',
    'customers',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'comunication_ltd.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'accounts.context_processors.worker_context',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'comunication_ltd'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER', '')
```

- [ ] **Step 7: Create `password_config.json`** in `version_secure/`

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

- [ ] **Step 8: Create `pytest.ini`** in `version_secure/`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = comunication_ltd.settings
python_files = tests/test_*.py
```

- [ ] **Step 9: Add `.env` and `venv/` to `.gitignore`**

Create `version_secure/.gitignore`:
```
venv/
.env
__pycache__/
*.pyc
db.sqlite3
```

- [ ] **Step 10: Commit**

```bash
git add version_secure/
git commit -m "feat: scaffold version_secure Django project"
```

---

## Task 2: Database Models

**Files:**
- Modify: `version_secure/accounts/models.py`
- Modify: `version_secure/customers/models.py`

- [ ] **Step 1: Write `accounts/models.py`**

```python
from django.db import models


class Worker(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=[('admin', 'Admin'), ('worker', 'Worker')])
    hashed_password = models.CharField(max_length=255)
    salt = models.CharField(max_length=64)
    login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class PasswordHistory(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    hashed_password = models.CharField(max_length=255)
    salt = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class PasswordResetToken(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
```

- [ ] **Step 2: Write `customers/models.py`**

```python
from django.db import models
from accounts.models import Worker


class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    package = models.CharField(max_length=100)
    created_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
```

- [ ] **Step 3: Run migrations**

```bash
cd version_secure
source venv/bin/activate
python manage.py makemigrations accounts customers
python manage.py migrate
```

Expected output: migrations applied, all tables created including `django_session`.

- [ ] **Step 4: Commit**

```bash
git add version_secure/accounts/models.py version_secure/customers/models.py version_secure/accounts/migrations/ version_secure/customers/migrations/
git commit -m "feat: add Worker, Customer, PasswordHistory, PasswordResetToken models"
```

---

## Task 3: Password Utilities (TDD)

**Files:**
- Create: `version_secure/accounts/utils.py`
- Create: `version_secure/accounts/tests/__init__.py`
- Create: `version_secure/accounts/tests/test_utils.py`
- Create: `version_secure/conftest.py`

- [ ] **Step 1: Create test infrastructure**

Create `version_secure/conftest.py`:
```python
import pytest
import secrets
from accounts.models import Worker
from accounts.utils import hash_password


@pytest.fixture
def worker_password():
    return 'ValidPass@123'


@pytest.fixture
def admin_worker(db, worker_password):
    salt = secrets.token_hex(16)
    return Worker.objects.create(
        username='admin',
        email='admin@test.com',
        role='admin',
        hashed_password=hash_password(worker_password, salt),
        salt=salt,
    )


@pytest.fixture
def regular_worker(db, worker_password):
    salt = secrets.token_hex(16)
    return Worker.objects.create(
        username='worker1',
        email='worker1@test.com',
        role='worker',
        hashed_password=hash_password(worker_password, salt),
        salt=salt,
    )


@pytest.fixture
def worker_client(client, regular_worker):
    session = client.session
    session['worker_id'] = regular_worker.id
    session.save()
    return client


@pytest.fixture
def admin_client(client, admin_worker):
    session = client.session
    session['worker_id'] = admin_worker.id
    session.save()
    return client
```

Create `version_secure/accounts/tests/__init__.py` (empty file).

- [ ] **Step 2: Write failing tests for `accounts/tests/test_utils.py`**

```python
import pytest
import secrets
from accounts.utils import hash_password, verify_password, validate_password
from accounts.models import Worker, PasswordHistory


class TestHashPassword:
    def test_same_input_same_salt_produces_same_hash(self):
        h1 = hash_password('MyPass@1', 'somesalt')
        h2 = hash_password('MyPass@1', 'somesalt')
        assert h1 == h2

    def test_different_salts_produce_different_hashes(self):
        h1 = hash_password('MyPass@1', 'salt1')
        h2 = hash_password('MyPass@1', 'salt2')
        assert h1 != h2

    def test_different_passwords_produce_different_hashes(self):
        h1 = hash_password('MyPass@1', 'salt')
        h2 = hash_password('OtherPass@1', 'salt')
        assert h1 != h2


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        salt = secrets.token_hex(16)
        hashed = hash_password('MyPass@1', salt)
        assert verify_password('MyPass@1', salt, hashed) is True

    def test_wrong_password_returns_false(self):
        salt = secrets.token_hex(16)
        hashed = hash_password('MyPass@1', salt)
        assert verify_password('WrongPass@1', salt, hashed) is False


@pytest.mark.django_db
class TestValidatePassword:
    def test_too_short_fails(self):
        errors = validate_password('Abc@1')
        assert any('10 characters' in e for e in errors)

    def test_missing_uppercase_fails(self):
        errors = validate_password('mypassword@1')
        assert any('uppercase' in e for e in errors)

    def test_missing_lowercase_fails(self):
        errors = validate_password('MYPASSWORD@1')
        assert any('lowercase' in e for e in errors)

    def test_missing_digit_fails(self):
        errors = validate_password('MyPassword@abc')
        assert any('digit' in e for e in errors)

    def test_missing_special_char_fails(self):
        errors = validate_password('MyPassword123')
        assert any('special character' in e for e in errors)

    def test_dictionary_word_fails(self):
        errors = validate_password('password')
        assert any('common' in e for e in errors)

    def test_valid_password_returns_no_errors(self):
        errors = validate_password('StrongPass@1')
        assert errors == []

    def test_password_history_rejected(self, regular_worker):
        old_pass = 'OldPass@123'
        PasswordHistory.objects.create(
            worker=regular_worker,
            hashed_password=hash_password(old_pass, 'oldsalt'),
            salt='oldsalt',
        )
        errors = validate_password(old_pass, worker=regular_worker)
        assert any('reuse' in e for e in errors)
```

- [ ] **Step 3: Run tests — confirm they all FAIL**

```bash
cd version_secure
pytest accounts/tests/test_utils.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` since `utils.py` doesn't exist yet.

- [ ] **Step 4: Write `accounts/utils.py`**

```python
import hashlib
import hmac as hmac_module
import json
import re
import secrets

from django.conf import settings
from django.core.mail import send_mail


def load_config():
    config_path = settings.BASE_DIR / 'password_config.json'
    with open(config_path) as f:
        return json.load(f)


def hash_password(password, salt):
    return hmac_module.new(
        salt.encode(),
        password.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_password(password, salt, stored_hash):
    return hash_password(password, salt) == stored_hash


def validate_password(password, worker=None):
    from accounts.models import PasswordHistory

    config = load_config()
    errors = []

    if len(password) < config['min_length']:
        errors.append(f"Password must be at least {config['min_length']} characters long.")

    if config['require_uppercase'] and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter.")

    if config['require_lowercase'] and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter.")

    if config['require_digits'] and not re.search(r'\d', password):
        errors.append("Password must contain at least one digit.")

    if config['require_special'] and not re.search(r'[^a-zA-Z0-9]', password):
        errors.append("Password must contain at least one special character.")

    if password.lower() in [w.lower() for w in config['dictionary']]:
        errors.append("This password is too common. Please choose a different one.")

    if worker:
        limit = config['history_limit']
        history = PasswordHistory.objects.filter(worker=worker).order_by('-created_at')[:limit]
        for entry in history:
            if hash_password(password, entry.salt) == entry.hashed_password:
                errors.append(f"You cannot reuse any of your last {limit} passwords.")
                break

    return errors


def generate_reset_token():
    raw = secrets.token_hex(20)
    hashed = hashlib.sha1(raw.encode()).hexdigest()
    return raw, hashed


def send_reset_email(worker_email, raw_token):
    send_mail(
        subject='Comunication_LTD — Password Reset',
        message=(
            f'Your password reset token is:\n\n{raw_token}\n\n'
            'Go to /reset-password/ and enter this token to reset your password.\n'
            'This token can only be used once.'
        ),
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[worker_email],
    )
```

- [ ] **Step 5: Run tests — confirm they all PASS**

```bash
pytest accounts/tests/test_utils.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add version_secure/accounts/utils.py version_secure/accounts/tests/ version_secure/conftest.py
git commit -m "feat: add password hashing and validation utilities with tests"
```

---

## Task 4: Auth Decorators + Context Processor

**Files:**
- Create: `version_secure/accounts/decorators.py`
- Create: `version_secure/accounts/context_processors.py`

- [ ] **Step 1: Write `accounts/decorators.py`**

```python
from functools import wraps
from django.shortcuts import redirect
from accounts.models import Worker


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        worker_id = request.session.get('worker_id')
        if not worker_id:
            return redirect('/login/')
        try:
            request.worker = Worker.objects.get(id=worker_id)
        except Worker.DoesNotExist:
            del request.session['worker_id']
            return redirect('/login/')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        worker_id = request.session.get('worker_id')
        if not worker_id:
            return redirect('/login/')
        try:
            request.worker = Worker.objects.get(id=worker_id)
        except Worker.DoesNotExist:
            del request.session['worker_id']
            return redirect('/login/')
        if request.worker.role != 'admin':
            return redirect('/customers/')
        return view_func(request, *args, **kwargs)
    return wrapper
```

- [ ] **Step 2: Write `accounts/context_processors.py`**

```python
from accounts.models import Worker


def worker_context(request):
    worker_id = request.session.get('worker_id')
    if worker_id:
        try:
            return {'worker': Worker.objects.get(id=worker_id)}
        except Worker.DoesNotExist:
            pass
    return {'worker': None}
```

- [ ] **Step 3: Commit**

```bash
git add version_secure/accounts/decorators.py version_secure/accounts/context_processors.py
git commit -m "feat: add login_required/admin_required decorators and worker context processor"
```

---

## Task 5: Base Template + Static Files + URL Routing

**Files:**
- Create: `version_secure/templates/base.html`
- Create: `version_secure/static/css/style.css`
- Modify: `version_secure/comunication_ltd/urls.py`
- Create: `version_secure/accounts/urls.py`
- Create: `version_secure/customers/urls.py`

- [ ] **Step 1: Create `static/css/style.css`**

```css
body {
    background-color: #f4f6f9;
}

.card {
    border: none;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.navbar-brand {
    font-weight: 600;
    letter-spacing: 0.5px;
}
```

- [ ] **Step 2: Create `templates/base.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Comunication_LTD{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/customers/">Comunication_LTD</a>
            <div class="navbar-nav ms-auto">
                {% if worker %}
                    <a class="nav-link" href="/customers/">Customers</a>
                    {% if worker.role == 'admin' %}
                        <a class="nav-link" href="/accounts/register/">Register Worker</a>
                    {% endif %}
                    <a class="nav-link" href="/change-password/">Change Password</a>
                    <a class="nav-link" href="/logout/">Logout</a>
                {% else %}
                    <a class="nav-link active" href="/login/">Login</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container mt-4" style="max-width: 720px;">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
```

- [ ] **Step 3: Write `accounts/urls.py`**

```python
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
]
```

- [ ] **Step 4: Write `customers/urls.py`**

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list_view, name='customer_list'),
    path('add/', views.add_customer_view, name='add_customer'),
]
```

- [ ] **Step 5: Replace `comunication_ltd/urls.py`**

```python
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('/customers/')),
    path('', include('accounts.urls')),
    path('accounts/', include('accounts.urls')),
    path('customers/', include('customers.urls')),
]
```

- [ ] **Step 6: Commit**

```bash
git add version_secure/templates/ version_secure/static/ version_secure/comunication_ltd/urls.py version_secure/accounts/urls.py version_secure/customers/urls.py
git commit -m "feat: add base template, static files, and URL routing"
```

---

## Task 6: Login + Logout Views (TDD)

**Files:**
- Modify: `version_secure/accounts/views.py`
- Create: `version_secure/templates/accounts/login.html`
- Create: `version_secure/accounts/tests/test_views.py`

- [ ] **Step 1: Write failing tests for `accounts/tests/test_views.py`**

```python
import pytest
from accounts.models import Worker


@pytest.mark.django_db
class TestLoginView:
    def test_get_login_page_returns_200(self, client):
        response = client.get('/login/')
        assert response.status_code == 200

    def test_nonexistent_user_shows_correct_error(self, client):
        response = client.post('/login/', {'username': 'nobody', 'password': 'anything'})
        assert response.status_code == 200
        assert 'User does not exist' in response.content.decode()

    def test_wrong_password_shows_correct_error(self, client, regular_worker):
        response = client.post('/login/', {'username': 'worker1', 'password': 'WrongPass@1'})
        assert response.status_code == 200
        assert 'Incorrect password' in response.content.decode()

    def test_correct_credentials_redirect_to_customers(self, client, regular_worker, worker_password):
        response = client.post('/login/', {'username': 'worker1', 'password': worker_password})
        assert response.status_code == 302
        assert response['Location'] == '/customers/'

    def test_session_is_set_after_login(self, client, regular_worker, worker_password):
        client.post('/login/', {'username': 'worker1', 'password': worker_password})
        assert client.session.get('worker_id') == regular_worker.id

    def test_account_locked_after_max_attempts(self, client, regular_worker):
        for _ in range(3):
            client.post('/login/', {'username': 'worker1', 'password': 'WrongPass@1'})
        response = client.post('/login/', {'username': 'worker1', 'password': 'WrongPass@1'})
        assert 'locked' in response.content.decode().lower()
        regular_worker.refresh_from_db()
        assert regular_worker.is_locked is True

    def test_locked_account_cannot_login_with_correct_password(self, client, regular_worker, worker_password):
        regular_worker.is_locked = True
        regular_worker.save()
        response = client.post('/login/', {'username': 'worker1', 'password': worker_password})
        assert 'locked' in response.content.decode().lower()


@pytest.mark.django_db
class TestLogoutView:
    def test_logout_clears_session(self, worker_client):
        worker_client.get('/logout/')
        assert worker_client.session.get('worker_id') is None

    def test_logout_redirects_to_login(self, worker_client):
        response = worker_client.get('/logout/')
        assert response.status_code == 302
        assert response['Location'] == '/login/'
```

- [ ] **Step 2: Run tests — confirm they FAIL**

```bash
pytest accounts/tests/test_views.py::TestLoginView accounts/tests/test_views.py::TestLogoutView -v
```

Expected: errors because views don't exist yet.

- [ ] **Step 3: Write login and logout views in `accounts/views.py`**

```python
import hashlib
import secrets

from django.db import connection
from django.shortcuts import redirect, render

from accounts.decorators import admin_required, login_required
from accounts.models import PasswordHistory, PasswordResetToken, Worker
from accounts.utils import (
    generate_reset_token,
    hash_password,
    load_config,
    send_reset_email,
    validate_password,
    verify_password,
)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # SECURE: parameterized query — user input is never part of the SQL string
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, hashed_password, salt, is_locked, login_attempts "
                "FROM accounts_worker WHERE username = %s",
                [username],
            )
            row = cursor.fetchone()

        # NOTE: In production, a single generic error message prevents user enumeration.
        # Here we return distinct messages as required by the assignment rubric.
        if row is None:
            return render(request, 'accounts/login.html', {'error': 'User does not exist.'})

        worker_id, stored_hash, salt, is_locked, login_attempts = row

        if is_locked:
            return render(request, 'accounts/login.html', {'error': 'This account is locked. Contact an administrator.'})

        if not verify_password(password, salt, stored_hash):
            config = load_config()
            new_attempts = login_attempts + 1
            if new_attempts >= config['max_login_attempts']:
                Worker.objects.filter(id=worker_id).update(login_attempts=new_attempts, is_locked=True)
                return render(request, 'accounts/login.html', {'error': 'This account is locked. Contact an administrator.'})
            Worker.objects.filter(id=worker_id).update(login_attempts=new_attempts)
            return render(request, 'accounts/login.html', {'error': 'Incorrect password.'})

        Worker.objects.filter(id=worker_id).update(login_attempts=0)
        request.session['worker_id'] = worker_id
        return redirect('/customers/')

    return render(request, 'accounts/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('/login/')


# Placeholder stubs — will be filled in Tasks 7–9
def register_view(request):
    pass


def change_password_view(request):
    pass


def forgot_password_view(request):
    pass


def reset_password_view(request):
    pass
```

- [ ] **Step 4: Create `templates/accounts/login.html`**

```html
{% extends 'base.html' %}

{% block title %}Login — Comunication_LTD{% endblock %}

{% block content %}
<div class="card p-4 mt-5">
    <h4 class="mb-3">Worker Login</h4>

    {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
    {% endif %}

    <form method="post">
        {% csrf_token %}
        <div class="mb-3">
            <label class="form-label">Username</label>
            <input type="text" name="username" class="form-control" required autofocus>
        </div>
        <div class="mb-3">
            <label class="form-label">Password</label>
            <input type="password" name="password" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-dark w-100">Login</button>
    </form>

    <div class="mt-3 text-center">
        <a href="/forgot-password/" class="text-muted small">Forgot your password?</a>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Run tests — confirm they PASS**

```bash
pytest accounts/tests/test_views.py::TestLoginView accounts/tests/test_views.py::TestLogoutView -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add version_secure/accounts/views.py version_secure/templates/accounts/login.html version_secure/accounts/tests/test_views.py
git commit -m "feat: add login and logout views with tests"
```

---

## Task 7: Register Worker View (Admin Only)

**Files:**
- Modify: `version_secure/accounts/views.py` (replace `register_view` stub)
- Create: `version_secure/templates/accounts/register.html`

- [ ] **Step 1: Add register tests to `accounts/tests/test_views.py`**

Append to the file:
```python
@pytest.mark.django_db
class TestRegisterView:
    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get('/accounts/register/')
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_regular_worker_redirected_to_customers(self, worker_client):
        response = worker_client.get('/accounts/register/')
        assert response.status_code == 302
        assert '/customers/' in response['Location']

    def test_admin_can_access_register(self, admin_client):
        response = admin_client.get('/accounts/register/')
        assert response.status_code == 200

    def test_admin_can_create_worker(self, admin_client):
        response = admin_client.post('/accounts/register/', {
            'username': 'newworker',
            'email': 'new@test.com',
            'password': 'NewPass@123',
            'role': 'worker',
        })
        assert Worker.objects.filter(username='newworker').exists()

    def test_weak_password_shows_errors(self, admin_client):
        response = admin_client.post('/accounts/register/', {
            'username': 'newworker2',
            'email': 'new2@test.com',
            'password': 'weak',
            'role': 'worker',
        })
        assert response.status_code == 200
        assert not Worker.objects.filter(username='newworker2').exists()

    def test_duplicate_username_shows_error(self, admin_client, regular_worker):
        response = admin_client.post('/accounts/register/', {
            'username': 'worker1',
            'email': 'different@test.com',
            'password': 'ValidPass@123',
            'role': 'worker',
        })
        assert response.status_code == 200
        assert 'already' in response.content.decode().lower()
```

- [ ] **Step 2: Run register tests — confirm they FAIL**

```bash
pytest accounts/tests/test_views.py::TestRegisterView -v
```

Expected: failures because `register_view` is a stub.

- [ ] **Step 3: Replace `register_view` stub in `accounts/views.py`**

```python
@admin_required
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', 'worker')

        errors = validate_password(password)

        if Worker.objects.filter(username=username).exists():
            errors.append('Username is already taken.')
        if Worker.objects.filter(email=email).exists():
            errors.append('Email is already registered.')

        if errors:
            return render(request, 'accounts/register.html', {'errors': errors})

        salt = secrets.token_hex(16)
        hashed = hash_password(password, salt)

        # SECURE: parameterized INSERT — values are passed separately, not concatenated
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO accounts_worker "
                "(username, email, role, hashed_password, salt, login_attempts, is_locked, created_at) "
                "VALUES (%s, %s, %s, %s, %s, 0, FALSE, NOW())",
                [username, email, role, hashed, salt],
            )

        return render(request, 'accounts/register.html', {
            'success': f'Worker account for "{username}" has been created.',
        })

    return render(request, 'accounts/register.html')
```

- [ ] **Step 4: Create `templates/accounts/register.html`**

```html
{% extends 'base.html' %}

{% block title %}Register Worker — Comunication_LTD{% endblock %}

{% block content %}
<div class="card p-4">
    <h4 class="mb-3">Register New Worker</h4>

    {% if success %}
        <div class="alert alert-success">{{ success }}</div>
    {% endif %}

    {% if errors %}
        <div class="alert alert-danger">
            <ul class="mb-0">
                {% for error in errors %}
                    <li>{{ error }}</li>
                {% endfor %}
            </ul>
        </div>
    {% endif %}

    <form method="post">
        {% csrf_token %}
        <div class="mb-3">
            <label class="form-label">Username</label>
            <input type="text" name="username" class="form-control" required>
        </div>
        <div class="mb-3">
            <label class="form-label">Email</label>
            <input type="email" name="email" class="form-control" required>
        </div>
        <div class="mb-3">
            <label class="form-label">Password</label>
            <input type="password" name="password" class="form-control" required>
        </div>
        <div class="mb-3">
            <label class="form-label">Role</label>
            <select name="role" class="form-select">
                <option value="worker">Worker</option>
                <option value="admin">Admin</option>
            </select>
        </div>
        <button type="submit" class="btn btn-dark w-100">Create Worker</button>
    </form>
</div>
{% endblock %}
```

- [ ] **Step 5: Run register tests — confirm they PASS**

```bash
pytest accounts/tests/test_views.py::TestRegisterView -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add version_secure/accounts/views.py version_secure/templates/accounts/register.html
git commit -m "feat: add admin-only register worker view with tests"
```

---

## Task 8: Change Password View

**Files:**
- Modify: `version_secure/accounts/views.py` (replace `change_password_view` stub)
- Create: `version_secure/templates/accounts/change_password.html`

- [ ] **Step 1: Replace `change_password_view` stub in `accounts/views.py`**

```python
@login_required
def change_password_view(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        worker = request.worker

        if not verify_password(current_password, worker.salt, worker.hashed_password):
            return render(request, 'accounts/change_password.html', {'error': 'Current password is incorrect.'})

        errors = validate_password(new_password, worker=worker)
        if errors:
            return render(request, 'accounts/change_password.html', {'errors': errors})

        PasswordHistory.objects.create(
            worker=worker,
            hashed_password=worker.hashed_password,
            salt=worker.salt,
        )

        new_salt = secrets.token_hex(16)
        worker.hashed_password = hash_password(new_password, new_salt)
        worker.salt = new_salt
        worker.save()

        return render(request, 'accounts/change_password.html', {'success': 'Password changed successfully.'})

    return render(request, 'accounts/change_password.html')
```

- [ ] **Step 2: Create `templates/accounts/change_password.html`**

```html
{% extends 'base.html' %}

{% block title %}Change Password — Comunication_LTD{% endblock %}

{% block content %}
<div class="card p-4">
    <h4 class="mb-3">Change Password</h4>

    {% if success %}
        <div class="alert alert-success">{{ success }}</div>
    {% endif %}

    {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
    {% endif %}

    {% if errors %}
        <div class="alert alert-danger">
            <ul class="mb-0">
                {% for e in errors %}
                    <li>{{ e }}</li>
                {% endfor %}
            </ul>
        </div>
    {% endif %}

    <form method="post">
        {% csrf_token %}
        <div class="mb-3">
            <label class="form-label">Current Password</label>
            <input type="password" name="current_password" class="form-control" required>
        </div>
        <div class="mb-3">
            <label class="form-label">New Password</label>
            <input type="password" name="new_password" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-dark w-100">Change Password</button>
    </form>
</div>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add version_secure/accounts/views.py version_secure/templates/accounts/change_password.html
git commit -m "feat: add change password view"
```

---

## Task 9: Forgot Password + Reset Password Views

**Files:**
- Modify: `version_secure/accounts/views.py` (replace remaining stubs)
- Create: `version_secure/templates/accounts/forgot_password.html`
- Create: `version_secure/templates/accounts/reset_password.html`

- [ ] **Step 1: Replace `forgot_password_view` stub in `accounts/views.py`**

```python
def forgot_password_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        try:
            worker = Worker.objects.get(username=username)
            raw_token, hashed_token = generate_reset_token()
            PasswordResetToken.objects.create(worker=worker, token=hashed_token)
            send_reset_email(worker.email, raw_token)
        except Worker.DoesNotExist:
            pass  # Don't reveal whether the username exists

        return render(request, 'accounts/forgot_password.html', {
            'info': 'If that username exists, a reset token has been sent to the associated email.',
        })

    return render(request, 'accounts/forgot_password.html')
```

- [ ] **Step 2: Replace `reset_password_view` stub in `accounts/views.py`**

```python
def reset_password_view(request):
    if request.method == 'POST':
        submitted_token = request.POST.get('token', '').strip()
        new_password = request.POST.get('new_password', '')

        hashed = hashlib.sha1(submitted_token.encode()).hexdigest()

        try:
            token_obj = PasswordResetToken.objects.get(token=hashed, is_used=False)
        except PasswordResetToken.DoesNotExist:
            return render(request, 'accounts/reset_password.html', {'error': 'Invalid or already used token.'})

        worker = token_obj.worker
        errors = validate_password(new_password, worker=worker)
        if errors:
            return render(request, 'accounts/reset_password.html', {'errors': errors})

        PasswordHistory.objects.create(
            worker=worker,
            hashed_password=worker.hashed_password,
            salt=worker.salt,
        )

        new_salt = secrets.token_hex(16)
        worker.hashed_password = hash_password(new_password, new_salt)
        worker.salt = new_salt
        worker.save()

        token_obj.is_used = True
        token_obj.save()

        return redirect('/login/')

    return render(request, 'accounts/reset_password.html')
```

- [ ] **Step 3: Create `templates/accounts/forgot_password.html`**

```html
{% extends 'base.html' %}

{% block title %}Forgot Password — Comunication_LTD{% endblock %}

{% block content %}
<div class="card p-4">
    <h4 class="mb-3">Forgot Password</h4>
    <p class="text-muted">Enter your username and we'll send a reset token to your registered email.</p>

    {% if info %}
        <div class="alert alert-info">{{ info }}</div>
    {% endif %}

    <form method="post">
        {% csrf_token %}
        <div class="mb-3">
            <label class="form-label">Username</label>
            <input type="text" name="username" class="form-control" required autofocus>
        </div>
        <button type="submit" class="btn btn-dark w-100">Send Reset Token</button>
    </form>

    <div class="mt-3 text-center">
        <a href="/login/" class="text-muted small">Back to Login</a>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Create `templates/accounts/reset_password.html`**

```html
{% extends 'base.html' %}

{% block title %}Reset Password — Comunication_LTD{% endblock %}

{% block content %}
<div class="card p-4">
    <h4 class="mb-3">Reset Password</h4>
    <p class="text-muted">Enter the token you received by email and choose a new password.</p>

    {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
    {% endif %}

    {% if errors %}
        <div class="alert alert-danger">
            <ul class="mb-0">
                {% for e in errors %}
                    <li>{{ e }}</li>
                {% endfor %}
            </ul>
        </div>
    {% endif %}

    <form method="post">
        {% csrf_token %}
        <div class="mb-3">
            <label class="form-label">Reset Token</label>
            <input type="text" name="token" class="form-control" required autofocus>
        </div>
        <div class="mb-3">
            <label class="form-label">New Password</label>
            <input type="password" name="new_password" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-dark w-100">Reset Password</button>
    </form>
</div>
{% endblock %}
```

- [ ] **Step 5: Commit**

```bash
git add version_secure/accounts/views.py version_secure/templates/accounts/
git commit -m "feat: add forgot password and reset password views"
```

---

## Task 10: Customer List View

**Files:**
- Modify: `version_secure/customers/views.py`
- Create: `version_secure/templates/customers/customer_list.html`
- Create: `version_secure/customers/tests/__init__.py`
- Create: `version_secure/customers/tests/test_views.py`

- [ ] **Step 1: Write `customers/tests/test_views.py`**

```python
import pytest
from customers.models import Customer
from accounts.models import Worker


@pytest.mark.django_db
class TestCustomerListView:
    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get('/customers/')
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_authenticated_worker_can_view_list(self, worker_client):
        response = worker_client.get('/customers/')
        assert response.status_code == 200

    def test_customer_name_appears_in_list(self, worker_client, regular_worker):
        Customer.objects.create(
            first_name='Alice',
            last_name='Smith',
            id_number='123',
            phone='050-0000000',
            package='Basic',
            created_by=regular_worker,
        )
        response = worker_client.get('/customers/')
        assert 'Alice' in response.content.decode()
```

- [ ] **Step 2: Write `customers/views.py`**

```python
from django.shortcuts import redirect, render
from django.db import connection

from accounts.decorators import login_required
from customers.models import Customer


@login_required
def customer_list_view(request):
    customers = Customer.objects.all().order_by('-created_at')
    return render(request, 'customers/customer_list.html', {'customers': customers})


# Placeholder — filled in Task 11
@login_required
def add_customer_view(request):
    pass
```

- [ ] **Step 3: Create `templates/customers/customer_list.html`**

```html
{% extends 'base.html' %}

{% block title %}Customers — Comunication_LTD{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <h4 class="mb-0">Customer List</h4>
    <a href="/customers/add/" class="btn btn-dark btn-sm">+ Add Customer</a>
</div>

<div class="card">
    <table class="table table-hover mb-0">
        <thead class="table-light">
            <tr>
                <th>First Name</th>
                <th>Last Name</th>
                <th>ID Number</th>
                <th>Phone</th>
                <th>Package</th>
            </tr>
        </thead>
        <tbody>
            {% for customer in customers %}
            <tr>
                <!--
                    SECURE: Django auto-escaping is active by default.
                    Special characters are encoded into HTML entities
                    (e.g. < becomes &lt;) so no injected script can execute.
                    This is the "encoding of special characters" fix required by the rubric.
                -->
                <td>{{ customer.first_name }}</td>
                <td>{{ customer.last_name }}</td>
                <td>{{ customer.id_number }}</td>
                <td>{{ customer.phone }}</td>
                <td>{{ customer.package }}</td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="5" class="text-center text-muted py-4">No customers yet.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

- [ ] **Step 4: Run customer list tests**

```bash
pytest customers/tests/test_views.py::TestCustomerListView -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add version_secure/customers/views.py version_secure/templates/customers/customer_list.html version_secure/customers/tests/
git commit -m "feat: add customer list view with tests"
```

---

## Task 11: Add Customer View

**Files:**
- Modify: `version_secure/customers/views.py` (replace stub)
- Create: `version_secure/templates/customers/add_customer.html`

- [ ] **Step 1: Replace `add_customer_view` stub in `customers/views.py`**

```python
@login_required
def add_customer_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        id_number = request.POST.get('id_number', '').strip()
        phone = request.POST.get('phone', '').strip()
        package = request.POST.get('package', '').strip()

        # SECURE: parameterized INSERT — values are placeholders, never concatenated into SQL
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO customers_customer "
                "(first_name, last_name, id_number, phone, package, created_by_id, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, NOW())",
                [first_name, last_name, id_number, phone, package, request.worker.id],
            )

        return render(request, 'customers/add_customer.html', {
            'success': f'Customer {first_name} {last_name} was added successfully.',
        })

    return render(request, 'customers/add_customer.html')
```

- [ ] **Step 2: Create `templates/customers/add_customer.html`**

```html
{% extends 'base.html' %}

{% block title %}Add Customer — Comunication_LTD{% endblock %}

{% block content %}
<div class="card p-4">
    <h4 class="mb-3">Add New Customer</h4>

    {% if success %}
        <div class="alert alert-success">{{ success }}</div>
    {% endif %}

    <form method="post">
        {% csrf_token %}
        <div class="mb-3">
            <label class="form-label">First Name</label>
            <input type="text" name="first_name" class="form-control" required>
        </div>
        <div class="mb-3">
            <label class="form-label">Last Name</label>
            <input type="text" name="last_name" class="form-control" required>
        </div>
        <div class="mb-3">
            <label class="form-label">ID Number</label>
            <input type="text" name="id_number" class="form-control" required>
        </div>
        <div class="mb-3">
            <label class="form-label">Phone</label>
            <input type="text" name="phone" class="form-control" required>
        </div>
        <div class="mb-3">
            <label class="form-label">Internet Package</label>
            <select name="package" class="form-select">
                <option>Basic 50MB</option>
                <option>Standard 100MB</option>
                <option>Premium 500MB</option>
                <option>Ultra 1GB</option>
            </select>
        </div>
        <button type="submit" class="btn btn-dark w-100">Add Customer</button>
    </form>

    <div class="mt-3">
        <a href="/customers/" class="text-muted small">← Back to Customer List</a>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add version_secure/customers/views.py version_secure/templates/customers/add_customer.html
git commit -m "feat: add customer view with parameterized SQL insert"
```

---

## Task 12: Initial Admin Setup

**Files:**
- Create: `version_secure/accounts/management/__init__.py`
- Create: `version_secure/accounts/management/commands/__init__.py`
- Create: `version_secure/accounts/management/commands/create_admin.py`

- [ ] **Step 1: Create the management command**

Create directory structure:
```bash
mkdir -p accounts/management/commands
touch accounts/management/__init__.py
touch accounts/management/commands/__init__.py
```

Create `accounts/management/commands/create_admin.py`:
```python
import secrets

from django.core.management.base import BaseCommand

from accounts.models import Worker
from accounts.utils import hash_password, validate_password


class Command(BaseCommand):
    help = 'Create the initial admin worker account'

    def handle(self, *args, **options):
        self.stdout.write('=== Create Initial Admin ===')
        username = input('Username: ').strip()
        email = input('Email: ').strip()
        password = input('Password: ').strip()

        if Worker.objects.filter(username=username).exists():
            self.stderr.write(f'Error: username "{username}" already exists.')
            return

        errors = validate_password(password)
        if errors:
            self.stderr.write('Password does not meet requirements:')
            for e in errors:
                self.stderr.write(f'  - {e}')
            return

        salt = secrets.token_hex(16)
        Worker.objects.create(
            username=username,
            email=email,
            role='admin',
            hashed_password=hash_password(password, salt),
            salt=salt,
        )
        self.stdout.write(self.style.SUCCESS(f'Admin "{username}" created successfully.'))
```

- [ ] **Step 2: Run the command to create the first admin**

```bash
python manage.py create_admin
```

Enter a username, email, and strong password when prompted.

- [ ] **Step 3: Start the server and verify login works**

```bash
python manage.py runserver
```

Open `http://localhost:8000/login/` and log in with the admin account. Verify the navbar shows "Register Worker".

- [ ] **Step 4: Commit**

```bash
git add version_secure/accounts/management/
git commit -m "feat: add create_admin management command"
```

---

## Task 13: Create Vulnerable Version

The vulnerable version is a copy of `version_secure` with exactly **4 changes**:
1. Login query — string concatenation (SQLi)
2. Register INSERT — string concatenation (SQLi)
3. Add Customer INSERT — string concatenation (SQLi)
4. Customer list template — `|safe` filter (Stored XSS)

- [ ] **Step 1: Copy the secure version**

```bash
cd /Users/shaked/Developer/Comunication_Ltd
cp -r version_secure version_vulnerable
```

- [ ] **Step 2: Create a separate MySQL database for the vulnerable version**

```sql
CREATE DATABASE comunication_ltd_vuln CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

- [ ] **Step 3: Update `version_vulnerable/.env`**

Change `DB_NAME=comunication_ltd_vuln` and keep all other values the same.

- [ ] **Step 4: Run migrations for vulnerable version**

```bash
cd version_vulnerable
source venv/bin/activate
python manage.py migrate
python manage.py create_admin
```

- [ ] **Step 5: Introduce SQLi in `version_vulnerable/accounts/views.py` — login**

Replace the secure login query block:
```python
        # VULNERABLE: string concatenation — open to SQL injection attack
        # An attacker can type: ' OR '1'='1' -- to bypass authentication
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, hashed_password, salt, is_locked, login_attempts "
                "FROM accounts_worker WHERE username = '" + username + "'"
            )
            row = cursor.fetchone()
```

- [ ] **Step 6: Introduce SQLi in `version_vulnerable/accounts/views.py` — register**

Replace the secure INSERT block in `register_view`:
```python
        # VULNERABLE: string concatenation — open to SQL injection attack
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO accounts_worker "
                "(username, email, role, hashed_password, salt, login_attempts, is_locked, created_at) "
                "VALUES ('" + username + "', '" + email + "', '" + role + "', '"
                + hashed + "', '" + salt + "', 0, FALSE, NOW())"
            )
```

- [ ] **Step 7: Introduce SQLi in `version_vulnerable/customers/views.py` — add customer**

Replace the secure INSERT block in `add_customer_view`:
```python
        # VULNERABLE: string concatenation — open to SQL injection attack
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO customers_customer "
                "(first_name, last_name, id_number, phone, package, created_by_id, created_at) "
                "VALUES ('" + first_name + "', '" + last_name + "', '" + id_number
                + "', '" + phone + "', '" + package + "', "
                + str(request.worker.id) + ", NOW())"
            )
```

- [ ] **Step 8: Introduce Stored XSS in `version_vulnerable/templates/customers/customer_list.html`**

Replace the secure table cells:
```html
            <tr>
                <!--
                    VULNERABLE: |safe disables Django's auto-escaping.
                    If a customer's name contains <script>...</script>,
                    the browser will execute it. This is a Stored XSS vulnerability.
                -->
                <td>{{ customer.first_name|safe }}</td>
                <td>{{ customer.last_name|safe }}</td>
                <td>{{ customer.id_number }}</td>
                <td>{{ customer.phone }}</td>
                <td>{{ customer.package }}</td>
            </tr>
```

- [ ] **Step 9: Verify the vulnerable version runs**

```bash
cd version_vulnerable
python manage.py runserver 8001
```

Open `http://localhost:8001/login/` — confirm it loads.

- [ ] **Step 10: Test SQLi demo**

In the username field of the login page, enter:
```
' OR '1'='1' --
```
Leave password empty. You should be logged in without valid credentials.

- [ ] **Step 11: Test Stored XSS demo**

Log in normally, go to Add Customer, enter this as First Name:
```
<script>alert('XSS!')</script>
```
Submit. Go to Customer List. An alert box should appear.

- [ ] **Step 12: Commit**

```bash
git add version_vulnerable/
git commit -m "feat: add version_vulnerable with intentional SQLi and Stored XSS for Part B demo"
```

---

## Final Checklist

Run the full test suite on the secure version before submitting:

```bash
cd version_secure
pytest -v
```

Expected: all tests pass.

Manual smoke test for both versions:
- [ ] Login with correct credentials → redirected to customers
- [ ] Login with wrong username → "User does not exist"
- [ ] Login with wrong password → "Incorrect password"
- [ ] Login 3 times with wrong password → account locked
- [ ] Admin can register a new worker
- [ ] Regular worker cannot access /accounts/register/
- [ ] Change password works, history is enforced
- [ ] Forgot password sends email, token resets password
- [ ] Add customer shows name in list (secure: as text; vulnerable: XSS fires)
- [ ] SQLi bypasses login (vulnerable only)
