
import sqlite3
import csv
import shutil
from datetime import datetime, timedelta
from config import Config, ensure_data_files
from logger import get_logger

logger = get_logger(__name__)


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class DBBase:
    def __init__(self):
        ensure_data_files()
        self.db_path = Config.PURCHASES_DB

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=Config.DB_TIMEOUT)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn


class PurchaseDB(DBBase):
    """SQLite storage for purchases (keeps last N)."""

    def __init__(self):
        super().__init__()
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    customer TEXT NOT NULL,
                    customer_email TEXT,
                    product TEXT NOT NULL,
                    amount REAL NOT NULL,
                    quantity REAL,
                    unit_price REAL,
                    subtotal REAL,
                    discount REAL,
                    tax REAL,
                    total REAL,
                    currency TEXT,
                    status TEXT NOT NULL,
                    payment_status TEXT,
                    fulfillment_status TEXT,
                    payment_method TEXT,
                    channel TEXT,
                    source TEXT,
                    region TEXT,
                    sales_rep TEXT,
                    invoice_id TEXT,
                    tags TEXT,
                    notes TEXT
                )
                """
            )
            conn.commit()
            self._ensure_columns(conn)

    def _ensure_columns(self, conn):
        existing = {row[1] for row in conn.execute("PRAGMA table_info(purchases)")}
        required = {
            "customer_email": "TEXT",
            "quantity": "REAL",
            "unit_price": "REAL",
            "subtotal": "REAL",
            "discount": "REAL",
            "tax": "REAL",
            "total": "REAL",
            "currency": "TEXT",
            "payment_status": "TEXT",
            "fulfillment_status": "TEXT",
            "payment_method": "TEXT",
            "channel": "TEXT",
            "source": "TEXT",
            "region": "TEXT",
            "sales_rep": "TEXT",
            "invoice_id": "TEXT",
            "tags": "TEXT",
            "notes": "TEXT",
        }
        for name, col_type in required.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE purchases ADD COLUMN {name} {col_type}")
        conn.commit()

    def add_purchase(
        self,
        customer,
        product,
        amount,
        status="Completed",
        customer_email="",
        quantity=1,
        unit_price=None,
        discount=0.0,
        tax=0.0,
        total=None,
        currency=None,
        payment_status="",
        fulfillment_status="",
        payment_method="",
        channel="",
        source="",
        region="",
        sales_rep="",
        invoice_id="",
        tags="",
        notes="",
    ):
        try:
            quantity = float(quantity) if quantity else 1.0
        except ValueError:
            quantity = 1.0
        if quantity <= 0:
            quantity = 1.0

        try:
            amount = float(amount)
        except ValueError:
            amount = 0.0

        if unit_price is None:
            unit_price = amount
        try:
            unit_price = float(unit_price)
        except ValueError:
            unit_price = 0.0

        try:
            discount = float(discount)
        except ValueError:
            discount = 0.0

        try:
            tax = float(tax)
        except ValueError:
            tax = 0.0

        subtotal = max(quantity * unit_price, 0.0)
        computed_total = subtotal - max(discount, 0.0) + max(tax, 0.0)

        if total is None:
            total = computed_total
        try:
            total = float(total)
        except ValueError:
            total = computed_total
        if total < 0:
            total = 0.0

        currency = currency or Config.DEFAULT_CURRENCY
        ts = _now()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO purchases (
                    timestamp, customer, customer_email, product, amount,
                    quantity, unit_price, subtotal, discount, tax, total, currency,
                    status, payment_status, fulfillment_status, payment_method,
                    channel, source, region, sales_rep, invoice_id, tags, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ts,
                    customer,
                    customer_email,
                    product,
                    total,
                    quantity,
                    unit_price,
                    subtotal,
                    discount,
                    tax,
                    total,
                    currency,
                    status,
                    payment_status,
                    fulfillment_status,
                    payment_method,
                    channel,
                    source,
                    region,
                    sales_rep,
                    invoice_id,
                    tags,
                    notes,
                ),
            )
            conn.execute(
                """
                DELETE FROM purchases
                WHERE id NOT IN (
                    SELECT id FROM purchases ORDER BY id DESC LIMIT ?
                )
                """,
                (Config.MAX_RECENT_PURCHASES,),
            )
            conn.commit()

    def get_last_purchases(self, limit=None):
        if limit is None:
            limit = Config.MAX_RECENT_PURCHASES
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT timestamp, customer, customer_email, product,
                       quantity, unit_price, subtotal, discount, tax, total, currency,
                       status, payment_status, fulfillment_status,
                       payment_method, channel, source, region, sales_rep,
                       invoice_id, tags, notes
                FROM purchases
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
            result = []
            for row in rows:
                result.append(
                    {
                        "timestamp": row[0],
                        "customer": row[1],
                        "customer_email": row[2] or "",
                        "product": row[3],
                        "quantity": float(row[4] or 0),
                        "unit_price": float(row[5] or 0),
                        "subtotal": float(row[6] or 0),
                        "discount": float(row[7] or 0),
                        "tax": float(row[8] or 0),
                        "total": float(row[9] or 0),
                        "currency": row[10] or "",
                        "status": row[11] or "",
                        "payment_status": row[12] or "",
                        "fulfillment_status": row[13] or "",
                        "payment_method": row[14] or "",
                        "channel": row[15] or "",
                        "source": row[16] or "",
                        "region": row[17] or "",
                        "sales_rep": row[18] or "",
                        "invoice_id": row[19] or "",
                        "tags": row[20] or "",
                        "notes": row[21] or "",
                    }
                )
            return result

    def search_purchases(self, query="", days=None, limit=20):
        like = f"%{query}%"
        clauses = []
        params = []

        if query:
            clauses.append(
                "(customer LIKE ? OR customer_email LIKE ? OR product LIKE ? "
                "OR notes LIKE ? OR invoice_id LIKE ? OR tags LIKE ?)"
            )
            params.extend([like, like, like, like, like, like])

        if days is not None and days > 0:
            cutoff = datetime.now() - timedelta(days=days)
            clauses.append("timestamp >= ?")
            params.append(cutoff.strftime("%Y-%m-%d %H:%M:%S"))

        sql = (
            "SELECT timestamp, customer, customer_email, product, quantity, unit_price, "
            "subtotal, discount, tax, total, currency, status, payment_status, "
            "fulfillment_status, payment_method, channel, source, region, sales_rep, "
            "invoice_id, tags, notes FROM purchases"
        )
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
            result = []
            for row in rows:
                result.append(
                    {
                        "timestamp": row[0],
                        "customer": row[1],
                        "customer_email": row[2] or "",
                        "product": row[3],
                        "quantity": float(row[4] or 0),
                        "unit_price": float(row[5] or 0),
                        "subtotal": float(row[6] or 0),
                        "discount": float(row[7] or 0),
                        "tax": float(row[8] or 0),
                        "total": float(row[9] or 0),
                        "currency": row[10] or "",
                        "status": row[11] or "",
                        "payment_status": row[12] or "",
                        "fulfillment_status": row[13] or "",
                        "payment_method": row[14] or "",
                        "channel": row[15] or "",
                        "source": row[16] or "",
                        "region": row[17] or "",
                        "sales_rep": row[18] or "",
                        "invoice_id": row[19] or "",
                        "tags": row[20] or "",
                        "notes": row[21] or "",
                    }
                )
            return result

    def get_daily_summary(self, date_label):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*),
                       SUM(COALESCE(total, amount, 0)),
                       AVG(COALESCE(total, amount, 0))
                FROM purchases
                WHERE date(timestamp) = ?
                """,
                (date_label,),
            ).fetchone()
            count = int(row[0] or 0)
            revenue = float(row[1] or 0)
            avg = float(row[2] or 0)
            return {"count": count, "revenue": revenue, "avg": avg}

    def get_sales_trend(self, days=7):
        if days <= 0:
            return []
        offset = f"-{days - 1} days"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT date(timestamp), SUM(COALESCE(total, amount, 0))
                FROM purchases
                WHERE date(timestamp) >= date('now', ?)
                GROUP BY date(timestamp)
                ORDER BY date(timestamp)
                """,
                (offset,),
            ).fetchall()
            return [{"date": r[0], "revenue": float(r[1] or 0)} for r in rows]

    def get_top_products(self, days=7, limit=3):
        if days <= 0:
            return []
        offset = f"-{days - 1} days"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT product, COUNT(*), SUM(COALESCE(total, amount, 0))
                FROM purchases
                WHERE date(timestamp) >= date('now', ?)
                GROUP BY product
                ORDER BY SUM(COALESCE(total, amount, 0)) DESC
                LIMIT ?
                """,
                (offset, limit),
            ).fetchall()
            return [
                {"product": r[0], "count": int(r[1] or 0), "revenue": float(r[2] or 0)}
                for r in rows
            ]

    def export_purchases_csv(self, path, limit=None):
        rows = self.get_last_purchases(limit=limit)
        if not rows:
            return False
        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return True

    def backup_db(self, path):
        shutil.copy2(self.db_path, path)
        return path


