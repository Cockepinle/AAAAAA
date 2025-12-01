from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from users.views import UserViewSet, UserSettingsViewSet
from catalog.views import (
    AddressViewSet, ShopViewSet, CategoryViewSet, MaterialViewSet,
    SizeViewSet, StonesViewSet, ProductViewSet, ShopProductViewSet
)
from orders.views import StatusViewSet, OrderViewSet, OrderItemViewSet, PaymentViewSet
from cart.views import CartViewSet, CartItemViewSet
from audit.views import ReportLogViewSet, AuditLogViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'user-settings', UserSettingsViewSet)
router.register(r'addresses', AddressViewSet)
router.register(r'shops', ShopViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'materials', MaterialViewSet)
router.register(r'sizes', SizeViewSet)
router.register(r'stones', StonesViewSet)
router.register(r'products', ProductViewSet)
router.register(r'shop-products', ShopProductViewSet)
router.register(r'statuses', StatusViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'carts', CartViewSet)
router.register(r'cart-items', CartItemViewSet)
router.register(r'report-logs', ReportLogViewSet)
router.register(r'audit-logs', AuditLogViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
    path('api/auth/', include('rest_framework.urls')),
    path('api/jwt/', include('users.jwt_urls')),
    path('', include('users.urls')),     
    path('', include('catalog.urls')),  
    path('', include('cart.urls')),
    path('orders/', include('orders.web_urls')),
    path('prometheus/', include('django_prometheus.urls'))
]
