from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient

from catalog.models import Category
from orders.models import Order, Payment, Status


class SecurityTests(TestCase):

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
        cls.status = Status.objects.create(status="New")

    def test_sql_injection_payload_does_not_break_categories(self):
        payload = "' OR '1'='1"
        resp = self.client_user.get(f"/api/categories/?search={payload}")
        self.assertLess(resp.status_code, 500)

    def test_non_admin_cannot_create_category(self):
        resp = self.client_user.post(
            "/api/categories/",
            {"name_category": "InjCat", "description_category": "Test"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_encrypted_fields_at_rest(self):
        order = Order.objects.create(
            user=self.user,
            address_delivery="Secret address",
            comment="Secret comment",
            status=self.status,
            total_amount="10.00",
        )
        payment = Payment.objects.create(
            order=order,
            amount="10.00",
            payment_date="2025-01-01T00:00:00Z",
            payment_method="card",
            transaction_id="TXN-12345",
            status="paid",
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT address_delivery FROM orders_order WHERE id=%s", [order.id])
            raw_address = cursor.fetchone()[0]
            cursor.execute("SELECT transaction_id FROM orders_payment WHERE id=%s", [payment.id])
            raw_txn = cursor.fetchone()[0]

        self.assertNotEqual(raw_address, "Secret address")
        self.assertNotEqual(raw_txn, "TXN-12345")
