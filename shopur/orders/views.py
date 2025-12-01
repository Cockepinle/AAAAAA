# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from cart.models import Cart, CartItem
from .models import Order, OrderItem, Payment, Status
from .serializers import (
    OrderCreateSerializer,
    OrderItemSerializer,
    OrderSerializer,
    PaymentSerializer,
    StatusSerializer
)
from .utils import compute_order_analytics, export_analytics_csv

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Шрифт по умолчанию
RECEIPT_FONT = "Arial"

# Путь к стандартному Arial в Windows
arial_path = r"C:\Windows\Fonts\arial.ttf"

# Регистрируем Arial
if os.path.exists(arial_path):
    pdfmetrics.registerFont(TTFont("Arial", arial_path))
else:
    # если Arial вдруг нет
    RECEIPT_FONT = "Helvetica"

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

PAID_KEYWORDS = {'paid', 'completed', 'success', 'done', 'оплачен', 'принят'}

def is_payment_confirmed(status):
    status = (status or '').lower()
    return any(keyword in status for keyword in PAID_KEYWORDS)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @action(detail=False, methods=['post'])
    def place(self, request):
        ser = OrderCreateSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        order = ser.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class StatusViewSet(viewsets.ModelViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer


def _is_manager(user):
    return getattr(user, 'role', '') == 'ROLE_MANAGER' or user.is_staff or user.is_superuser


# --- Web views ---
@login_required
def orders_list_view(request):
    is_manager = _is_manager(request.user)
    if request.method == 'POST' and is_manager:
        order_id = request.POST.get('order_id')
        status_id = request.POST.get('status_id')
        if order_id and status_id:
            try:
                order = Order.objects.get(id=order_id)
                new_status = Status.objects.get(id=status_id)
                order.status = new_status
                order.save(update_fields=['status'])
            except (Order.DoesNotExist, Status.DoesNotExist):
                pass

    if is_manager:
        orders = Order.objects.select_related('status', 'user').order_by('-date_create')
        # убираем дубль статусов (если в БД есть одинаковые названия)
        try:
            statuses = Status.objects.order_by('status', 'id').distinct('status')
        except Exception:
            statuses = Status.objects.order_by('status', 'id')
    else:
        orders = Order.objects.filter(user=request.user).select_related('status').order_by('-date_create')
        statuses = None
    return render(request, 'orders/orders_list.html', {'orders': orders, 'is_manager': is_manager, 'statuses': statuses})


@login_required
def order_detail_view(request, order_id):
    base_qs = Order.objects.select_related('status', 'user').prefetch_related('orderitem_set__shop_product__product')
    if _is_manager(request.user):
        order = get_object_or_404(base_qs, id=order_id)
    else:
        order = get_object_or_404(base_qs, id=order_id, user=request.user)
    items = OrderItem.objects.filter(order=order).select_related('shop_product', 'shop_product__product')
    for item in items:
        item.line_total = item.quantity * item.shop_product.price
    payment = Payment.objects.filter(order=order).order_by('-payment_date').first()
    payment_status_text = payment.status if payment else 'Не оплачен'
    payment_label = 'Оплачен' if is_payment_confirmed(payment_status_text) else 'Не оплачен'
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'items': items,
        'payment_status': payment_status_text,
        'payment_label': payment_label,
    })


@require_POST
def place_order_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'auth_required'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        payload = {}

    ser = OrderCreateSerializer(data=payload, context={'request': request})
    if not ser.is_valid():
        return JsonResponse({'error': ser.errors}, status=400)

    with transaction.atomic():
        order = ser.save()

        # clear only selected items from user's cart
        try:
            cart = Cart.objects.get(user=request.user)
            selected_ids = [it.get('shop_product') for it in payload.get('items', []) if isinstance(it, dict) and it.get('shop_product')]
            if selected_ids:
                CartItem.objects.filter(cart=cart, shop_product_id__in=selected_ids).delete()
        except Cart.DoesNotExist:
            pass

    return JsonResponse(OrderSerializer(order).data, status=201)


