CREATE OR REPLACE FUNCTION calc_order_total(order_id INT)
RETURNS NUMERIC AS $$
DECLARE
    total NUMERIC := 0;
BEGIN
    SELECT SUM(oi.quantity * sp.price)
    INTO total
    FROM orders_orderitem oi
    JOIN catalog_shopproduct sp ON oi.shop_product_id = sp.id
    WHERE oi.order_id = order_id;

    RETURN COALESCE(total, 0);
END;
$$ LANGUAGE plpgsql; -- расчет общей суммы заказа

CREATE OR REPLACE FUNCTION check_stock_before_order(product_id INT, quantity INT)
RETURNS BOOLEAN AS $$
DECLARE
    stock INT;
BEGIN
    SELECT quantity INTO stock
    FROM catalog_shopproduct
    WHERE id = product_id;

    IF stock >= quantity THEN
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql; -- проверка остатка товара
