DROP TRIGGER IF EXISTS trg_catalog_product_audit ON catalog_product CASCADE;
DROP FUNCTION IF EXISTS fn_audit_catalog_product() CASCADE;

CREATE OR REPLACE FUNCTION fn_audit_catalog_product()
RETURNS TRIGGER AS $$
DECLARE
    v_old_summary TEXT := '';
    v_new_summary TEXT := '';
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_new_summary := NEW.name_product || ' ' || COALESCE(NEW.description_product, '');
        INSERT INTO audit_auditlog(table_name, operation, new_value, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, v_new_summary, NOW());
    ELSIF TG_OP = 'UPDATE' THEN
        v_old_summary := OLD.name_product || ' ' || COALESCE(OLD.description_product, '');
        v_new_summary := NEW.name_product || ' ' || COALESCE(NEW.description_product, '');
        INSERT INTO audit_auditlog(table_name, operation, old_value, new_value, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, v_old_summary, v_new_summary, NOW());
    ELSIF TG_OP = 'DELETE' THEN
        v_old_summary := OLD.name_product || ' ' || COALESCE(OLD.description_product, '');
        INSERT INTO audit_auditlog(table_name, operation, old_value, timestamp)
        VALUES (TG_TABLE_NAME, TG_OP, v_old_summary, NOW());
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_catalog_product_audit
AFTER INSERT OR UPDATE OR DELETE ON catalog_product
FOR EACH ROW
EXECUTE FUNCTION fn_audit_catalog_product();
