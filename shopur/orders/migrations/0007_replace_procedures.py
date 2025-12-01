from django.db import migrations


DROP_OLD = """
DROP PROCEDURE IF EXISTS sp_apply_order_discount(INT, NUMERIC);
DROP PROCEDURE IF EXISTS sp_recalculate_order_total(INT);
DROP PROCEDURE IF EXISTS sp_update_order_status(INT, INT, INT);
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
    SELECT COALESCE(SUM(oi.quantity * sp.price), 0)
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

SP_ADD_ITEM = """
CREATE OR REPLACE PROCEDURE sp_add_order_item(
    IN p_order_id INT,
    IN p_shop_product_id INT,
    IN p_quantity INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_exists INT;
BEGIN
    IF p_quantity <= 0 THEN
        RAISE EXCEPTION 'Quantity must be positive';
    END IF;

    SELECT 1 INTO v_exists FROM orders_order WHERE id = p_order_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Order % not found', p_order_id;
    END IF;

    SELECT 1 INTO v_exists FROM catalog_shopproduct WHERE id = p_shop_product_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Shop product % not found', p_shop_product_id;
    END IF;

    INSERT INTO orders_orderitem (order_id, shop_product_id, quantity, discount)
    VALUES (p_order_id, p_shop_product_id, p_quantity, 0)
    ON CONFLICT (order_id, shop_product_id)
    DO UPDATE SET quantity = orders_orderitem.quantity + EXCLUDED.quantity;

    CALL sp_recalculate_order_total(p_order_id);
END;
$$;
"""

SP_MARK_READY = """
CREATE OR REPLACE PROCEDURE sp_mark_order_ready(
    IN p_order_id INT,
    IN p_actor_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_ready_status INT;
BEGIN
    SELECT id INTO v_ready_status FROM orders_status WHERE status = 'Готов к получению';
    IF v_ready_status IS NULL THEN
        RAISE EXCEPTION 'Status "Готов к получению" not configured';
    END IF;
    CALL sp_update_order_status(p_order_id, v_ready_status, p_actor_id);
END;
$$;
"""

DROP_NEW = """
DROP PROCEDURE IF EXISTS sp_add_order_item(INT, INT, INT);
DROP PROCEDURE IF EXISTS sp_mark_order_ready(INT, INT);
DROP PROCEDURE IF EXISTS sp_recalculate_order_total(INT);
DROP PROCEDURE IF EXISTS sp_update_order_status(INT, INT, INT);
"""


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_audit_triggers'),
    ]

    operations = [
        migrations.RunSQL(DROP_OLD, reverse_sql=""),
        migrations.RunSQL(SP_RECALC_TOTAL, reverse_sql="DROP PROCEDURE IF EXISTS sp_recalculate_order_total(INT);"),
        migrations.RunSQL(SP_UPDATE_STATUS, reverse_sql="DROP PROCEDURE IF EXISTS sp_update_order_status(INT, INT, INT);"),
        migrations.RunSQL(SP_ADD_ITEM, reverse_sql="DROP PROCEDURE IF EXISTS sp_add_order_item(INT, INT, INT);"),
        migrations.RunSQL(SP_MARK_READY, reverse_sql="DROP PROCEDURE IF EXISTS sp_mark_order_ready(INT, INT);"),
    ]
