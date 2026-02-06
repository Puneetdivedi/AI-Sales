from datetime import datetime
from pathlib import Path
from monitoring import SalesMonitor
from db import ProductDB, CustomerDB
from config import validate_config, Config
from logger import get_logger
from ui import print_table, pretty_money, print_kv

logger = get_logger(__name__)


def prompt_text(label, default=None):
    value = input(label).strip()
    return value if value else default


def prompt_float(label, default_value):
    while True:
        value = input(label).strip()
        if not value:
            return default_value
        try:
            return float(value)
        except ValueError:
            print("Please enter a valid number.")


def prompt_int(label, default_value=None):
    while True:
        value = input(label).strip()
        if not value:
            return default_value
        try:
            return int(value)
        except ValueError:
            print("Please enter a valid integer.")


def prompt_yes_no(label, default=True):
    hint = "Y/n" if default else "y/N"
    value = input(f"{label} ({hint}): ").strip().lower()
    if not value:
        return default
    return value in ("y", "yes")


def list_products(product_db, active_only=True):
    products = product_db.list_products(active_only=active_only)
    rows = []
    for p in products:
        rows.append(
            {
                "id": p["id"],
                "name": p["name"],
                "sku": p["sku"],
                "category": p["category"],
                "price": pretty_money(p["price"]),
                "active": "Yes" if p["active"] == 1 else "No",
            }
        )
    print_table(
        rows,
        [
            ("id", "ID"),
            ("name", "Name"),
            ("sku", "SKU"),
            ("category", "Category"),
            ("price", "Price"),
            ("active", "Active"),
        ],
        title="\nProducts",
        max_width=24,
    )
    return products


def add_product(product_db):
    name = prompt_text("Product name: ", "")
    if not name:
        print("Name is required.")
        return

    price = prompt_float("Price: ", 0.0)
    cost = prompt_float("Cost (optional): ", 0.0)
    tax_rate = prompt_float("Tax rate (0-1, optional): ", 0.0)
    unit = prompt_text("Unit (optional, e.g. license/seat): ", "")
    description = prompt_text("Description (optional): ", "")
    features = prompt_text("Features (optional): ", "")
    best_for = prompt_text("Best for (optional): ", "")
    sku = prompt_text("SKU (optional): ", "")
    category = prompt_text("Category (optional): ", "")

    product_db.add_product(
        name=name,
        price=price,
        features=features,
        best_for=best_for,
        sku=sku,
        category=category,
        cost=cost,
        tax_rate=tax_rate,
        unit=unit,
        description=description,
    )
    print("Product added.")


def edit_product(product_db):
    list_products(product_db, active_only=False)
    product_id = prompt_int("Enter Product ID to edit: ", None)
    if not product_id:
        return

    product = product_db.get_product_by_id(product_id)
    if not product:
        print("Product not found.")
        return

    print("Leave fields empty to keep current values.")
    name = prompt_text(f"Name [{product['name']}]: ", "")
    sku = prompt_text(f"SKU [{product['sku']}]: ", "")
    category = prompt_text(f"Category [{product['category']}]: ", "")
    price = prompt_text(f"Price [{product['price']}]: ", "")
    cost = prompt_text(f"Cost [{product['cost']}]: ", "")
    tax_rate = prompt_text(f"Tax rate [{product['tax_rate']}]: ", "")
    unit = prompt_text(f"Unit [{product['unit']}]: ", "")
    description = prompt_text("Description (optional): ", "")
    features = prompt_text(f"Features [{product['features']}]: ", "")
    best_for = prompt_text(f"Best for [{product['best_for']}]: ", "")

    updates = {}
    if name:
        updates["name"] = name
    if sku:
        updates["sku"] = sku
    if category:
        updates["category"] = category
    if price:
        try:
            updates["price"] = float(price)
        except ValueError:
            print("Invalid price; skipping update for price.")
    if cost:
        try:
            updates["cost"] = float(cost)
        except ValueError:
            print("Invalid cost; skipping update for cost.")
    if tax_rate:
        try:
            updates["tax_rate"] = float(tax_rate)
        except ValueError:
            print("Invalid tax rate; skipping update for tax rate.")
    if unit:
        updates["unit"] = unit
    if description:
        updates["description"] = description
    if features:
        updates["features"] = features
    if best_for:
        updates["best_for"] = best_for

    if updates:
        product_db.update_product(product_id, **updates)
        print("Product updated.")
    else:
        print("No changes made.")


