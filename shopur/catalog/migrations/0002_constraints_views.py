from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0001_initial'),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL("""

        -- Функция пересчёта суммы заказа
        CREATE OR REPLACE FUNCTION calc_order_total(order_id INT)
        RETURNS NUMERIC AS $$
        DECLARE total NUMERIC := 0;
        BEGIN
            SELECT SUM((oi.quantity * sp.price) * (1 - oi.discount / 100.0))
            INTO total
            FROM orders_orderitem oi
            JOIN catalog_shopproduct sp ON sp.id = oi.shop_product_id
            WHERE oi.order_id = order_id;

            UPDATE orders_order SET total_amount = COALESCE(total, 0)
            WHERE id = order_id;

            RETURN COALESCE(total, 0);
        END;
        $$ LANGUAGE plpgsql;


        -- Проверка наличия товара на складе
        CREATE OR REPLACE FUNCTION check_stock_before_order()
        RETURNS TRIGGER AS $$
        DECLARE available INT;
        BEGIN
            SELECT quantity INTO available FROM catalog_shopproduct WHERE id = NEW.shop_product_id;
            IF available < NEW.quantity THEN
                RAISE EXCEPTION 'Недостаточно товара на складе';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_check_stock
        BEFORE INSERT ON orders_orderitem
        FOR EACH ROW EXECUTE FUNCTION check_stock_before_order();


        -- Уменьшение количества после заказа
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
        FOR EACH ROW EXECUTE FUNCTION reduce_stock_after_order();


        -- Логирование изменений товара
        CREATE OR REPLACE FUNCTION log_product_changes()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO audit_auditlog(user_id, table_name, operation, old_value, new_value, timestamp)
            VALUES (1, 'catalog_product', TG_OP, row_to_json(OLD)::TEXT, row_to_json(NEW)::TEXT, NOW());
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_log_product_changes
        AFTER UPDATE ON catalog_product
        FOR EACH ROW EXECUTE FUNCTION log_product_changes();

        """)
    ]
