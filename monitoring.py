from datetime import date
from config import Config
from db import PurchaseDB
from llm_client import LLMClient
from logger import get_logger
from ui import pretty_money

logger = get_logger(__name__)


class SalesMonitor:
    """Sales monitoring and alerts."""

    def __init__(self):
        self.llm = LLMClient()
        self.db = PurchaseDB()

    def log_sale(
        self,
        product,
        amount,
        customer,
        status="Completed",
        customer_email="",
        quantity=1,
        unit_price=None,
        discount=0.0,
        tax=0.0,
        total=None,
        currency=None,
        payment_status="",
        payment_terms="",
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
            self.db.add_purchase(
                customer=customer,
                product=product,
                amount=amount,
                status=status,
                customer_email=customer_email,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount,
                tax=tax,
                total=total,
                currency=currency,
                payment_status=payment_status,
                payment_terms=payment_terms,
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
        except Exception as exc:
            logger.error("Failed to log sale: %s", exc)

    def check_alerts(self, today_count):
        alerts = []
        if today_count == 0:
            alerts.append("No sales recorded today")
        if today_count < Config.LOW_SALES_THRESHOLD:
            alerts.append(
                f"Sales below threshold: {today_count} < {Config.LOW_SALES_THRESHOLD}"
            )
        return alerts

    def _call_llm(self, system_prompt, user_prompt):
        return self.llm.complete(system_prompt, user_prompt)

    def generate_daily_report(self):
        today_label = date.today().isoformat()
        summary = self.db.get_daily_summary(today_label)
        trend = self.db.get_sales_trend(days=7)
        top_products = self.db.get_top_products(days=7, limit=3)

        count = summary["count"]
        revenue = summary["revenue"]
        avg = summary["avg"]

        print("\n" + "=" * 60)
        print(f"DAILY SALES REPORT - {today_label}")
        print("=" * 60)
        currency_prefix = f"{Config.DEFAULT_CURRENCY} "
        print(f"Sales count: {count}")
        print(f"Revenue: {pretty_money(revenue, currency_prefix)}")
        print(f"Average deal: {pretty_money(avg, currency_prefix)}")

        alerts = self.check_alerts(count)
        print("\nAlerts:")
        if alerts:
            for alert in alerts:
                print(f"- {alert}")
        else:
            print("- None")

        if top_products:
            print("\nTop products (7 days):")
            for p in top_products:
                print(
                    f"- {p['product']} | Orders: {p['count']} | Revenue: {pretty_money(p['revenue'], currency_prefix)}"
                )

        if trend:
            print("\n7-day revenue trend:")
            for row in trend:
                print(f"- {row['date']}: {pretty_money(row['revenue'], currency_prefix)}")

        summary_text = (
            f"Sales count: {count}\n"
            f"Revenue: {revenue:.2f}\n"
            f"Average deal: {avg:.2f}\n"
            f"Target: {Config.DAILY_SALES_TARGET}\n"
            f"Top products: {[p['product'] for p in top_products]}"
        )

        system_prompt = (
            "You are a sales analytics assistant. Provide a short summary with "
            "trends and 1-2 recommendations."
        )

        ai_summary = self._call_llm(system_prompt, summary_text)
        print("\nSummary:")
        if ai_summary:
            print(ai_summary)
        else:
            if count < Config.DAILY_SALES_TARGET:
                print("Sales are below target. Consider follow-ups on warm leads.")
            else:
                print("Sales are on track. Keep momentum with demos and follow-ups.")
        print("=" * 60 + "\n")
