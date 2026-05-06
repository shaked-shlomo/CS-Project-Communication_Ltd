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
