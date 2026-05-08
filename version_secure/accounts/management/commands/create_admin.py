import secrets

from django.core.management.base import BaseCommand

from accounts.models import Worker
from accounts.utils import hash_password, validate_password


class Command(BaseCommand):
    help = 'Create the initial admin worker account'

    def handle(self, *args, **options):
        # Create default admin for testing
        username = 'admin'
        email = 'admin@test.com'
        password = 'AdminPass@123'

        if Worker.objects.filter(username=username).exists():
            self.stdout.write('Admin user already exists.')
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