class CustomerDB(DBBase):
    def __init__(self):
        super().__init__()
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    company TEXT,
                    industry TEXT,
                    segment TEXT,
                    status TEXT,
                    lead_source TEXT,
                    address_line1 TEXT,
                    address_line2 TEXT,
                    city TEXT,
                    state TEXT,
                    country TEXT,
                    postal_code TEXT,
                    notes TEXT,
                    last_contact_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_customers_email
                ON customers (email)
                """
            )
            conn.commit()
            self._ensure_columns(conn)

    def _ensure_columns(self, conn):
        existing = {row[1] for row in conn.execute("PRAGMA table_info(customers)")}
        required = {
            "industry": "TEXT",
            "segment": "TEXT",
            "status": "TEXT",
            "lead_source": "TEXT",
            "address_line1": "TEXT",
            "address_line2": "TEXT",
            "city": "TEXT",
            "state": "TEXT",
            "country": "TEXT",
            "postal_code": "TEXT",
            "last_contact_at": "TEXT",
            "updated_at": "TEXT",
        }
        for name, col_type in required.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE customers ADD COLUMN {name} {col_type}")
        conn.commit()

    def upsert_customer(
        self,
        name,
        email="",
        phone="",
        company="",
        industry="",
        segment="",
        status="",
        lead_source="",
        address_line1="",
        address_line2="",
        city="",
        state="",
        country="",
        postal_code="",
        notes="",
        last_contact_at="",
    ):
        name = (name or "").strip()
        email = (email or "").strip()
        phone = (phone or "").strip()
        company = (company or "").strip()
        industry = (industry or "").strip()
        segment = (segment or "").strip()
        status = (status or "").strip()
        lead_source = (lead_source or "").strip()
        address_line1 = (address_line1 or "").strip()
        address_line2 = (address_line2 or "").strip()
        city = (city or "").strip()
        state = (state or "").strip()
        country = (country or "").strip()
        postal_code = (postal_code or "").strip()
        notes = (notes or "").strip()
        last_contact_at = (last_contact_at or "").strip()

        if not name:
            return None

        now = _now()

        with self._connect() as conn:
            row = None
            if email:
                row = conn.execute(
                    "SELECT id FROM customers WHERE email = ?", (email,)
                ).fetchone()
            if row is None:
                row = conn.execute(
                    "SELECT id FROM customers WHERE name = ? LIMIT 1", (name,)
                ).fetchone()

            if row:
                customer_id = row[0]
                conn.execute(
                    """
                    UPDATE customers
                    SET name = ?,
                        email = COALESCE(NULLIF(?, ''), email),
                        phone = COALESCE(NULLIF(?, ''), phone),
                        company = COALESCE(NULLIF(?, ''), company),
                        industry = COALESCE(NULLIF(?, ''), industry),
                        segment = COALESCE(NULLIF(?, ''), segment),
                        status = COALESCE(NULLIF(?, ''), status),
                        lead_source = COALESCE(NULLIF(?, ''), lead_source),
                        address_line1 = COALESCE(NULLIF(?, ''), address_line1),
                        address_line2 = COALESCE(NULLIF(?, ''), address_line2),
                        city = COALESCE(NULLIF(?, ''), city),
                        state = COALESCE(NULLIF(?, ''), state),
                        country = COALESCE(NULLIF(?, ''), country),
                        postal_code = COALESCE(NULLIF(?, ''), postal_code),
                        notes = COALESCE(NULLIF(?, ''), notes),
                        last_contact_at = COALESCE(NULLIF(?, ''), last_contact_at),
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        name,
                        email,
                        phone,
                        company,
                        industry,
                        segment,
                        status,
                        lead_source,
                        address_line1,
                        address_line2,
                        city,
                        state,
                        country,
                        postal_code,
                        notes,
                        last_contact_at,
                        now,
                        customer_id,
                    ),
                )
                conn.commit()
                return customer_id

            conn.execute(
                """
                INSERT INTO customers (
                    name, email, phone, company, industry, segment, status,
                    lead_source, address_line1, address_line2, city, state,
                    country, postal_code, notes, last_contact_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    phone,
                    company,
                    industry,
                    segment,
                    status,
                    lead_source,
                    address_line1,
                    address_line2,
                    city,
                    state,
                    country,
                    postal_code,
                    notes,
                    last_contact_at or now,
                    now,
                    now,
                ),
            )
            conn.commit()
            return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def get_customer_by_id(self, customer_id):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, name, email, phone, company, industry, segment, status,
                       lead_source, address_line1, address_line2, city, state, country,
                       postal_code, notes, last_contact_at, created_at, updated_at
                FROM customers
                WHERE id = ?
                """,
                (customer_id,),
            ).fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2] or "",
                "phone": row[3] or "",
                "company": row[4] or "",
                "industry": row[5] or "",
                "segment": row[6] or "",
                "status": row[7] or "",
                "lead_source": row[8] or "",
                "address_line1": row[9] or "",
                "address_line2": row[10] or "",
                "city": row[11] or "",
                "state": row[12] or "",
                "country": row[13] or "",
                "postal_code": row[14] or "",
                "notes": row[15] or "",
                "last_contact_at": row[16] or "",
                "created_at": row[17] or "",
                "updated_at": row[18] or "",
            }

    def list_customers(self, limit=20):
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT id, name, email, phone, company, industry, status, created_at
                FROM customers
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "email": row[2] or "",
                    "phone": row[3] or "",
                    "company": row[4] or "",
                    "industry": row[5] or "",
                    "status": row[6] or "",
                    "created_at": row[7] or "",
                }
                for row in cur.fetchall()
            ]

    def search_customers(self, query, limit=20):
        like = f"%{query}%"
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT id, name, email, phone, company, industry, status, created_at
                FROM customers
                WHERE name LIKE ? OR email LIKE ? OR phone LIKE ? OR company LIKE ?
                      OR industry LIKE ? OR status LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (like, like, like, like, like, like, limit),
            )
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "email": row[2] or "",
                    "phone": row[3] or "",
                    "company": row[4] or "",
                    "industry": row[5] or "",
                    "status": row[6] or "",
                    "created_at": row[7] or "",
                }
                for row in cur.fetchall()
            ]


