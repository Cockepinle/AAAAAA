from django.db import migrations


FUNCTION_SQL = r"""
CREATE OR REPLACE FUNCTION calc_order_total(order_id INT)
RETURNS NUMERIC AS $$
DECLARE
    total NUMERIC := 0;
BEGIN
    SELECT SUM((oi.quantity * sp.price) * (1 - oi.discount / 100.0))
      INTO total
      FROM orders_orderitem oi
      JOIN catalog_shopproduct sp ON oi.shop_product_id = sp.id
     WHERE oi.order_id = $1;  -- use positional parameter to avoid ambiguity

    RETURN COALESCE(total, 0);
END;
$$ LANGUAGE plpgsql;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL(FUNCTION_SQL, reverse_sql=FUNCTION_SQL),
    ]