@login_required
def download_receipt_view(request, order_id):
    base_qs = Order.objects.select_related('status', 'user').prefetch_related(
        'orderitem_set__shop_product__product',
        'orderitem_set__shop_product__material',
        'orderitem_set__shop_product__size',
    )
    if _is_manager(request.user):
        order = get_object_or_404(base_qs, id=order_id)
    else:
        order = get_object_or_404(base_qs, id=order_id, user=request.user)
    items = OrderItem.objects.filter(order=order).select_related('shop_product', 'shop_product__product', 'shop_product__material', 'shop_product__size')
    payment = Payment.objects.filter(order=order).order_by('-payment_date').first()
    payment_status_text = payment.status if payment else 'Не оплачен'

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{order.id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName=RECEIPT_FONT,
        fontSize=18,
        textColor=colors.HexColor('#1c1b19'),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontName=RECEIPT_FONT,
        fontSize=12,
        textColor=colors.HexColor('#1c1b19'),
        spaceAfter=8,
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=RECEIPT_FONT,
        fontSize=10,
        textColor=colors.HexColor('#1c1b19'),
    )

    story.append(Paragraph('LUMENOVA', title_style))
    story.append(Paragraph(f'Чек №{order.id}', heading_style))
    story.append(Spacer(1, 0.3*cm))

    order_date = order.date_create.strftime('%d.%m.%Y %H:%M')
    order_status = order.status.status if order.status else 'N/A'
    delivery = order.address_delivery or 'Not specified'

    info_data = [
        [Paragraph('Дата:', normal_style), Paragraph(order_date, normal_style)],
        [Paragraph('Статус:', normal_style), Paragraph(order_status, normal_style)],
        [Paragraph('Оплата:', normal_style), Paragraph(payment_status_text, normal_style)],
        [Paragraph('Доставка:', normal_style), Paragraph(delivery, normal_style)],
    ]

    info_table = Table(info_data, colWidths=[3*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), RECEIPT_FONT, 9),
        ('FONT', (1, 0), (1, -1), RECEIPT_FONT, 9),
        ('TEXTCOLOR', (0, 0), (1, -1), colors.HexColor('#1c1b19')),
        ('ROWBACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f5ef')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5dfd3')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph('Позиции', heading_style))

    items_data = [
        [
            Paragraph('#', normal_style),
            Paragraph('Товар', normal_style),
            Paragraph('Материал', normal_style),
            Paragraph('Размер', normal_style),
            Paragraph('Кол-во', normal_style),
            Paragraph('Цена', normal_style),
            Paragraph('Итого', normal_style),
        ]
    ]
    for idx, item in enumerate(items, 1):
        product_name = item.shop_product.product.name_product[:30]
        material_name = item.shop_product.material.material_name[:15]
        size_name = item.shop_product.size.size_name[:10]
        qty = str(item.quantity)
        price = f"{item.shop_product.price}"
        total = f"{item.quantity * item.shop_product.price}"

        items_data.append([
            Paragraph(str(idx), normal_style),
            Paragraph(product_name, normal_style),
            Paragraph(material_name, normal_style),
            Paragraph(size_name, normal_style),
            Paragraph(qty, normal_style),
            Paragraph(price, normal_style),
            Paragraph(total, normal_style),
        ])

    items_table = Table(items_data, colWidths=[0.6*cm, 4*cm, 2.5*cm, 1.5*cm, 1*cm, 1.8*cm, 2*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c9b38f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONT', (0, 0), (-1, 0), RECEIPT_FONT, 9),
        ('FONT', (0, 1), (-1, -1), RECEIPT_FONT, 8),
        ('ROWBACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f5ef')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5dfd3')),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.4*cm))

    total_amount = f"{order.total_amount}"
    total_data = [
        [
            Paragraph('', normal_style),
            Paragraph('', normal_style),
            Paragraph('', normal_style),
            Paragraph('', normal_style),
            Paragraph('ИТОГО:', normal_style),
            Paragraph(total_amount, normal_style),
        ]
    ]
    total_table = Table(total_data, colWidths=[0.6*cm, 4*cm, 2.5*cm, 1.5*cm, 1.8*cm, 2*cm])
    total_table.setStyle(TableStyle([
        ('FONT', (-2, -1), (-1, -1), RECEIPT_FONT, 11),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1c1b19')),
        ('ALIGN', (-2, -1), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#c9b38f')),
        ('TEXTCOLOR', (-2, -1), (-1, -1), colors.whitesmoke),
        ('RIGHTPADDING', (-2, -1), (-1, -1), 8),
        ('LEFTPADDING', (-2, -1), (-1, -1), 8),
        ('TOPPADDING', (-2, -1), (-1, -1), 6),
        ('BOTTOMPADDING', (-2, -1), (-1, -1), 6),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 0.5*cm))

    if order.comment:
        story.append(Paragraph(f'<b>Комментарий:</b> {order.comment}', normal_style))

    story.append(Spacer(1, 0.3*cm))
    print_date = datetime.now().strftime('%d.%m.%Y %H:%M')
    story.append(Paragraph(f'Дата печати: {print_date}', normal_style))
    story.append(Paragraph('Спасибо за покупку!', normal_style))

    doc.build(story)
    return response


@login_required
def manager_analytics_view(request):
    if not _is_manager(request.user):
        return HttpResponse(status=403)

    today = datetime.today().date()
    default_start = today - timedelta(days=30)
    default_end = today

    try:
        start_date = datetime.strptime(request.GET.get('start_date', ''), '%Y-%m-%d').date()
    except Exception:
        start_date = default_start

    try:
        end_date = datetime.strptime(request.GET.get('end_date', ''), '%Y-%m-%d').date()
    except Exception:
        end_date = default_end

    selected_status = request.GET.get('status') or None

    analytics = compute_order_analytics(start_date, end_date, status_id=selected_status)

    if request.GET.get('export') == 'csv':
        return export_analytics_csv(start_date, end_date, analytics, user=request.user)

    statuses = Status.objects.all()

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'selected_status': str(selected_status) if selected_status else '',
        'statuses': statuses,
        'summary': analytics['summary'],
        'top_customers': analytics['top_customers'],
        'status_breakdown': analytics['status_breakdown'],
        'top_products': analytics['top_products'],
        'chart_payload': analytics['chart_payload'],
    }
    return render(request, 'orders/manager_analytics.html', context)
