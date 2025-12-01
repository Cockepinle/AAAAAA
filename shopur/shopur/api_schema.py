from drf_spectacular.openapi import AutoSchema

MODEL_TAGS = {
    'users.user': 'users_user',
    'users.usersettings': 'users_usersettings',
    'catalog.address': 'catalog_address',
    'catalog.shop': 'catalog_shop',
    'catalog.category': 'catalog_category',
    'catalog.material': 'catalog_material',
    'catalog.size': 'catalog_size',
    'catalog.stones': 'catalog_stones',
    'catalog.product': 'catalog_product',
    'catalog.shopproduct': 'catalog_shopproduct',
    'orders.status': 'orders_status',
    'orders.order': 'orders_order',
    'orders.orderitem': 'orders_orderitem',
    'orders.payment': 'orders_payment',
    'cart.cart': 'cart_cart',
    'cart.cartitem': 'cart_cartitem',
    'audit.auditlog': 'audit_auditlog',
    'audit.reportlog': 'audit_reportlog',
}


class TaggedAutoSchema(AutoSchema):
    """Группирует эндпоинты в Swagger по смысловым разделам."""

    def get_tags(self):
        if getattr(self.view, 'schema_tags', None):
            return self.view.schema_tags
        queryset = getattr(self.view, 'queryset', None)
        if queryset is not None and queryset.model is not None:
            model = queryset.model
            key = f'{model._meta.app_label}.{model._meta.model_name}'
            return [MODEL_TAGS.get(key, key)]
        module = (self.view.__module__ or '').split('.')[0]
        return [MODEL_TAGS.get(module, module.capitalize() or 'API')]
