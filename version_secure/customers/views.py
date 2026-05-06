from django.shortcuts import redirect, render
from django.db import connection

from accounts.decorators import login_required
from customers.models import Customer


@login_required
def customer_list_view(request):
    customers = Customer.objects.all().order_by('-created_at')
    return render(request, 'customers/customer_list.html', {'customers': customers})


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
