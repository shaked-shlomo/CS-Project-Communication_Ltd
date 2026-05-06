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
