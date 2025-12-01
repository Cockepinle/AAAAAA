from decimal import Decimal

from django.db import transaction, connection
from rest_framework import serializers

from .models import Order, OrderItem, Status, Payment


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'


class OrderItemInCreate(serializers.Serializer):
    shop_product = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    address_delivery = serializers.CharField(max_length=255)
    comment = serializers.CharField(allow_blank=True, required=False)
    items = OrderItemInCreate(many=True)

    def create(self, validated_data):
        user = self.context['request'].user
        with transaction.atomic():
            status_obj, _ = Status.objects.get_or_create(status="Ожидание")

            order = Order.objects.create(
                user=user,
                address_delivery=validated_data['address_delivery'],
                comment=validated_data.get('comment', ''),
                status=status_obj,
                total_amount=Decimal('0')
            )

            for item in validated_data['items']:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "CALL sp_add_order_item(%s, %s, %s)",
                        [order.id, item['shop_product'], item['quantity']]
                    )

            with connection.cursor() as cursor:
                cursor.execute("CALL sp_recalculate_order_total(%s)", [order.id])

            order.refresh_from_db(fields=['total_amount'])
        return order


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
