"""
Нагрузочные сценарии для Locust.

Как запускать (пример):
    locust -f load/locustfile.py \
        --host http://localhost:8000 \
        --users 50 --spawn-rate 5

Требуемые переменные окружения:
    AUTH_TOKEN          — Bearer/JWT токен для API (обязателен для POST).
    TEST_USER_ID        — ID пользователя, от имени которого создаются корзины/заказы.
    TEST_PRODUCT_ID     — ID shop_product для добавления в корзину.
    TEST_STATUS_ID      — ID статуса заказа (например, "New").

Что покрывает:
    - Чтение каталога (GET /api/shop-products/).
    - Массовые POST создания заказа: /api/carts/, /api/cart-items/, /api/orders/.
    - Параллельное обновление остатков (PATCH /api/shop-products/<id>/) как имитация конкурентных транзакций.
Метрики p95/p99 видны в UI Locust; результаты — скриншоты для отчёта.
"""

import os
import random
from decimal import Decimal

from locust import HttpUser, task, between


def auth_headers():
    token = os.getenv("AUTH_TOKEN", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


class CatalogUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(3)
    def list_shop_products(self):
        self.client.get("/api/shop-products/", headers=auth_headers(), name="GET /api/shop-products/")


class OrderUser(HttpUser):
    wait_time = between(0.5, 1.5)

    @task(1)
    def create_order_flow(self):
        headers = auth_headers()
        user_id = os.getenv("TEST_USER_ID")
        product_id = os.getenv("TEST_PRODUCT_ID")
        status_id = os.getenv("TEST_STATUS_ID")
        if not all([user_id, product_id, status_id]):
            return  

        resp_cart = self.client.post(
            "/api/carts/", json={"user": int(user_id)}, headers=headers, name="POST /api/carts/"
        )
        if resp_cart.status_code not in (200, 201):
            return
        cart_id = resp_cart.json().get("id")
        if not cart_id:
            return

        quantity = random.randint(1, 3)
        resp_item = self.client.post(
            "/api/cart-items/",
            json={"cart": cart_id, "shop_product": int(product_id), "quantity": quantity},
            headers=headers,
            name="POST /api/cart-items/",
        )
        if resp_item.status_code not in (200, 201):
            return

        price = Decimal(os.getenv("TEST_PRICE", "1000"))
        total_amount = float(price * quantity)
        self.client.post(
            "/api/orders/",
            json={
                "user": int(user_id),
                "address_delivery": "LoadTest address",
                "comment": "Load test order",
                "status": int(status_id),
                "total_amount": total_amount,
            },
            headers=headers,
            name="POST /api/orders/",
        )


class StockUpdateUser(HttpUser):
    wait_time = between(0.2, 0.8)

    @task
    def patch_stock(self):
        headers = auth_headers()
        product_id = os.getenv("TEST_PRODUCT_ID")
        if not product_id:
            return
        new_quantity = random.randint(1, 20)
        self.client.patch(
            f"/api/shop-products/{product_id}/",
            json={"quantity": new_quantity},
            headers=headers,
            name="PATCH /api/shop-products/{id}/",
        )
