from datetime import datetime, time
import csv

from django.db.models import Count, Sum, F, DecimalField
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone

from audit.models import ReportLog

from .models import Order, OrderItem


def _make_datetime_range(start_date, end_date):
    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start_date, time.min), tz)
    end_dt = timezone.make_aware(datetime.combine(end_date, time.max), tz)
    return start_dt, end_dt


def compute_order_analytics(start_date, end_date, status_id=None):
    start_dt, end_dt = _make_datetime_range(start_date, end_date)

    orders_qs = Order.objects.select_related('status', 'user').filter(
        date_create__range=(start_dt, end_dt)
    )
    if status_id:
        orders_qs = orders_qs.filter(status_id=status_id)

    revenue_total = orders_qs.aggregate(total=Sum('total_amount'))['total'] or 0
    order_count = orders_qs.count()
    avg_order = revenue_total / order_count if order_count else 0
    delivered = orders_qs.filter(status__status__iexact='Доставлен').count()

    revenue_by_day = list(
        orders_qs.annotate(day=TruncDate('date_create'))
        .values('day')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('day')
    )
    revenue_labels = [item['day'].strftime('%d.%m') for item in revenue_by_day]
    revenue_values = [float(item['total']) for item in revenue_by_day]
    revenue_counts = [item['count'] for item in revenue_by_day]

    status_breakdown = list(
        orders_qs.values('status__status').annotate(count=Count('id')).order_by('-count')
    )
    status_labels = [item['status__status'] for item in status_breakdown]
    status_values = [item['count'] for item in status_breakdown]

    revenue_expr = Sum(
        F('quantity') * F('shop_product__price'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    order_items_qs = OrderItem.objects.filter(order__date_create__range=(start_dt, end_dt))
    if status_id:
        order_items_qs = order_items_qs.filter(order__status_id=status_id)

    top_products = list(
        order_items_qs.values('shop_product__product__name_product')
        .annotate(total=revenue_expr)
        .order_by('-total')[:5]
    )
    product_labels = [item['shop_product__product__name_product'] for item in top_products]
    product_values = [float(item['total']) if item['total'] else 0 for item in top_products]

    top_customers = list(
        orders_qs.values('user__email', 'user__username')
        .annotate(order_count=Count('id'), total=Sum('total_amount'))
        .order_by('-total')[:5]
    )

    return {
        'orders_qs': orders_qs,
        'revenue_by_day': revenue_by_day,
        'status_breakdown': status_breakdown,
        'top_products': top_products,
        'top_customers': top_customers,
        'summary': {
            'revenue_total': revenue_total,
            'order_count': order_count,
            'avg_order': avg_order,
            'delivered': delivered,
        },
        'chart_payload': {
            'revenue': {'labels': revenue_labels, 'revenue': revenue_values, 'count': revenue_counts},
            'status': {'labels': status_labels, 'values': status_values},
            'products': {'labels': product_labels, 'values': product_values},
        },
    }


def export_analytics_csv(start_date, end_date, analytics, user=None):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f'orders_analytics_{start_date}_{end_date}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')

    writer.writerow(['Период', start_date, end_date])
    writer.writerow(['Всего заказов', analytics['summary']['order_count']])
    writer.writerow(['Доставлено', analytics['summary']['delivered']])
    writer.writerow(['Выручка', analytics['summary']['revenue_total']])
    writer.writerow([])

    writer.writerow(['Выручка по дням'])
    writer.writerow(['Дата', 'Выручка', 'Количество заказов'])
    for row in analytics['revenue_by_day']:
        writer.writerow([row['day'], row['total'], row['count']])
    writer.writerow([])

    writer.writerow(['Заказы по статусам'])
    writer.writerow(['Статус', 'Количество'])
    for row in analytics['status_breakdown']:
        writer.writerow([row['status__status'], row['count']])
    writer.writerow([])

    writer.writerow(['Топ продукты (по выручке)'])
    writer.writerow(['Название', 'Выручка'])
    for row in analytics['top_products']:
        writer.writerow([row['shop_product__product__name_product'], row['total']])
    writer.writerow([])

    writer.writerow(['Топ клиенты'])
    writer.writerow(['Email', 'Имя пользователя', 'Заказов', 'Сумма'])
    for row in analytics['top_customers']:
        writer.writerow([row['user__email'], row['user__username'], row['order_count'], row['total']])

    if user:
        ReportLog.objects.create(
            user=user,
            report_type='orders_analytics',
            report_name=f'Orders analytics {start_date} - {end_date}',
            file_link=filename,
        )

    return response
