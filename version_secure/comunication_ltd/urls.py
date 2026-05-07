from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('/customers/')),
    path('', include('accounts.urls')),
    path('accounts/', include('accounts.urls')),
    path('customers/', include('customers.urls')),
]
