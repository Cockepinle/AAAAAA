from django.db import migrations
import shopur.fields


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_specialized_audit_functions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='address_delivery',
            field=shopur.fields.EncryptedTextField(),
        ),
        migrations.AlterField(
            model_name='order',
            name='comment',
            field=shopur.fields.EncryptedTextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='transaction_id',
            field=shopur.fields.EncryptedTextField(blank=True, null=True),
        ),
    ]
