from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_encrypt_sensitive_fields'),
        ('orders', '0009_fix_auditlog_timestamp'),
    ]

    operations = []
