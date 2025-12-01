-- Пример атомарной бизнес-операции внутри PL/pgSQL
CREATE OR REPLACE PROCEDURE sp_create_order_with_items(
    IN p_user_id INT,
    IN p_address VARCHAR,
    IN p_comment VARCHAR,
    IN p_items JSONB
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_id INT;
BEGIN
    -- Старт транзакции: процедура выполняется в рамках одного атомарного блока
    INSERT INTO orders_order (user_id, address_delivery, comment, status_id, total_amount)
    VALUES (p_user_id, p_address, p_comment, (SELECT id FROM orders_status WHERE status = 'Ожидание' LIMIT 1), 0)
    RETURNING id INTO v_order_id;

    -- Добавляем позиции через существующую процедуру (она уже включает проверку ошибок)
    FOR SELECT (item->>'shop_product')::INT, (item->>'quantity')::INT FROM jsonb_array_elements(p_items) AS item LOOP
        CALL sp_add_order_item(v_order_id, $1, $2);
    END LOOP;

    CALL sp_recalculate_order_total(v_order_id);
EXCEPTION WHEN OTHERS THEN
    -- Логирование ошибки + откат
    INSERT INTO audit_auditlog (user_id, table_name, operation, old_value, new_value)
    VALUES (p_user_id, 'Order', 'CREATE_FAILED', NULL, SQLERRM);
    RAISE;
END;
$$;

-- Серверная логика на Python/Django: гарантируем атомарность business-операции
"""
from django.db import transaction, connection

def create_order_from_cart(user, cart_items):
    with transaction.atomic():
        cursor = connection.cursor()
        payload = json.dumps([
            {"shop_product": item.shop_product_id, "quantity": item.quantity}
            for item in cart_items
        ])
        cursor.execute("CALL sp_create_order_with_items(%s, %s, %s, %s)", [
            user.id,
            user.profile.pickup_address,
            '',
            payload
        ])
"""
