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


def register_view(request):
    return HttpResponse('TODO')


def change_password_view(request):
    return HttpResponse('TODO')


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
