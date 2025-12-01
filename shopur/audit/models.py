from django.db import models
from users.models import User
from django.utils import timezone


class ReportLog(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    report_type = models.CharField(max_length=50)
    report_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    file_link = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.report_name} ({self.user.username})"


class AuditLog(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    table_name = models.CharField(max_length=50)
    operation = models.CharField(max_length=20)
    timestamp = models.DateTimeField(default=timezone.now, editable=False)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Аудит {self.table_name} ({self.operation})"


class BackupGuide(models.Model):
    """Виртуальная модель для отображения регламента бэкапа в админке."""

    class Meta:
        managed = False
        verbose_name = 'Регламент резервного копирования'
        verbose_name_plural = 'Регламент резервного копирования'

