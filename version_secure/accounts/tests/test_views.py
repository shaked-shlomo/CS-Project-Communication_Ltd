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