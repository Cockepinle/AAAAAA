from django.urls import path, include
from rest_framework.routers import DefaultRouter
from cart.views import add_to_cart
from catalog import views
from .views import (
    AddressViewSet, ShopViewSet, CategoryViewSet, MaterialViewSet,
    SizeViewSet, StonesViewSet, ProductViewSet, ShopProductViewSet
)

router = DefaultRouter()
router.register(r'addresses', AddressViewSet)
router.register(r'shops', ShopViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'materials', MaterialViewSet)
router.register(r'sizes', SizeViewSet)
router.register(r'stones', StonesViewSet)
router.register(r'products', ProductViewSet)
router.register(r'shop-products', ShopProductViewSet)

urlpatterns = [
    path('', views.home_view, name='home'),
    path('catalog/', views.catalog_view, name='catalog'),
    path('product/<int:id>/', views.product_detail_view, name='product_detail'),
    path('product/<int:id>/add/', add_to_cart, name='add_to_cart'),
]
