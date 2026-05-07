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
