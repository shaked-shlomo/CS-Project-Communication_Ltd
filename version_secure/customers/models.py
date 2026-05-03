from django.db import models
from accounts.models import Worker


class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    package = models.CharField(max_length=100)
    created_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
