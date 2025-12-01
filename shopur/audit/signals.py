from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import AuditLog
from catalog.models import Product, ShopProduct
from orders.models import Order

TRACKED_MODELS = (Product, ShopProduct, Order)


def write(table, op, old=None, new=None, user=None):
    AuditLog.objects.create(
        user=user,
        table_name=table,
        operation=op,
        old_value=str(old) if old else None,
        new_value=str(new) if new else None,
    )


def attach_old_state(sender, instance):
    if not instance.pk:
        instance.__old_state = None
        return
    try:
        instance.__old_state = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance.__old_state = None


@receiver(pre_save, sender=Product)
@receiver(pre_save, sender=ShopProduct)
@receiver(pre_save, sender=Order)
def before_save(sender, instance, **kwargs):
    attach_old_state(sender, instance)


@receiver(post_save, sender=Product)
@receiver(post_save, sender=ShopProduct)
@receiver(post_save, sender=Order)
def on_save(sender, instance, created, **kwargs):
    old_state = getattr(instance, '__old_state', None)
    write(
        sender.__name__,
        'CREATE' if created else 'UPDATE',
        old=None if created else old_state,
        new=instance,
        user=getattr(instance, '_actor', None),
    )


@receiver(post_delete, sender=Product)
@receiver(post_delete, sender=ShopProduct)
@receiver(post_delete, sender=Order)
def on_del(sender, instance, **kwargs):
    write(sender.__name__, 'DELETE', old=instance, user=getattr(instance, '_actor', None))
