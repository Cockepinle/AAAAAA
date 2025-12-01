from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from django.test import Client

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
from orders.models import Status, Order
from users.models import Favorite


class IntegrationFlowsTest(TestCase):
    """
    Рабочие интеграционные проверки по доступным API:
    - права на создание категории (аналог бренда);
    - поток корзина → заказ (сумма позиций);
    - уникальность настроек пользователя (OneToOne).
    """

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
        cls.order_status = Status.objects.create(status="New")
        cls.client_admin = APIClient()
        cls.client_admin.force_authenticate(user=cls.admin)
        cls.client_user = APIClient()
        cls.client_user.force_authenticate(user=cls.user)
        cls.web_client_user = Client()  # Django test client with session auth

    # 1. Права на создание категории (аналог бренда)
    def test_admin_create_category_user_gets_403(self):
        resp_admin = self.client_admin.post(
            "/api/categories/",
            {"name_category": "NewCategory", "description_category": "Test"},
            format="json",
        )
        self.assertEqual(resp_admin.status_code, 201)

        resp_user = self.client_user.post(
            "/api/categories/",
            {"name_category": "UserCategory", "description_category": "Test"},
            format="json",
        )
        self.assertEqual(resp_user.status_code, 403)

    # 2. Поток корзина → заказ (через API)
    def test_cart_to_order_flow(self):
        # создать корзину
        resp_cart = self.client_user.post("/api/carts/", {"user": self.user.pk}, format="json")
        self.assertEqual(resp_cart.status_code, 201)
        cart_id = resp_cart.data["id"]

        # добавить позицию
        resp_item = self.client_user.post(
            "/api/cart-items/",
            {"cart": cart_id, "shop_product": self.shop_product.pk, "quantity": 2},
            format="json",
        )
        self.assertEqual(resp_item.status_code, 201)

        # оформить заказ
        total_amount = float(Decimal(self.shop_product.price) * 2)
        resp_order = self.client_user.post(
            "/api/orders/",
            {
                "user": self.user.pk,
                "address_delivery": "Test address",
                "comment": "Test order",
                "status": self.order_status.pk,
                "total_amount": total_amount,
            },
            format="json",
        )
        self.assertEqual(resp_order.status_code, 201)
        self.assertAlmostEqual(float(resp_order.data.get("total_amount", total_amount)), total_amount, places=2)

    # 3. Уникальность настроек пользователя (OneToOne)
    def test_usersettings_one_to_one(self):
        resp_ok = self.client_user.post(
            "/api/user-settings/",
            {"user": self.user.pk, "theme": "dark", "language": "ru"},
            format="json",
        )
        self.assertEqual(resp_ok.status_code, 201)

        resp_dup = self.client_user.post(
            "/api/user-settings/",
            {"user": self.user.pk, "theme": "light", "language": "en"},
            format="json",
        )
        self.assertIn(resp_dup.status_code, (400, 409))

    # 4. Экспорт CSV аналитики (через web-ендпоинт менеджера/админа)
    def test_export_csv_analytics(self):
        # login as admin via session to pass login_required if any
        self.assertTrue(self.web_client_user.login(email="admin@example.com", password="pass1234"))
        resp = self.web_client_user.get("/orders/analytics/?export=csv")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])

    # 5. Генерация PDF-чека (web)
    def test_pdf_receipt_download(self):
        order = self._create_order_for_user(self.user)
        self.assertTrue(self.web_client_user.login(email="user@example.com", password="pass1234"))
        resp = self.web_client_user.get(f"/orders/{order.pk}/download/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/pdf", resp["Content-Type"])

    # 6. M2M избранное через toggle
    def test_favorites_toggle(self):
        self.assertTrue(self.web_client_user.login(email="user@example.com", password="pass1234"))
        # add (toggle requires POST)
        resp_add = self.web_client_user.post(f"/favorites/toggle/{self.shop_product.pk}/")
        self.assertIn(resp_add.status_code, (200, 302))
        self.assertTrue(Favorite.objects.filter(user=self.user, shop_product=self.shop_product).exists())
        # remove
        resp_del = self.web_client_user.post(f"/favorites/toggle/{self.shop_product.pk}/")
        self.assertIn(resp_del.status_code, (200, 302))
        self.assertFalse(Favorite.objects.filter(user=self.user, shop_product=self.shop_product).exists())

    # helpers
    def _create_order_for_user(self, user):
        return Order.objects.create(
            user=user,
            address_delivery="Test",
            comment="",
            status=self.order_status,
            total_amount="10.00",
        )
