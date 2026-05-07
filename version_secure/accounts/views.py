import hashlib
import secrets
from datetime import datetime

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


# Stubs for Scope 3 (login, logout, forgot_password, reset_password) — not yet implemented
def login_view(request):
    from django.http import HttpResponse
    return HttpResponse('TODO')


def logout_view(request):
    from django.http import HttpResponse
    return HttpResponse('TODO')


def forgot_password_view(request):
    from django.http import HttpResponse
    return HttpResponse('TODO')


def reset_password_view(request):
    from django.http import HttpResponse
    return HttpResponse('TODO')


# --- Scope 4: Worker Account Management ---

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
                "VALUES (%s, %s, %s, %s, %s, 0, 0, %s)",
                [username, email, role, hashed, salt, datetime.now()],
            )

        return render(request, 'accounts/register.html', {
            'success': f'Worker account for "{username}" has been created.',
        })

    return render(request, 'accounts/register.html')


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