class ProductDB(DBBase):
    def __init__(self):
        super().__init__()
        self._init_db()
        self._seed_if_empty()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    sku TEXT,
                    category TEXT,
                    price REAL NOT NULL,
                    cost REAL,
                    tax_rate REAL,
                    unit TEXT,
                    description TEXT,
                    features TEXT,
                    best_for TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_products_name
                ON products (name)
                """
            )
            conn.commit()
            self._ensure_columns(conn)

    def _ensure_columns(self, conn):
        existing = {row[1] for row in conn.execute("PRAGMA table_info(products)")}
        required = {
            "cost": "REAL",
            "tax_rate": "REAL",
            "unit": "TEXT",
            "description": "TEXT",
            "updated_at": "TEXT",
        }
        for name, col_type in required.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE products ADD COLUMN {name} {col_type}")
        conn.commit()

    def _seed_if_empty(self):
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            if count > 0:
                return

            seeded = False
            if Config.PRODUCTS_FILE.exists():
                try:
                    with open(Config.PRODUCTS_FILE, newline="", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                    for p in rows:
                        name = (p.get("name") or p.get("Product_Name") or "").strip()
                        if not name:
                            continue
                        price = p.get("price") or p.get("Price") or 0
                        features = p.get("features") or p.get("Features") or ""
                        best_for = p.get("best_for") or p.get("Best_For") or ""
                        conn.execute(
                            """
                            INSERT INTO products (
                                name, sku, category, price, cost, tax_rate, unit,
                                description, features, best_for, active, created_at, updated_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                            """,
                            (
                                name,
                                "",
                                "",
                                float(price),
                                0.0,
                                0.0,
                                "",
                                "",
                                features,
                                best_for,
                                _now(),
                                _now(),
                            ),
                        )
                        seeded = True
                except Exception as exc:
                    logger.warning("Failed to import products from CSV: %s", exc)

            if not seeded:
                samples = [
                    {
                        "name": "CRM Pro",
                        "sku": "CRM-001",
                        "category": "CRM",
                        "price": 99,
                        "features": "Contact management, email tracking, basic reporting",
                        "best_for": "Small teams",
                    },
                    {
                        "name": "Analytics Suite",
                        "sku": "ANL-101",
                        "category": "Analytics",
                        "price": 149,
                        "features": "Dashboards, predictive insights, custom reports",
                        "best_for": "Data teams",
                    },
                    {
                        "name": "Marketing Tool",
                        "sku": "MKT-201",
                        "category": "Marketing",
                        "price": 79,
                        "features": "Email campaigns, social scheduling, A/B testing",
                        "best_for": "Marketing teams",
                    },
                ]
                for p in samples:
                    conn.execute(
                        """
                        INSERT INTO products (
                            name, sku, category, price, cost, tax_rate, unit,
                            description, features, best_for, active, created_at, updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                        """,
                        (
                            p["name"],
                            p["sku"],
                            p["category"],
                            p["price"],
                            0.0,
                            0.0,
                            "",
                            "",
                            p["features"],
                            p["best_for"],
                            _now(),
                            _now(),
                        ),
                    )

            conn.commit()

    def list_products(self, active_only=True):
        sql = (
            "SELECT id, name, sku, category, price, cost, tax_rate, unit, description, "
            "features, best_for, active FROM products"
        )
        params = []
        if active_only:
            sql += " WHERE active = 1"
        sql += " ORDER BY id ASC"

        with self._connect() as conn:
            cur = conn.execute(sql, params)
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "sku": row[2] or "",
                    "category": row[3] or "",
                    "price": float(row[4] or 0),
                    "cost": float(row[5] or 0),
                    "tax_rate": float(row[6] or 0),
                    "unit": row[7] or "",
                    "description": row[8] or "",
                    "features": row[9] or "",
                    "best_for": row[10] or "",
                    "active": int(row[11]),
                }
                for row in cur.fetchall()
            ]

    def get_product_by_id(self, product_id):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, name, sku, category, price, cost, tax_rate, unit,
                       description, features, best_for, active
                FROM products
                WHERE id = ?
                """,
                (product_id,),
            ).fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "sku": row[2] or "",
                "category": row[3] or "",
                "price": float(row[4] or 0),
                "cost": float(row[5] or 0),
                "tax_rate": float(row[6] or 0),
                "unit": row[7] or "",
                "description": row[8] or "",
                "features": row[9] or "",
                "best_for": row[10] or "",
                "active": int(row[11]),
            }

    def add_product(
        self,
        name,
        price,
        features="",
        best_for="",
        sku="",
        category="",
        cost=0.0,
        tax_rate=0.0,
        unit="",
        description="",
    ):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO products (
                    name, sku, category, price, cost, tax_rate, unit, description,
                    features, best_for, active, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    name.strip(),
                    sku.strip(),
                    category.strip(),
                    float(price),
                    float(cost),
                    float(tax_rate),
                    unit.strip(),
                    description.strip(),
                    features.strip(),
                    best_for.strip(),
                    _now(),
                    _now(),
                ),
            )
            conn.commit()

    def update_product(self, product_id, **fields):
        allowed = {
            "name",
            "sku",
            "category",
            "price",
            "cost",
            "tax_rate",
            "unit",
            "description",
            "features",
            "best_for",
            "active",
        }
        updates = []
        params = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            updates.append(f"{key} = ?")
            params.append(value)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(_now())
        params.append(product_id)

        with self._connect() as conn:
            conn.execute(
                f"UPDATE products SET {', '.join(updates)} WHERE id = ?", params
            )
            conn.commit()
            return True

    def deactivate_product(self, product_id):
        return self.update_product(product_id, active=0)

    def activate_product(self, product_id):
        return self.update_product(product_id, active=1)

