from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix audit triggers'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Drop all old triggers and functions
            cursor.execute("DROP TRIGGER IF EXISTS trg_catalog_product_audit ON catalog_product CASCADE")
            cursor.execute("DROP TRIGGER IF EXISTS trg_catalog_shopproduct_audit ON catalog_shopproduct CASCADE")
            cursor.execute("DROP TRIGGER IF EXISTS trg_orders_audit ON orders_order CASCADE")
            cursor.execute("DROP FUNCTION IF EXISTS fn_audit_catalog_product() CASCADE")
            cursor.execute("DROP FUNCTION IF EXISTS fn_audit_catalog_shopproduct() CASCADE")
            cursor.execute("DROP FUNCTION IF EXISTS fn_audit_orders() CASCADE")
            # Legacy trigger from migration catalog.0002 that hardcoded user_id = 1
            cursor.execute("DROP TRIGGER IF EXISTS trg_log_product_changes ON catalog_product CASCADE")
            cursor.execute("DROP FUNCTION IF EXISTS log_product_changes() CASCADE")

            # Create function for catalog_product
            sql_product = """
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
            """
            cursor.execute(sql_product)

            # Create trigger for catalog_product
            cursor.execute("""
            CREATE TRIGGER trg_catalog_product_audit
            AFTER INSERT OR UPDATE OR DELETE ON catalog_product
            FOR EACH ROW
            EXECUTE FUNCTION fn_audit_catalog_product()
            """)

            # Create function for catalog_shopproduct
            sql_shopproduct = """
            CREATE OR REPLACE FUNCTION fn_audit_catalog_shopproduct()
            RETURNS TRIGGER AS $$
            DECLARE
                v_new_summary TEXT := '';
            BEGIN
                IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
                    v_new_summary := 'ShopProduct updated';
                    INSERT INTO audit_auditlog(table_name, operation, new_value, timestamp)
                    VALUES (TG_TABLE_NAME, TG_OP, v_new_summary, NOW());
                ELSIF TG_OP = 'DELETE' THEN
                    INSERT INTO audit_auditlog(table_name, operation, timestamp)
                    VALUES (TG_TABLE_NAME, TG_OP, NOW());
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
            cursor.execute(sql_shopproduct)

            # Create trigger for catalog_shopproduct
            cursor.execute("""
            CREATE TRIGGER trg_catalog_shopproduct_audit
            AFTER INSERT OR UPDATE OR DELETE ON catalog_shopproduct
            FOR EACH ROW
            EXECUTE FUNCTION fn_audit_catalog_shopproduct()
            """)

            # Create function for orders
            sql_orders = """
            CREATE OR REPLACE FUNCTION fn_audit_orders()
            RETURNS TRIGGER AS $$
            DECLARE
                v_new_summary TEXT := '';
            BEGIN
                IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
                    v_new_summary := 'Order #' || NEW.id;
                    INSERT INTO audit_auditlog(table_name, operation, new_value, timestamp)
                    VALUES (TG_TABLE_NAME, TG_OP, v_new_summary, NOW());
                ELSIF TG_OP = 'DELETE' THEN
                    INSERT INTO audit_auditlog(table_name, operation, timestamp)
                    VALUES (TG_TABLE_NAME, TG_OP, NOW());
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
            cursor.execute(sql_orders)

            # Create trigger for orders
            cursor.execute("""
            CREATE TRIGGER trg_orders_audit
            AFTER INSERT OR UPDATE OR DELETE ON orders_order
            FOR EACH ROW
            EXECUTE FUNCTION fn_audit_orders()
            """)

        self.stdout.write(self.style.SUCCESS('All triggers fixed successfully'))

