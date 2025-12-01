from rest_framework import viewsets
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
import json

from cart.models import Cart, CartItem
from cart.serializers import CartSerializer, CartItemSerializer
from catalog.models import ShopProduct, Shop


@login_required
@require_POST
def add_to_cart(request, id):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        payload = {}

    base_variant = get_object_or_404(ShopProduct, id=id)

    material_id = payload.get('material_id')
    size_id = payload.get('size_id')
    quantity = int(payload.get('quantity') or 1)

    if material_id and size_id:
        try:
            variant = ShopProduct.objects.get(product=base_variant.product, material_id=material_id, size_id=size_id)
        except ShopProduct.DoesNotExist:
            return JsonResponse({'error': 'Вариант не найден'}, status=404)
    else:
        variant = base_variant

    if quantity < 1:
        return JsonResponse({'error': 'Количество должно быть положительным'}, status=400)

    if quantity > variant.quantity:
        return JsonResponse({'error': 'Запрошено больше, чем есть на складе'}, status=400)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        shop_product=variant,
        defaults={'quantity': quantity}
    )

    if not created:
        if item.quantity + quantity > variant.quantity:
            return JsonResponse({'error': 'Запрошено больше, чем доступно на складе'}, status=400)
        item.quantity += quantity
        item.save()

    return JsonResponse({'message': 'Товар добавлен в корзину'})


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart).select_related('shop_product', 'shop_product__product', 'shop_product__material', 'shop_product__size')
    total = sum((item.shop_product.price * item.quantity) for item in items) if items else 0
    shops = Shop.objects.select_related('address').all()

    return render(request, 'cart/cart.html', {
        'cart': cart,
        'items': items,
        'total': total,
        'shops': shops,
    })


@login_required
@require_POST
def update_cart_item(request, item_id):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        payload = {}

    new_qty = int(payload.get('quantity', -1))
    if new_qty < 0:
        return JsonResponse({'error': 'Количество должно быть неотрицательным'}, status=400)

    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    variant = item.shop_product

    if new_qty > variant.quantity:
        return JsonResponse({'error': 'Недостаточно остатка на складе'}, status=400)

    cart = item.cart
    if new_qty == 0:
        item.delete()
    else:
        item.quantity = new_qty
        item.save()

    total = sum(ci.shop_product.price * ci.quantity for ci in CartItem.objects.filter(cart=cart))
    return JsonResponse({'message': 'Обновлено', 'total': total})


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer


class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
