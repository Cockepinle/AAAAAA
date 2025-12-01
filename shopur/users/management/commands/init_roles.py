from django.core.management import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        admin, _ = Group.get_or_create(name='ROLE_ADMIN')
        manager, _ = Group.get_or_create(name='ROLE_MANAGER')
        user, _ = Group.get_or_create(name='ROLE_USER')
        guest, _ = Group.get_or_create(name='ROLE_GUEST')

        admin.permissions.set(Permission.objects.all())

        def allow(app_label, model, codenames):
            perms = Permission.objects.filter(
                content_type__app_label=app_label,
                content_type__model=model.lower(),
                codename__in=codenames
            )
            return list(perms)

        manager.permissions.set(
            allow('catalog','Product',['add_product','change_product','view_product']) +
            allow('catalog','Category',['add_category','change_category','view_category']) +
            allow('orders','Order',['change_order','view_order']) +
            allow('orders','OrderItem',['view_orderitem'])
        )
        user.permissions.set(
            allow('catalog','Product',['view_product']) +
            allow('catalog','Category',['view_category']) +
            allow('orders','Order',['add_order','view_order']) +
            allow('orders','OrderItem',['add_orderitem','view_orderitem'])
        )
        guest.permissions.set(
            allow('catalog','Product',['view_product']) +
            allow('catalog','Category',['view_category'])
        )
        self.stdout.write('RBAC: роли и права созданы')
