from django.db import migrations


ORDER_AUDIT_FUNCTION = """
CREATE OR REPLACE FUNCTION fn_audit_orders_order()
RETURNS trigger AS $$
DECLARE
    v_old TEXT := NULL;
    v_new TEXT := NULL;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_new := row_to_json(NEW)::text;
    ELSIF TG_OP = 'DELETE' THEN
        v_old := row_to_json(OLD)::text;
    ELSE
        v_old := row_to_json(OLD)::text;
        v_new := row_to_json(NEW)::text;
    END IF;

    INSERT INTO audit_auditlog(user_id, table_name, operation, old_value, new_value)
    VALUES (NULL, TG_TABLE_NAME, TG_OP, v_old, v_new);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
"""

PRODUCT_AUDIT_FUNCTION = """
CREATE OR REPLACE FUNCTION fn_audit_catalog_product()
RETURNS trigger AS $$
DECLARE
    v_old TEXT := NULL;
    v_new TEXT := NULL;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_new := row_to_json(NEW)::text;
    ELSIF TG_OP = 'DELETE' THEN
        v_old := row_to_json(OLD)::text;
    ELSE
        v_old := row_to_json(OLD)::text;
        v_new := row_to_json(NEW)::text;
    END IF;

    INSERT INTO audit_auditlog(user_id, table_name, operation, old_value, new_value)
    VALUES (NULL, TG_TABLE_NAME, TG_OP, v_old, v_new);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
"""

SHOPPRODUCT_AUDIT_FUNCTION = """
CREATE OR REPLACE FUNCTION fn_audit_catalog_shopproduct()
RETURNS trigger AS $$
DECLARE
    v_old TEXT := NULL;
    v_new TEXT := NULL;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_new := row_to_json(NEW)::text;
    ELSIF TG_OP = 'DELETE' THEN
        v_old := row_to_json(OLD)::text;
    ELSE
        v_old := row_to_json(OLD)::text;
        v_new := row_to_json(NEW)::text;
    END IF;

    INSERT INTO audit_auditlog(user_id, table_name, operation, old_value, new_value)
    VALUES (NULL, TG_TABLE_NAME, TG_OP, v_old, v_new);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
"""

DROP_FUNCTIONS = """
DROP FUNCTION IF EXISTS fn_audit_orders_order() CASCADE;
DROP FUNCTION IF EXISTS fn_audit_catalog_product() CASCADE;
DROP FUNCTION IF EXISTS fn_audit_catalog_shopproduct() CASCADE;
"""

ORDER_TRIGGER = """
CREATE TRIGGER trg_orders_order_audit
AFTER INSERT OR UPDATE OR DELETE ON orders_order
FOR EACH ROW EXECUTE FUNCTION fn_audit_orders_order();
"""

PRODUCT_TRIGGER = """
CREATE TRIGGER trg_catalog_product_audit
AFTER INSERT OR UPDATE OR DELETE ON catalog_product
FOR EACH ROW EXECUTE FUNCTION fn_audit_catalog_product();
"""

SHOPPRODUCT_TRIGGER = """
CREATE TRIGGER trg_catalog_shopproduct_audit
AFTER INSERT OR UPDATE OR DELETE ON catalog_shopproduct
FOR EACH ROW EXECUTE FUNCTION fn_audit_catalog_shopproduct();
"""

DROP_TRIGGERS = """
DROP TRIGGER IF EXISTS trg_orders_order_audit ON orders_order;
DROP TRIGGER IF EXISTS trg_catalog_product_audit ON catalog_product;
DROP TRIGGER IF EXISTS trg_catalog_shopproduct_audit ON catalog_shopproduct;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_views_and_procedures'),
    ]

    operations = [
        migrations.RunSQL(ORDER_AUDIT_FUNCTION, reverse_sql="DROP FUNCTION IF EXISTS fn_audit_orders_order() CASCADE;"),
        migrations.RunSQL(PRODUCT_AUDIT_FUNCTION, reverse_sql="DROP FUNCTION IF EXISTS fn_audit_catalog_product() CASCADE;"),
        migrations.RunSQL(SHOPPRODUCT_AUDIT_FUNCTION, reverse_sql="DROP FUNCTION IF EXISTS fn_audit_catalog_shopproduct() CASCADE;"),
        migrations.RunSQL(ORDER_TRIGGER, reverse_sql="DROP TRIGGER IF EXISTS trg_orders_order_audit ON orders_order;"),
        migrations.RunSQL(PRODUCT_TRIGGER, reverse_sql="DROP TRIGGER IF EXISTS trg_catalog_product_audit ON catalog_product;"),
        migrations.RunSQL(SHOPPRODUCT_TRIGGER, reverse_sql="DROP TRIGGER IF EXISTS trg_catalog_shopproduct_audit ON catalog_shopproduct;"),
    ]
