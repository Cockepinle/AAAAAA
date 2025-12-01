from django.urls import path
from .views import orders_list_view, order_detail_view, place_order_view, download_receipt_view, manager_analytics_view

urlpatterns = [
    path('', orders_list_view, name='orders_list'),
    path('analytics/', manager_analytics_view, name='manager_analytics'),
    path('place/', place_order_view, name='place_order'),
    path('<int:order_id>/', order_detail_view, name='order_detail'),
    path('<int:order_id>/download/', download_receipt_view, name='download_receipt'),
]
