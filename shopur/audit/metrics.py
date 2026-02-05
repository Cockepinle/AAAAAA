from prometheus_client import Gauge, Counter, Summary
from django.contrib.auth import get_user_model
from django.db.models import Sum, F
from cart.models import Cart
from orders.models import Order

User = get_user_model()

debug_metrics_called_total = Counter(
    'shopur_debug_metrics_called_total',
    'Сколько раз была выполнена функция update_business_metrics()'
)

orders_completed_total = Gauge(
    'shopur_orders_completed_total',
    'Текущее количество выполненных заказов'
)

orders_revenue_total = Gauge(
    'shopur_orders_revenue_total',
    'Общая сумма выручки по всем заказам'
)

cart_price_avg = Gauge(
    'shopur_cart_price_avg',
    'Средняя стоимость корзины среди всех корзин'
)

cart_price_summary = Summary(
    'shopur_cart_price_summary',
    'Распределение стоимости корзин в рублях'
)


def update_business_metrics():
    completed = Order.objects.filter(status__status='Выдан клиенту').count()
    orders_completed_total.set(completed)

    revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    orders_revenue_total.set(float(revenue))


    carts = Cart.objects.annotate(
        total_price=Sum(
            F('cartitem__shop_product__price') * F('cartitem__quantity')
        )
    )

    non_empty = [float(c.total_price or 0) for c in carts if c.total_price]
    if non_empty:
        cart_price_avg.set(sum(non_empty) / len(non_empty))
    else:
        cart_price_avg.set(0)

    for cart in carts:
        total = float(cart.total_price or 0)
        cart_price_summary.observe(total)

















































