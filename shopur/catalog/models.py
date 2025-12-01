from django.db import models


class Address(models.Model):
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.city}, {self.street}"


class Shop(models.Model):
    name_shop = models.CharField(max_length=100)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    office_hours = models.CharField(max_length=100)

    def __str__(self):
        return self.name_shop


class Category(models.Model):
    name_category = models.CharField(max_length=100)
    description_category = models.CharField(max_length=255)

    def __str__(self):
        return self.name_category


class Material(models.Model):
    material_name = models.CharField(max_length=50)

    def __str__(self):
        return self.material_name


class Size(models.Model):
    size_name = models.CharField(max_length=50)
    description = models.CharField(max_length=60)

    def __str__(self):
        return self.size_name


class Stones(models.Model):
    stones_name = models.CharField(max_length=50)

    def __str__(self):
        return self.stones_name


class Product(models.Model):
    name_product = models.CharField(max_length=100)
    description_product = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name_product

class ShopProduct(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stones = models.ForeignKey(Stones, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name_product} ({self.shop.name_shop})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'shop', 'product', 'material', 'size', 'stones'
                ],
                name='uniq_shopproduct_variant'
            )
        ]


class ProductImage(models.Model):
    product = models.ForeignKey(ShopProduct, on_delete=models.CASCADE, related_name='images')
    image_url = models.CharField(max_length=255)

    def __str__(self):
        return f"Фото для {self.product.product.name_product}"
