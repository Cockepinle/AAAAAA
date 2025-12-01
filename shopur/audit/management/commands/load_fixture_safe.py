from django.core.management.base import BaseCommand
from django.db import connection
import os


class Command(BaseCommand):
    help = 'Load fixture data with disabled triggers'

    def add_arguments(self, parser):
        parser.add_argument('fixture', nargs='*', help='Fixture to load')

    def handle(self, *args, **options):
        fixture = options.get('fixture', [])
        if not fixture:
            self.stdout.write(self.style.ERROR('Please provide fixture file'))
            return

        with connection.cursor() as cursor:
            # Disable all triggers
            cursor.execute("ALTER TABLE audit_auditlog DISABLE TRIGGER ALL")
            cursor.execute("ALTER TABLE catalog_product DISABLE TRIGGER ALL")
            cursor.execute("ALTER TABLE catalog_shopproduct DISABLE TRIGGER ALL")
            cursor.execute("ALTER TABLE orders_order DISABLE TRIGGER ALL")
            cursor.execute("ALTER TABLE orders_orderitem DISABLE TRIGGER ALL")

        # Load fixture using Django's management command
        from django.core.management import call_command
        for f in fixture:
            call_command('loaddata', f)

        with connection.cursor() as cursor:
            # Re-enable all triggers
            cursor.execute("ALTER TABLE audit_auditlog ENABLE TRIGGER ALL")
            cursor.execute("ALTER TABLE catalog_product ENABLE TRIGGER ALL")
            cursor.execute("ALTER TABLE catalog_shopproduct ENABLE TRIGGER ALL")
            cursor.execute("ALTER TABLE orders_order ENABLE TRIGGER ALL")
            cursor.execute("ALTER TABLE orders_orderitem ENABLE TRIGGER ALL")

        self.stdout.write(self.style.SUCCESS('Fixture loaded successfully'))
