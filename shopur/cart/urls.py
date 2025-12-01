from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .views import update_cart_item

router = DefaultRouter()
router.register(r'carts', CartViewSet)
router.register(r'cart-items', CartItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('cart/', cart_view, name='cart'),
    path('cart/update/<int:item_id>/', update_cart_item, name='update_cart_item'),

]