def toggle_product(product_db, activate=False):
    list_products(product_db, active_only=False)
    product_id = prompt_int(
        "Enter Product ID to activate: " if activate else "Enter Product ID to deactivate: ",
        None,
    )
    if not product_id:
        return

    product = product_db.get_product_by_id(product_id)
    if not product:
        print("Product not found.")
        return

    if activate:
        product_db.activate_product(product_id)
        print("Product activated.")
    else:
        product_db.deactivate_product(product_id)
        print("Product deactivated.")


def manage_products(product_db):
    while True:
        print("\nProduct Management")
        print("1. List products")
        print("2. Add product")
        print("3. Edit product")
        print("4. Deactivate product")
        print("5. Activate product")
        print("6. Back")

        choice = input("Choose an option (1-6): ").strip()
        if choice == "1":
            list_products(product_db, active_only=False)
        elif choice == "2":
            add_product(product_db)
        elif choice == "3":
            edit_product(product_db)
        elif choice == "4":
            toggle_product(product_db, activate=False)
        elif choice == "5":
            toggle_product(product_db, activate=True)
        elif choice == "6":
            break
        else:
            print("Invalid choice.")


def list_customers(customer_db):
    customers = customer_db.list_customers(limit=20)
    print_table(
        customers,
        [
            ("id", "ID"),
            ("name", "Name"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("company", "Company"),
            ("industry", "Industry"),
            ("status", "Status"),
        ],
        title="\nCustomers (latest 20)",
        max_width=22,
    )


def view_customer(customer_db):
    customer_id = prompt_int("Enter Customer ID: ", None)
    if not customer_id:
        return

    customer = customer_db.get_customer_by_id(customer_id)
    if not customer:
        print("Customer not found.")
        return

    print_kv(
        "\nCustomer Details",
        [
            ("Name", customer["name"]),
            ("Email", customer["email"]),
            ("Phone", customer["phone"]),
            ("Company", customer["company"]),
            ("Industry", customer["industry"]),
            ("Segment", customer["segment"]),
            ("Status", customer["status"]),
            ("Lead Source", customer["lead_source"]),
            ("Address", customer["address_line1"]),
            ("Address 2", customer["address_line2"]),
            ("City", customer["city"]),
            ("State", customer["state"]),
            ("Country", customer["country"]),
            ("Postal Code", customer["postal_code"]),
            ("Last Contact", customer["last_contact_at"]),
            ("Created", customer["created_at"]),
            ("Updated", customer["updated_at"]),
            ("Notes", customer["notes"]),
        ],
    )


def add_customer(customer_db):
    name = prompt_text("Customer name: ", "")
    if not name:
        print("Name is required.")
        return

    email = prompt_text("Email (optional): ", "")
    phone = prompt_text("Phone (optional): ", "")
    company = prompt_text("Company (optional): ", "")
    industry = prompt_text("Industry (optional): ", "")
    segment = prompt_text("Segment (optional): ", "")
    status = prompt_text("Status (Lead/Active/Inactive): ", "")
    lead_source = prompt_text("Lead source (optional): ", "")
    address_line1 = prompt_text("Address line 1 (optional): ", "")
    address_line2 = prompt_text("Address line 2 (optional): ", "")
    city = prompt_text("City (optional): ", "")
    state = prompt_text("State (optional): ", "")
    country = prompt_text("Country (optional): ", "")
    postal_code = prompt_text("Postal code (optional): ", "")
    notes = prompt_text("Notes (optional): ", "")

    customer_db.upsert_customer(
        name=name,
        email=email,
        phone=phone,
        company=company,
        industry=industry,
        segment=segment,
        status=status,
        lead_source=lead_source,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state=state,
        country=country,
        postal_code=postal_code,
        notes=notes,
        last_contact_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    print("Customer saved.")


def search_customers(customer_db):
    query = prompt_text("Search customers (name/email/company): ", "")
    if not query:
        print("Search text is required.")
        return

    results = customer_db.search_customers(query, limit=20)
    print_table(
        results,
        [
            ("id", "ID"),
            ("name", "Name"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("company", "Company"),
            ("industry", "Industry"),
            ("status", "Status"),
        ],
        title="\nCustomer Search Results",
        max_width=22,
    )


def manage_customers(customer_db):
    while True:
        print("\nCustomer Management")
        print("1. List customers")
        print("2. Add customer")
        print("3. Search customers")
        print("4. View customer details")
        print("5. Back")

        choice = input("Choose an option (1-5): ").strip()
        if choice == "1":
            list_customers(customer_db)
        elif choice == "2":
            add_customer(customer_db)
        elif choice == "3":
            search_customers(customer_db)
        elif choice == "4":
            view_customer(customer_db)
        elif choice == "5":
            break
        else:
            print("Invalid choice.")


def add_sale(product_db, customer_db, monitor):
    products = list_products(product_db, active_only=True)
    if not products:
        print("No active products. Add products first.")
        return

    product_id = prompt_int("Select product ID: ", None)
    if not product_id:
        return

    product = product_db.get_product_by_id(product_id)
    if not product or product["active"] == 0:
        print("Invalid product selection.")
        return

    quantity = prompt_float("Quantity (default 1): ", 1.0)
    unit_price = prompt_float(
        "Unit price (press Enter for product price): ", product["price"]
    )
    discount = prompt_float("Discount amount (optional): ", 0.0)
    subtotal = quantity * unit_price
    default_tax = subtotal * Config.DEFAULT_TAX_RATE
    tax = prompt_float("Tax amount (optional): ", default_tax)
    currency = prompt_text("Currency (default USD): ", Config.DEFAULT_CURRENCY)

    total = subtotal - discount + tax

    print("\nSale summary:")
    print(f"- Product: {product['name']}")
    print(f"- Quantity: {quantity}")
    currency_prefix = f"{currency} "
    print(f"- Unit price: {pretty_money(unit_price, currency_prefix)}")
    print(f"- Subtotal: {pretty_money(subtotal, currency_prefix)}")
    print(f"- Discount: {pretty_money(discount, currency_prefix)}")
    print(f"- Tax: {pretty_money(tax, currency_prefix)}")
    print(f"- Total: {pretty_money(total, currency_prefix)}")

    if not prompt_yes_no("Confirm and save sale?", True):
        print("Sale cancelled.")
        return

    customer_name = prompt_text("Customer name: ", "Walk-in Customer")
    customer_email = prompt_text("Customer email (optional): ", "")
    phone = prompt_text("Phone (optional): ", "")
    company = prompt_text("Company (optional): ", "")

    payment_method = prompt_text("Payment method (cash/card/upi/other): ", "")

    add_more = prompt_yes_no("Add more details?", False)
    industry = segment = status = lead_source = ""
    address_line1 = address_line2 = city = state = country = postal_code = ""
    payment_status = Config.DEFAULT_PAYMENT_STATUS
    fulfillment_status = Config.DEFAULT_FULFILLMENT_STATUS
    channel = Config.DEFAULT_CHANNEL
    source = Config.DEFAULT_SOURCE
    region = Config.DEFAULT_REGION
    sales_rep = Config.DEFAULT_SALES_REP
    invoice_id = ""
    tags = ""
    notes = ""

    if add_more:
        industry = prompt_text("Industry (optional): ", "")
        segment = prompt_text("Segment (optional): ", "")
        status = prompt_text("Customer status (Lead/Active/Inactive): ", "")
        lead_source = prompt_text("Lead source (optional): ", "")
        address_line1 = prompt_text("Address line 1 (optional): ", "")
        address_line2 = prompt_text("Address line 2 (optional): ", "")
        city = prompt_text("City (optional): ", "")
        state = prompt_text("State (optional): ", "")
        country = prompt_text("Country (optional): ", "")
        postal_code = prompt_text("Postal code (optional): ", "")
        payment_status = prompt_text(
            f"Payment status (default {Config.DEFAULT_PAYMENT_STATUS}): ",
            Config.DEFAULT_PAYMENT_STATUS,
        )
        fulfillment_status = prompt_text(
            f"Fulfillment status (default {Config.DEFAULT_FULFILLMENT_STATUS}): ",
            Config.DEFAULT_FULFILLMENT_STATUS,
        )
        channel = prompt_text(
            f"Channel (default {Config.DEFAULT_CHANNEL}): ", Config.DEFAULT_CHANNEL
        )
        source = prompt_text(
            f"Source (default {Config.DEFAULT_SOURCE}): ", Config.DEFAULT_SOURCE
        )
        region = prompt_text(
            f"Region (default {Config.DEFAULT_REGION}): ", Config.DEFAULT_REGION
        )
        sales_rep = prompt_text("Sales rep (optional): ", Config.DEFAULT_SALES_REP)
        invoice_id = prompt_text("Invoice ID (optional): ", "")
        tags = prompt_text("Tags (comma separated, optional): ", "")
        notes = prompt_text("Notes (optional): ", "")

    customer_db.upsert_customer(
        name=customer_name,
        email=customer_email,
        phone=phone,
        company=company,
        industry=industry,
        segment=segment,
        status=status,
        lead_source=lead_source,
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state=state,
        country=country,
        postal_code=postal_code,
        notes=notes,
        last_contact_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    monitor.log_sale(
        product=product["name"],
        amount=total,
        customer=customer_name,
        status="Completed",
        customer_email=customer_email,
        quantity=quantity,
        unit_price=unit_price,
        discount=discount,
        tax=tax,
        total=total,
        currency=currency,
        payment_status=payment_status,
        fulfillment_status=fulfillment_status,
        payment_method=payment_method,
        channel=channel,
        source=source,
        region=region,
        sales_rep=sales_rep,
        invoice_id=invoice_id,
        tags=tags,
        notes=notes,
    )
    print("Sale recorded.")


def show_recent_purchases(monitor):
    rows = monitor.db.get_last_purchases(Config.MAX_RECENT_PURCHASES)
    if not rows:
        print("\nNo purchases stored yet.")
        return

    display = []
    for row in rows:
        display.append(
            {
                "timestamp": row["timestamp"],
                "customer": row["customer"],
                "email": row["customer_email"],
                "product": row["product"],
                "qty": row["quantity"],
                "currency": row["currency"],
                "total": pretty_money(row["total"], f"{row['currency']} "),
                "status": row["status"],
                "payment": row["payment_status"],
            }
        )

    print_table(
        display,
        [
            ("timestamp", "Time"),
            ("customer", "Customer"),
            ("email", "Email"),
            ("product", "Product"),
            ("qty", "Qty"),
            ("currency", "Cur"),
            ("total", "Total"),
            ("status", "Status"),
            ("payment", "Payment"),
        ],
        title=f"\nLast {Config.MAX_RECENT_PURCHASES} Purchases",
        max_width=18,
    )


def search_purchases(monitor):
    query = prompt_text("Search text (customer/product/notes): ", "")
    days = prompt_int("Last N days (optional): ", None)

    rows = monitor.db.search_purchases(query=query, days=days, limit=50)
    if not rows:
        print("No matching purchases.")
        return

    display = []
    for row in rows:
        display.append(
            {
                "timestamp": row["timestamp"],
                "customer": row["customer"],
                "email": row["customer_email"],
                "product": row["product"],
                "qty": row["quantity"],
                "currency": row["currency"],
                "total": pretty_money(row["total"], f"{row['currency']} "),
                "payment": row["payment_status"],
            }
        )

    print_table(
        display,
        [
            ("timestamp", "Time"),
            ("customer", "Customer"),
            ("email", "Email"),
            ("product", "Product"),
            ("qty", "Qty"),
            ("currency", "Cur"),
            ("total", "Total"),
            ("payment", "Payment"),
        ],
        title="\nPurchase Search Results",
        max_width=18,
    )


def export_purchases(monitor):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_path = Config.EXPORTS_DIR / f"purchases_{timestamp}.csv"
    path_text = prompt_text(f"Export path [{default_path}]: ", str(default_path))
    export_path = Path(path_text)

    if monitor.db.export_purchases_csv(export_path):
        print(f"Exported to {export_path}")
    else:
        print("No purchases to export.")


def backup_database(monitor):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_path = Config.BACKUPS_DIR / f"purchases_{timestamp}.db"
    path_text = prompt_text(f"Backup path [{default_path}]: ", str(default_path))
    backup_path = Path(path_text)

    monitor.db.backup_db(backup_path)
    print(f"Backup saved to {backup_path}")


def main():
    logger.info("Application started")
    warnings = validate_config()
    if warnings:
        print("\nConfiguration warnings:")
        for w in warnings:
            print(f"- {w}")
        print("")

    product_db = ProductDB()
    customer_db = CustomerDB()
    monitor = SalesMonitor()

    print(f"{Config.APP_NAME} v{Config.APP_VERSION}")

    while True:
        print("\n" + "=" * 60)
        print("SALES AND MONITORING - MENU")
        print("=" * 60)
        print("1. Add a sale")
        print("2. View last purchases")
        print("3. Search purchases")
        print("4. Daily sales report")
        print("5. Export purchases to CSV")
        print("6. Backup database")
        print("7. Manage products")
        print("8. Manage customers")
        print("9. Exit")

        choice = input("Choose an option (1-9): ").strip()
        if choice == "1":
            add_sale(product_db, customer_db, monitor)
        elif choice == "2":
            show_recent_purchases(monitor)
        elif choice == "3":
            search_purchases(monitor)
        elif choice == "4":
            monitor.generate_daily_report()
        elif choice == "5":
            export_purchases(monitor)
        elif choice == "6":
            backup_database(monitor)
        elif choice == "7":
            manage_products(product_db)
        elif choice == "8":
            manage_customers(customer_db)
        elif choice == "9":
            print("Goodbye.")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
