from decimal import Decimal, InvalidOperation
from rest_framework import viewsets, permissions
from django.shortcuts import render, get_object_or_404
from .models import (
    Address, Shop, Category, Material, Size, Stones,
    Product, ShopProduct, ProductImage
)
from .serializers import *


# ===== API =====
class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer


class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    """Запрет на изменение без прав админа, чтение открыто."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer


class SizeViewSet(viewsets.ModelViewSet):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer


class StonesViewSet(viewsets.ModelViewSet):
    queryset = Stones.objects.all()
    serializer_class = StonesSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ShopProductViewSet(viewsets.ModelViewSet):
    queryset = ShopProduct.objects.all()
    serializer_class = ShopProductSerializer


def _get_favorite_ids(user):
    if not user.is_authenticated:
        return set()
    try:
        from users.models import Favorite
        return set(
            Favorite.objects.filter(user=user).values_list('shop_product_id', flat=True)
        )
    except Exception:
        return set()


def home_view(request):
    products = (
        ShopProduct.objects.select_related('product', 'material', 'size', 'stones')
        .prefetch_related('images')
        .order_by('-id')[:8]
    )
    context = {
        'products': products,
        'favorite_ids': _get_favorite_ids(request.user),
        'categories': Category.objects.order_by('name_category')[:6],
    }
    return render(request, 'catalog/home.html', context)


def catalog_view(request):
    products = ShopProduct.objects.select_related(
        'product', 'material', 'size', 'stones', 'shop'
    ).prefetch_related('images')

    search_query = (request.GET.get('q') or '').strip()
    category_param = (request.GET.get('category') or '').strip()
    material_id = (request.GET.get('material') or '').strip()
    size_id = (request.GET.get('size') or '').strip()
    stones_id = (request.GET.get('stones') or '').strip()
    price_min = (request.GET.get('price_min') or '').strip()
    price_max = (request.GET.get('price_max') or '').strip()
    sort = (request.GET.get('sort') or '').strip()

    if category_param and category_param != 'all':
        products = products.filter(product__category_id=category_param)

    if search_query:
        products = products.filter(product__name_product__icontains=search_query)
    if material_id:
        products = products.filter(material_id=material_id)
    if size_id:
        products = products.filter(size_id=size_id)
    if stones_id:
        products = products.filter(stones_id=stones_id)
    if price_min:
        try:
            products = products.filter(price__gte=Decimal(price_min))
        except InvalidOperation:
            price_min = ''
    if price_max:
        try:
            products = products.filter(price__lte=Decimal(price_max))
        except InvalidOperation:
            price_max = ''

    if sort == 'asc':
        products = products.order_by('price')
    elif sort == 'desc':
        products = products.order_by('-price')

    filters_active = any([material_id, size_id, stones_id, price_min, price_max, sort])

    context = {
        'products': products,
        'categories': Category.objects.order_by('name_category'),
        'materials': Material.objects.order_by('material_name'),
        'sizes': Size.objects.order_by('size_name'),
        'stones': Stones.objects.order_by('stones_name'),
        'favorite_ids': _get_favorite_ids(request.user),
        'search_query': search_query,
        'selected_category': category_param,
        'selected_material': material_id,
        'selected_size': size_id,
        'selected_stones': stones_id,
        'price_min': price_min,
        'price_max': price_max,
        'sort': sort,
        'filters_active': filters_active,
    }
    return render(request, 'catalog/catalog.html', context)


def product_detail_view(request, id):
    product = get_object_or_404(
        ShopProduct.objects.prefetch_related('images', 'product', 'material', 'size', 'stones'),
        id=id
    )

    variants = ShopProduct.objects.filter(product=product.product)
    materials = variants.values_list('material__id', 'material__material_name').distinct()
    sizes = variants.values_list('size__id', 'size__size_name').distinct()

    context = {
        'product': product,
        'materials': materials,
        'sizes': sizes,
        'base_product_id': product.product.id,
    }

    return render(request, 'catalog/product_detail.html', context)
