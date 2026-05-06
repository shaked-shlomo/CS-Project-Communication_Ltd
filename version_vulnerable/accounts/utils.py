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
