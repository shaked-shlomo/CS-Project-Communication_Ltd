from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list_view, name='customer_list'),
    path('add/', views.add_customer_view, name='add_customer'),
]
