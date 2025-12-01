CREATE OR REPLACE PROCEDURE update_order_status(p_order_id INT, p_status_id INT, p_user_id INT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_old_status TEXT;
    v_new_status TEXT;
BEGIN
    SELECT s.status_name INTO v_old_status
    FROM orders_status s
    JOIN orders_order o ON o.status_id = s.id
    WHERE o.id = p_order_id;

    SELECT status_name INTO v_new_status
    FROM orders_status WHERE id = p_status_id;

    UPDATE orders_order
    SET status_id = p_status_id
    WHERE id = p_order_id;

    INSERT INTO audit_auditlog (user_id, action, created_at)
    VALUES (
        p_user_id,
        CONCAT('Изменён статус заказа №', p_order_id, ' с "', v_old_status, '" на "', v_new_status, '"'),
        NOW()
    );
END;
$$;
