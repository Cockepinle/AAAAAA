from django.db import migrations


ORDER_SUMMARY_VIEW = """
CREATE OR REPLACE VIEW orders_order_summary AS
SELECT
    o.id AS order_id,
    u.email AS customer_email,
    o.date_create::date AS order_date,
    s.status AS status_name,
    COALESCE(SUM(oi.quantity), 0) AS items_count,
    COALESCE(SUM((oi.quantity * sp.price) * (1 - oi.discount / 100.0)), o.total_amount) AS calculated_amount,
    o.total_amount AS stored_amount
FROM orders_order o
JOIN users_user u ON u.id = o.user_id
JOIN orders_status s ON s.id = o.status_id
LEFT JOIN orders_orderitem oi ON oi.order_id = o.id
LEFT JOIN catalog_shopproduct sp ON sp.id = oi.shop_product_id
GROUP BY o.id, u.email, o.date_create, s.status, o.total_amount;
"""

CUSTOMER_LTV_VIEW = """
CREATE OR REPLACE VIEW orders_customer_ltv AS
SELECT
    u.id AS user_id,
    u.email AS customer_email,
    COALESCE(SUM(o.total_amount), 0) AS total_spent,
    COUNT(o.id) AS orders_count,
    COALESCE(MAX(o.date_create), '1970-01-01') AS last_order_at
FROM users_user u
LEFT JOIN orders_order o ON o.user_id = u.id
GROUP BY u.id, u.email;
"""

DROP_VIEWS = """
DROP VIEW IF EXISTS orders_order_summary;
DROP VIEW IF EXISTS orders_customer_ltv;
"""

SP_UPDATE_STATUS = """
CREATE OR REPLACE PROCEDURE sp_update_order_status(
    IN p_order_id INT,
    IN p_status_id INT,
    IN p_actor_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_old_status TEXT;
    v_new_status TEXT;
BEGIN
    SELECT s.status INTO v_old_status
    FROM orders_order o
    JOIN orders_status s ON s.id = o.status_id
    WHERE o.id = p_order_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order % not found', p_order_id;
    END IF;

    SELECT status INTO v_new_status
    FROM orders_status
    WHERE id = p_status_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Status % not found', p_status_id;
    END IF;

    UPDATE orders_order
       SET status_id = p_status_id
     WHERE id = p_order_id;

    INSERT INTO audit_auditlog (user_id, table_name, operation, old_value, new_value)
    VALUES (p_actor_id, 'Order', 'STATUS_CHANGE', v_old_status, v_new_status);
END;
$$;
"""

SP_APPLY_DISCOUNT = """
CREATE OR REPLACE PROCEDURE sp_apply_order_discount(
    IN p_order_id INT,
    IN p_discount NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_discount < 0 OR p_discount > 100 THEN
        RAISE EXCEPTION 'Discount % must be between 0 and 100', p_discount;
    END IF;

    UPDATE orders_orderitem
       SET discount = p_discount
     WHERE order_id = p_order_id;

    PERFORM sp_recalculate_order_total(p_order_id);
END;
$$;
"""

SP_RECALC_TOTAL = """
CREATE OR REPLACE PROCEDURE sp_recalculate_order_total(
    IN p_order_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_total NUMERIC := 0;
BEGIN
    SELECT COALESCE(SUM((oi.quantity * sp.price) * (1 - oi.discount / 100.0)), 0)
      INTO v_total
      FROM orders_orderitem oi
      JOIN catalog_shopproduct sp ON sp.id = oi.shop_product_id
     WHERE oi.order_id = p_order_id;

    UPDATE orders_order
       SET total_amount = v_total
     WHERE id = p_order_id;
END;
$$;
"""

DROP_PROCS = """
DROP PROCEDURE IF EXISTS sp_update_order_status(INT, INT, INT);
DROP PROCEDURE IF EXISTS sp_apply_order_discount(INT, NUMERIC);
DROP PROCEDURE IF EXISTS sp_recalculate_order_total(INT);
"""


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0004_merge_20250220_0000'),
    ]

    operations = [
        migrations.RunSQL(ORDER_SUMMARY_VIEW, reverse_sql="DROP VIEW IF EXISTS orders_order_summary;"),
        migrations.RunSQL(CUSTOMER_LTV_VIEW, reverse_sql="DROP VIEW IF EXISTS orders_customer_ltv;"),
        migrations.RunSQL(SP_RECALC_TOTAL, reverse_sql="DROP PROCEDURE IF EXISTS sp_recalculate_order_total(INT);"),
        migrations.RunSQL(SP_UPDATE_STATUS, reverse_sql="DROP PROCEDURE IF EXISTS sp_update_order_status(INT, INT, INT);"),
        migrations.RunSQL(SP_APPLY_DISCOUNT, reverse_sql="DROP PROCEDURE IF EXISTS sp_apply_order_discount(INT, NUMERIC);"),
    ]
