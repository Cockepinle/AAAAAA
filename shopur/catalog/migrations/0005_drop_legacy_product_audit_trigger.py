from django.db import migrations


DROP_TRIGGER = """
DO $$
BEGIN
    -- Отключаем устаревший аудит, который проставлял user_id = 1
    IF EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_log_product_changes'
    ) THEN
        DROP TRIGGER IF EXISTS trg_log_product_changes ON catalog_product;
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'log_product_changes'
    ) THEN
        DROP FUNCTION IF EXISTS log_product_changes() CASCADE;
    END IF;
END;
$$;
"""


CREATE_TRIGGER_BACK = """
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
"""


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_shopproduct_uniq_shopproduct_variant'),
    ]

    operations = [
        migrations.RunSQL(DROP_TRIGGER, reverse_sql=CREATE_TRIGGER_BACK),
    ]
