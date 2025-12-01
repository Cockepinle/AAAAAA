from django.contrib import admin
from .models import (
    Address, Shop, Category, Material, Size, Stones,
    Product, ShopProduct, ProductImage
)


class ProductImageInline(admin.TabularInline):  # или StackedInline для карточек
    model = ProductImage
    extra = 1  # количество пустых полей по умолчанию


@admin.register(ShopProduct)
class ShopProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'price', 'quantity')
    inlines = [ProductImageInline]


admin.site.register(Address)
admin.site.register(Shop)
admin.site.register(Category)
admin.site.register(Material)
admin.site.register(Size)
admin.site.register(Stones)
admin.site.register(Product)
