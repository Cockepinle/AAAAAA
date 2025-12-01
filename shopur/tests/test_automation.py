from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from catalog.models import (
    Address,
    Shop,
    Category,
    Material,
    Size,
    Stones,
    Product,
    ShopProduct,
)
from cart.models import Cart, CartItem


class AutomationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="pass1234",
        )
        cls.user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="pass1234",
        )
        cls.client_admin = APIClient()
        cls.client_admin.force_authenticate(user=cls.admin)
        cls.client_user = APIClient()
        cls.client_user.force_authenticate(user=cls.user)

        cls.address = Address.objects.create(city="TestCity", street="Main st, 1")
        cls.shop = Shop.objects.create(
            name_shop="Main shop",
            address=cls.address,
            office_hours="10-20",
        )
        cls.category = Category.objects.create(
            name_category="Rings",
            description_category="Desc",
        )
        cls.material = Material.objects.create(material_name="Gold")
        cls.size = Size.objects.create(size_name="18", description="Ring size")
        cls.stones = Stones.objects.create(stones_name="Diamond")
        cls.product = Product.objects.create(
            name_product="Ring A",
            description_product="Nice ring",
            category=cls.category,
        )
        cls.shop_product = ShopProduct.objects.create(
            shop=cls.shop,
            product=cls.product,
            material=cls.material,
            size=cls.size,
            stones=cls.stones,
            quantity=10,
            price="1999.99",
        )

    def test_sku_uniqueness(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ShopProduct.objects.create(
                    shop=self.shop,
                    product=self.product,
                    material=self.material,
                    size=self.size,
                    stones=self.stones,
                    quantity=1,
                    price="100.00",
                )

    def test_cart_total_calculation(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, shop_product=self.shop_product, quantity=2)
        product_b = Product.objects.create(
            name_product="Ring B",
            description_product="Another ring",
            category=self.category,
        )
        sp_b = ShopProduct.objects.create(
            shop=self.shop,
            product=product_b,
            material=self.material,
            size=self.size,
            stones=self.stones,
            quantity=5,
            price="500.00",
        )
        CartItem.objects.create(cart=cart, shop_product=sp_b, quantity=3)

        expected_total = Decimal("1999.99") * 2 + Decimal("500.00") * 3
        expected_qty = 2 + 3
        total = sum(
            Decimal(item.shop_product.price) * item.quantity
            for item in CartItem.objects.filter(cart=cart).select_related("shop_product")
        )
        qty = sum(item.quantity for item in CartItem.objects.filter(cart=cart))
        self.assertEqual(total, expected_total)
        self.assertEqual(qty, expected_qty)

    def test_order_requires_user_field(self):
        resp = self.client_user.post(
            "/api/orders/",
            {
                "address_delivery": "Test address",
                "status": 1,
                "total_amount": 10,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_admin_can_create_category_user_forbidden(self):
        resp_admin = self.client_admin.post(
            "/api/categories/",
            {"name_category": "NewCat", "description_category": "Test"},
            format="json",
        )
        self.assertEqual(resp_admin.status_code, 201)

        resp_user = self.client_user.post(
            "/api/categories/",
            {"name_category": "FailCat", "description_category": "Test"},
            format="json",
        )
        self.assertEqual(resp_user.status_code, 403)

    def test_migrate_check(self):
        call_command("migrate", "--check", verbosity=0)
        call_command("migrate", "--check", verbosity=0)
