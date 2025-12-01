CREATE OR REPLACE FUNCTION log_product_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_auditlog(table_name, operation, timestamp)
    VALUES ('catalog_product', 'UPDATE', NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_product_update
AFTER UPDATE ON catalog_product
FOR EACH ROW
EXECUTE FUNCTION log_product_changes();


CREATE OR REPLACE FUNCTION reduce_stock_after_order()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE catalog_shopproduct
    SET quantity = quantity - NEW.quantity
    WHERE id = NEW.shop_product_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_reduce_stock
AFTER INSERT ON orders_orderitem
FOR EACH ROW
EXECUTE FUNCTION reduce_stock_after_order(); -- уменьшение остатков  при заказе
