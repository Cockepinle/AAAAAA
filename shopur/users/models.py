from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    username = models.CharField(max_length=150, unique=False, blank=False)
    email = models.EmailField(unique=True, blank=False, null=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    ROLE_CHOICES = [
        ('ROLE_ADMIN', 'Администратор'),
        ('ROLE_MANAGER', 'Менеджер'),
        ('ROLE_USER', 'Пользователь'),
        ('ROLE_GUEST', 'Гость'),
    ]
    patronymic = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ROLE_USER')

    def __str__(self):
        return f"{self.username} ({self.role})"


class UserSettings(models.Model):
    THEME_CHOICES = [
        ('light', 'Светлая тема'),
        ('dark', 'Тёмная тема'),
    ]
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='ru')
    page_size = models.IntegerField(default=10)
    saved_filters = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Параметры пользователя {self.user.username}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    shop_product = models.ForeignKey('catalog.ShopProduct', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'shop_product')

    def __str__(self):
        return f"{self.user.username} — {self.shop_product.product.name_product}"
