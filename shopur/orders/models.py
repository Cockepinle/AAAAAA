from django.db import models
from users.models import User
from catalog.models import ShopProduct
from shopur.fields import EncryptedTextField


class Status(models.Model):
    status = models.CharField(max_length=50)

    def __str__(self):
        return self.status


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address_delivery = EncryptedTextField()
    comment = EncryptedTextField(blank=True, null=True)
    date_create = models.DateTimeField(auto_now_add=True)
    date_finish = models.DateTimeField(blank=True, null=True)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Заказ №{self.id} от {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    shop_product = models.ForeignKey(ShopProduct, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    discount = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.shop_product.product.name_product} x {self.quantity}"


class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField()
    payment_method = models.CharField(max_length=20)
    transaction_id = EncryptedTextField(blank=True, null=True)
    status = models.CharField(max_length=20)

    def __str__(self):
        return f"Оплата заказа {self.order.id}"
