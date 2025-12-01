# -*- coding: utf-8 -*-
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','shopur.settings')
import django
django.setup()
from catalog.models import ShopProduct
sp = ShopProduct.objects.get(id=1)
sp.quantity = 20
sp.save()
print('quantity set', sp.quantity)
