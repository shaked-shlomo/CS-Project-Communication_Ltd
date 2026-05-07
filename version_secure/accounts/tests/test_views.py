import pytest
from accounts.models import Worker


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
        admin_client.post('/accounts/register/', {
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
