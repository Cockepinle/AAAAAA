from django.db import migrations


def add_statuses(apps, schema_editor):
    Status = apps.get_model('orders', 'Status')
    defaults = [
        'Ожидание',
        'В обработке',
        'Сборка заказа',
        'Готов к получению',
        'Выдан клиенту',
        'Отменён клиентом',
        'Отменён магазином',
    ]
    for label in defaults:
        Status.objects.get_or_create(status=label)


def remove_statuses(apps, schema_editor):
    Status = apps.get_model('orders', 'Status')
    defaults = [
        'В обработке',
        'Сборка заказа',
        'Готов к получению',
        'Выдан клиенту',
        'Отменён клиентом',
        'Отменён магазином',
    ]
    Status.objects.filter(status__in=defaults).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(add_statuses, remove_statuses),
    ]
