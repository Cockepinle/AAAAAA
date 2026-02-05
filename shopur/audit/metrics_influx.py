import time
import requests
from django.db.models import Sum, F
from cart.models import Cart
from orders.models import Order

INFLUX_URL = "http://localhost:8086"   
INFLUX_ORG = "Cockepinle"
INFLUX_BUCKET = "dashboard"
INFLUX_TOKEN = "sGOa7MdDm9KaoYNZ0Z-sxmSG3FpAVZr0dwTUS2741cajp7S_cNWY_6GI8ySUG06RhMLUy-mFOMQAg420H5VEzg=="


def build_influx_lines():
    ts = int(time.time() * 1e9) 
    lines = []

    completed = Order.objects.filter(status__status='Выдан клиенту').count()
    lines.append(f"shopur_orders_completed_total value={completed}i {ts}")

    revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    lines.append(f"shopur_orders_revenue_total value={float(revenue)} {ts}")

    carts = Cart.objects.annotate(
        total_price=Sum(
            F('cartitem__shop_product__price') * F('cartitem__quantity')
        )
    )
    non_empty = [float(c.total_price or 0) for c in carts if c.total_price]
    avg_price = sum(non_empty) / len(non_empty) if non_empty else 0

    lines.append(f"shopur_cart_price_avg value={avg_price} {ts}")

    for cart in carts:
        cost = float(cart.total_price or 0)
        lines.append(f"shopur_cart_price value={cost} {ts}")

    return "\n".join(lines)


def push_to_influx():
    payload = build_influx_lines()
    url = f"{INFLUX_URL}/api/v2/write"

    params = {
        "org": INFLUX_ORG,
        "bucket": INFLUX_BUCKET,
        "precision": "ns"
    }

    headers = {
        "Authorization": f"Token {INFLUX_TOKEN}",
        "Content-Type": "text/plain; charset=utf-8",
    }

    response = requests.post(
        url,
        params=params,
        data=payload.encode("utf-8"),
        headers=headers,
        timeout=5,
    )

    if response.status_code == 204:
        print("Метрики отправлены в InfluxDB")
    else:
        print("Ошибка:", response.status_code, response.text)
