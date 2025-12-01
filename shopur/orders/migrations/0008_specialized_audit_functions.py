from django.db import migrations


ORDERS_FUNCTION = """
CREATE OR REPLACE FUNCTION fn_audit_orders_order()
RETURNS trigger AS $$
DECLARE
    v_old_status TEXT;
    v_new_status TEXT;
    v_old_summary TEXT := NULL;
    v_new_summary TEXT := NULL;
BEGIN
    IF TG_OP = 'INSERT' THEN
        SELECT status INTO v_new_status FROM orders_status WHERE id = NEW.status_id;
        v_new_summary := format('Создан заказ #%s, статус "%s", сумма %s', NEW.id, COALESCE(v_new_status, '?'), NEW.total_amount);
    ELSIF TG_OP = 'DELETE' THEN
        SELECT status INTO v_old_status FROM orders_status WHERE id = OLD.status_id;
        v_old_summary := format('Удалён заказ #%s, статус "%s", сумма %s', OLD.id, COALESCE(v_old_status, '?'), OLD.total_amount);
    ELSE
        SELECT status INTO v_old_status FROM orders_status WHERE id = OLD.status_id;
        SELECT status INTO v_new_status FROM orders_status WHERE id = NEW.status_id;
        v_old_summary := format('Статус "%s", сумма %s', COALESCE(v_old_status, '?'), OLD.total_amount);
        v_new_summary := format('Статус "%s", сумма %s', COALESCE(v_new_status, '?'), NEW.total_amount);
    END IF;

    INSERT INTO audit_auditlog(user_id, table_name, operation, old_value, new_value)
    VALUES (NULL, TG_TABLE_NAME, TG_OP, v_old_summary, v_new_summary);
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
"""

PRODUCT_FUNCTION = """
CREATE OR REPLACE FUNCTION fn_audit_catalog_product()
RETURNS trigger AS $$
DECLARE
    v_old_summary TEXT := NULL;
    v_new_summary TEXT := NULL;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_new_summary := format('Добавлен продукт "%s" (%s)', NEW.name_product, NEW.description_product);
    ELSIF TG_OP = 'DELETE' THEN
        v_old_summary := format('Удалён продукт "%s" (%s)', OLD.name_product, OLD.description_product);
    ELSE
        v_old_summary := format('Название: "%s", Описание: "%s"', OLD.name_product, OLD.description_product);
        v_new_summary := format('Название: "%s", Описание: "%s"', NEW.name_product, NEW.description_product);
    END IF;

    INSERT INTO audit_auditlog(user_id, table_name, operation, old_value, new_value)
    VALUES (NULL, TG_TABLE_NAME, TG_OP, v_old_summary, v_new_summary);
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
"""

SHOPPRODUCT_FUNCTION = """
CREATE OR REPLACE FUNCTION fn_audit_catalog_shopproduct()
RETURNS trigger AS $$
DECLARE
    v_old_summary TEXT := NULL;
    v_new_summary TEXT := NULL;
    v_shop_name TEXT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        SELECT name_shop INTO v_shop_name FROM catalog_shop WHERE id = NEW.shop_id;
        v_new_summary := format('В магазин "%s" добавлен SKU товара %s: цена %s, количество %s',
            COALESCE(v_shop_name, '?'), NEW.product_id, NEW.price, NEW.quantity);
    ELSIF TG_OP = 'DELETE' THEN
        SELECT name_shop INTO v_shop_name FROM catalog_shop WHERE id = OLD.shop_id;
        v_old_summary := format('Удалён SKU товара %s из "%s": цена %s, количество %s',
            OLD.product_id, COALESCE(v_shop_name, '?'), OLD.price, OLD.quantity);
    ELSE
        SELECT name_shop INTO v_shop_name FROM catalog_shop WHERE id = NEW.shop_id;
        v_old_summary := format('Магазин "%s", цена %s, количество %s', COALESCE(v_shop_name, '?'), OLD.price, OLD.quantity);
        v_new_summary := format('Магазин "%s", цена %s, количество %s', COALESCE(v_shop_name, '?'), NEW.price, NEW.quantity);
    END IF;

    INSERT INTO audit_auditlog(user_id, table_name, operation, old_value, new_value)
    VALUES (NULL, TG_TABLE_NAME, TG_OP, v_old_summary, v_new_summary);
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_replace_procedures'),
    ]

    operations = [
        migrations.RunSQL(ORDERS_FUNCTION),
        migrations.RunSQL(PRODUCT_FUNCTION),
        migrations.RunSQL(SHOPPRODUCT_FUNCTION),
    ]
