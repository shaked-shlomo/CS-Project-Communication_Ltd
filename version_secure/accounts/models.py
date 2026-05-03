from django.db import models


class Worker(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=[('admin', 'Admin'), ('worker', 'Worker')])
    hashed_password = models.CharField(max_length=255)
    salt = models.CharField(max_length=64)
    login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class PasswordHistory(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    hashed_password = models.CharField(max_length=255)
    salt = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class PasswordResetToken(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
