import csv
from django.core.management import BaseCommand
from catalog.models import Product, Category

class Command(BaseCommand):
    def add_arguments(self, p): p.add_argument('csv_path')
    def handle(self, *a, **o):
        with open(o['csv_path'], encoding='utf-8') as f:
            for r in csv.DictReader(f):
                cat,_ = Category.objects.get_or_create(name_category=r['category'])
                Product.objects.update_or_create(
                    name_product=r['name'],
                    defaults={'description_product': r.get('description',''), 'category': cat}
                )
