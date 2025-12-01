-- Полный скрипт схемы PostgreSQL для проекта shopur
-- Включает таблицы, ограничения, 3+ функций/процедур/триггеров/представлений.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =======================
-- Пользователи и настройки
-- =======================
CREATE TABLE IF NOT EXISTS users_user (
    id BIGSERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMPTZ,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) NOT NULL,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL UNIQUE,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    patronymic VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'ROLE_USER'
);

CREATE TABLE IF NOT EXISTS users_usersettings (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE REFERENCES users_user (id) ON DELETE CASCADE,
    theme VARCHAR(10) NOT NULL DEFAULT 'light',
    language VARCHAR(5) NOT NULL DEFAULT 'ru',
    page_size INTEGER NOT NULL DEFAULT 10,
    saved_filters JSONB
);

CREATE TABLE IF NOT EXISTS users_favorite (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users_user (id) ON DELETE CASCADE,
    shop_product_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, shop_product_id)
);

-- =======================
-- Каталог
-- =======================
CREATE TABLE IF NOT EXISTS catalog_address (
    id BIGSERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    street VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_shop (
    id BIGSERIAL PRIMARY KEY,
    name_shop VARCHAR(100) NOT NULL,
    address_id BIGINT NOT NULL REFERENCES catalog_address (id) ON DELETE CASCADE,
    office_hours VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_category (
    id BIGSERIAL PRIMARY KEY,
    name_category VARCHAR(100) NOT NULL,
    description_category VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_material (
    id BIGSERIAL PRIMARY KEY,
    material_name VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_size (
    id BIGSERIAL PRIMARY KEY,
    size_name VARCHAR(50) NOT NULL,
    description VARCHAR(60) NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_stones (
    id BIGSERIAL PRIMARY KEY,
    stones_name VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS catalog_product (
    id BIGSERIAL PRIMARY KEY,
    name_product VARCHAR(100) NOT NULL,
    description_product VARCHAR(255) NOT NULL,
    category_id BIGINT NOT NULL REFERENCES catalog_category (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS catalog_shopproduct (
    id BIGSERIAL PRIMARY KEY,
    shop_id BIGINT NOT NULL REFERENCES catalog_shop (id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES catalog_product (id) ON DELETE CASCADE,
    material_id BIGINT NOT NULL REFERENCES catalog_material (id) ON DELETE CASCADE,
    size_id BIGINT NOT NULL REFERENCES catalog_size (id) ON DELETE CASCADE,
    stones_id BIGINT NOT NULL REFERENCES catalog_stones (id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    CONSTRAINT uniq_shopproduct_variant UNIQUE (shop_id, product_id, material_id, size_id, stones_id)
);

CREATE TABLE IF NOT EXISTS catalog_productimage (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES catalog_shopproduct (id) ON DELETE CASCADE,
    image_url VARCHAR(255) NOT NULL
);

-- =======================
-- Корзина
-- =======================
CREATE TABLE IF NOT EXISTS cart_cart (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE REFERENCES users_user (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cart_cartitem (
    id BIGSERIAL PRIMARY KEY,
    cart_id BIGINT NOT NULL REFERENCES cart_cart (id) ON DELETE CASCADE,
    shop_product_id BIGINT NOT NULL REFERENCES catalog_shopproduct (id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    CONSTRAINT uniq_cart_item UNIQUE (cart_id, shop_product_id)
);

-- =======================
-- Заказы и оплаты
-- =======================
CREATE TABLE IF NOT EXISTS orders_status (
    id BIGSERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders_order (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users_user (id) ON DELETE CASCADE,
    address_delivery TEXT NOT NULL,
    comment TEXT,
    date_create TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    date_finish TIMESTAMPTZ,
    status_id BIGINT NOT NULL REFERENCES orders_status (id) ON DELETE CASCADE,
    total_amount NUMERIC(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders_orderitem (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders_order (id) ON DELETE CASCADE,
    shop_product_id BIGINT NOT NULL REFERENCES catalog_shopproduct (id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    discount INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders_payment (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders_order (id) ON DELETE CASCADE,
    amount NUMERIC(10,2) NOT NULL,
    payment_date TIMESTAMPTZ NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    transaction_id TEXT,
    status VARCHAR(20) NOT NULL
);

-- =======================
-- Аудит
-- =======================
CREATE TABLE IF NOT EXISTS audit_reportlog (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users_user (id) ON DELETE SET NULL,
    report_type VARCHAR(50) NOT NULL,
    report_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    file_link VARCHAR(200) NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_auditlog (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users_user (id) ON DELETE SET NULL,
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    old_value TEXT,
    new_value TEXT
);

-- =======================
-- Индексы для ускорения
-- =======================
CREATE INDEX IF NOT EXISTS idx_users_favorite_user_id ON users_favorite(user_id);
CREATE INDEX IF NOT EXISTS idx_users_favorite_shop_product_id ON users_favorite(shop_product_id);
CREATE INDEX IF NOT EXISTS idx_cart_cart_user_id ON cart_cart(user_id);
CREATE INDEX IF NOT EXISTS idx_cart_cartitem_cart_id ON cart_cartitem(cart_id);
CREATE INDEX IF NOT EXISTS idx_cart_cartitem_shop_product_id ON cart_cartitem(shop_product_id);
CREATE INDEX IF NOT EXISTS idx_catalog_shopproduct_shop_id ON catalog_shopproduct(shop_id);
CREATE INDEX IF NOT EXISTS idx_catalog_shopproduct_product_id ON catalog_shopproduct(product_id);
CREATE INDEX IF NOT EXISTS idx_catalog_shopproduct_material_id ON catalog_shopproduct(material_id);
CREATE INDEX IF NOT EXISTS idx_catalog_shopproduct_size_id ON catalog_shopproduct(size_id);
CREATE INDEX IF NOT EXISTS idx_catalog_shopproduct_stones_id ON catalog_shopproduct(stones_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_user_id ON orders_order(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_status_id ON orders_order(status_id);
CREATE INDEX IF NOT EXISTS idx_orders_orderitem_order_id ON orders_orderitem(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_orderitem_shop_product_id ON orders_orderitem(shop_product_id);
CREATE INDEX IF NOT EXISTS idx_orders_payment_order_id ON orders_payment(order_id);

-- =======================
-- Функции (3 шт)
-- =======================
-- 1) Общая сумма заказа
CREATE OR REPLACE FUNCTION calc_order_total(p_order_id INT)
RETURNS NUMERIC AS $$
DECLARE
    total NUMERIC := 0;
BEGIN
    SELECT COALESCE(SUM(oi.quantity * sp.price), 0)
    INTO total
    FROM orders_orderitem oi
    JOIN catalog_shopproduct sp ON oi.shop_product_id = sp.id
    WHERE oi.order_id = p_order_id;

    RETURN total;
END;
$$ LANGUAGE plpgsql;

-- 2) Проверка остатка перед созданием позиции заказа
CREATE OR REPLACE FUNCTION check_stock_before_order(p_product_id INT, p_quantity INT)
RETURNS BOOLEAN AS $$
DECLARE
    stock INT;
BEGIN
    SELECT quantity INTO stock
    FROM catalog_shopproduct
    WHERE id = p_product_id;

    RETURN stock >= p_quantity;
END;
$$ LANGUAGE plpgsql;

-- 3) Сумма корзины пользователя
CREATE OR REPLACE FUNCTION calc_cart_total(p_user_id INT)
RETURNS NUMERIC AS $$
DECLARE
    total NUMERIC := 0;
BEGIN
    SELECT COALESCE(SUM(ci.quantity * sp.price), 0)
    INTO total
    FROM cart_cart c
    JOIN cart_cartitem ci ON ci.cart_id = c.id
    JOIN catalog_shopproduct sp ON ci.shop_product_id = sp.id
    WHERE c.user_id = p_user_id;

    RETURN total;
END;
$$ LANGUAGE plpgsql;

-- =======================
-- Процедуры (3 шт)
-- =======================
-- 1) Обновление статуса заказа с логированием
CREATE OR REPLACE PROCEDURE update_order_status(
    p_order_id INT,
    p_status_id INT,
    p_user_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_old_status TEXT;
    v_new_status TEXT;
BEGIN
    SELECT s.status INTO v_old_status
    FROM orders_status s
    JOIN orders_order o ON o.status_id = s.id
    WHERE o.id = p_order_id;

    SELECT status INTO v_new_status
    FROM orders_status
    WHERE id = p_status_id;

    UPDATE orders_order
    SET status_id = p_status_id
    WHERE id = p_order_id;

    INSERT INTO audit_auditlog (user_id, table_name, operation, timestamp, old_value, new_value)
    VALUES (p_user_id, 'orders_order', 'UPDATE', NOW(), v_old_status, v_new_status);
END;
$$;

-- 2) Добавление товара в корзину с авто-созданием корзины
CREATE OR REPLACE PROCEDURE add_item_to_cart(
    p_user_id INT,
    p_shop_product_id INT,
    p_quantity INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_cart_id BIGINT;
BEGIN
    -- на всякий случай проверяем остатки
    IF NOT check_stock_before_order(p_shop_product_id, p_quantity) THEN
        RAISE EXCEPTION 'Недостаточно остатков по товару %', p_shop_product_id;
    END IF;

    SELECT id INTO v_cart_id FROM cart_cart WHERE user_id = p_user_id;
    IF v_cart_id IS NULL THEN
        INSERT INTO cart_cart(user_id) VALUES (p_user_id) RETURNING id INTO v_cart_id;
    END IF;

    INSERT INTO cart_cartitem(cart_id, shop_product_id, quantity)
    VALUES (v_cart_id, p_shop_product_id, p_quantity)
    ON CONFLICT (cart_id, shop_product_id) DO UPDATE
        SET quantity = cart_cartitem.quantity + EXCLUDED.quantity;

    UPDATE cart_cart SET updated_at = NOW() WHERE id = v_cart_id;
END;
$$;

-- 3) Создание платежа и закрытие заказа с логированием
CREATE OR REPLACE PROCEDURE create_payment_and_close_order(
    p_order_id INT,
    p_amount NUMERIC,
    p_payment_method VARCHAR,
    p_transaction_id TEXT,
    p_payment_status VARCHAR,
    p_new_order_status_id INT,
    p_user_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_old_status TEXT;
    v_new_status TEXT;
BEGIN
    SELECT s.status INTO v_old_status
    FROM orders_status s
    JOIN orders_order o ON o.status_id = s.id
    WHERE o.id = p_order_id;

    INSERT INTO orders_payment(order_id, amount, payment_date, payment_method, transaction_id, status)
    VALUES (p_order_id, p_amount, NOW(), p_payment_method, p_transaction_id, p_payment_status);

    UPDATE orders_order
    SET status_id = p_new_order_status_id,
        total_amount = p_amount,
        date_finish = NOW()
    WHERE id = p_order_id;

    SELECT status INTO v_new_status FROM orders_status WHERE id = p_new_order_status_id;

    INSERT INTO audit_auditlog (user_id, table_name, operation, timestamp, old_value, new_value)
    VALUES (p_user_id, 'orders_order', 'UPDATE', NOW(), v_old_status, v_new_status);
END;
$$;

-- =======================
-- Триггеры (3 шт)
-- =======================
-- 1) Логирование изменения каталога
CREATE OR REPLACE FUNCTION log_product_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_auditlog(table_name, operation, timestamp, old_value, new_value)
    VALUES ('catalog_product', TG_OP, NOW(), row_to_json(OLD)::text, row_to_json(NEW)::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_product_update ON catalog_product;
CREATE TRIGGER trg_product_update
AFTER UPDATE ON catalog_product
FOR EACH ROW
EXECUTE FUNCTION log_product_changes();

-- 2) Снижение остатков после добавления позиции заказа
CREATE OR REPLACE FUNCTION reduce_stock_after_order()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE catalog_shopproduct
    SET quantity = quantity - NEW.quantity
    WHERE id = NEW.shop_product_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_reduce_stock ON orders_orderitem;
CREATE TRIGGER trg_reduce_stock
AFTER INSERT ON orders_orderitem
FOR EACH ROW
EXECUTE FUNCTION reduce_stock_after_order();

-- 3) Аудит смены статуса заказа
CREATE OR REPLACE FUNCTION log_order_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status_id IS DISTINCT FROM OLD.status_id THEN
        INSERT INTO audit_auditlog(table_name, operation, timestamp, old_value, new_value)
        VALUES (
            'orders_order',
            TG_OP,
            NOW(),
            OLD.status_id::text,
            NEW.status_id::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_order_status_audit ON orders_order;
CREATE TRIGGER trg_order_status_audit
AFTER UPDATE ON orders_order
FOR EACH ROW
EXECUTE FUNCTION log_order_status_change();

-- =======================
-- Представления (3 шт)
-- =======================
-- 1) Детализация заказов
CREATE OR REPLACE VIEW vw_order_details AS
SELECT
    o.id AS order_id,
    u.email AS user_email,
    o.address_delivery,
    o.date_create,
    o.date_finish,
    st.status AS status,
    o.total_amount,
    calc_order_total(o.id) AS recalculated_total
FROM orders_order o
JOIN users_user u ON o.user_id = u.id
JOIN orders_status st ON o.status_id = st.id;

-- 2) Остатки по товарам
CREATE OR REPLACE VIEW vw_catalog_stock AS
SELECT
    sp.id AS shop_product_id,
    sh.name_shop,
    p.name_product,
    m.material_name,
    sz.size_name,
    stn.stones_name,
    sp.price,
    sp.quantity
FROM catalog_shopproduct sp
JOIN catalog_shop sh ON sp.shop_id = sh.id
JOIN catalog_product p ON sp.product_id = p.id
JOIN catalog_material m ON sp.material_id = m.id
JOIN catalog_size sz ON sp.size_id = sz.id
JOIN catalog_stones stn ON sp.stones_id = stn.id;

-- 3) Избранное пользователей
CREATE OR REPLACE VIEW vw_user_favorites AS
SELECT
    f.id AS favorite_id,
    u.email AS user_email,
    p.name_product,
    sh.name_shop,
    sp.price,
    f.created_at
FROM users_favorite f
JOIN users_user u ON f.user_id = u.id
JOIN catalog_shopproduct sp ON f.shop_product_id = sp.id
JOIN catalog_shop sh ON sp.shop_id = sh.id
JOIN catalog_product p ON sp.product_id = p.id;

-- =======================
-- Примеры использования
-- SELECT calc_order_total(1);
-- CALL update_order_status(1, 2, 10);
-- CALL add_item_to_cart(10, 5, 2);
-- CALL create_payment_and_close_order(1, 1999.99, 'card', 'txn-123', 'paid', 3, 10);
-- SELECT * FROM vw_order_details WHERE order_id = 1;
