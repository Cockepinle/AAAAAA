from datetime import datetime, timedelta

from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone

from .models import Status, Order, OrderItem, Payment
from .utils import compute_order_analytics, export_analytics_csv


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('status',)


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'date_create', 'total_amount')
    list_filter = ('status', 'date_create')
    search_fields = ('id', 'user__email', 'user__username')
    date_hierarchy = 'date_create'
    change_list_template = 'admin/orders/order/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'analytics/',
                self.admin_site.admin_view(self.analytics_view),
                name='orders_order_analytics',
            ),
        ]
        return custom + urls

    def analytics_view(self, request):
        today = timezone.localdate()
        default_start = today - timedelta(days=30)

        def parse_date(value, fallback):
            if not value:
                return fallback
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                return fallback

        start_date = parse_date(request.GET.get('start_date'), default_start)
        end_date = parse_date(request.GET.get('end_date'), today)
        status_id = request.GET.get('status') or ''

        analytics = compute_order_analytics(start_date, end_date, status_id or None)

        if request.GET.get('export') == 'csv':
            return export_analytics_csv(start_date, end_date, analytics, user=request.user)

        context = dict(
            self.admin_site.each_context(request),
            title='Аналитика заказов',
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            statuses=Status.objects.all(),
            selected_status=status_id,
            summary=analytics['summary'],
            status_breakdown=analytics['status_breakdown'],
            top_products=analytics['top_products'],
            top_customers=analytics['top_customers'],
            chart_payload=analytics['chart_payload'],
        )
        return TemplateResponse(request, 'admin/orders/order/analytics.html', context)


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Payment)
