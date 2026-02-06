import os
import csv
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Central configuration."""

    # App
    APP_NAME = os.getenv("APP_NAME", "AI Sales")
    APP_VERSION = os.getenv("APP_VERSION", "1.2.0")

    # Company
    COMPANY_NAME = os.getenv("COMPANY_NAME", "Your Company")
    COMPANY_EMAIL = os.getenv("COMPANY_EMAIL_ID", "sales@yourcompany.com")
    ALERT_EMAIL = os.getenv("ALERT_EMAIL", "manager@yourcompany.com")

    # Storage
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    EXPORTS_DIR = DATA_DIR / "exports"
    BACKUPS_DIR = DATA_DIR / "backups"
    PRODUCTS_FILE = DATA_DIR / "products.csv"
    SALES_LOG_FILE = DATA_DIR / "sales_log.csv"
    INTERACTIONS_FILE = DATA_DIR / "interactions.csv"
    PURCHASES_DB = DATA_DIR / "purchases.db"

    # LLM
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none").lower()
    API_KEY = os.getenv("API_KEY", "")
    LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "600"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE = LOGS_DIR / "app.log"

    # Database
    DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "5"))
    MAX_RECENT_PURCHASES = int(os.getenv("MAX_RECENT_PURCHASES", "10"))

    # Defaults
    DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")
    DEFAULT_TAX_RATE = float(os.getenv("DEFAULT_TAX_RATE", "0.0"))
    DEFAULT_PAYMENT_STATUS = os.getenv("DEFAULT_PAYMENT_STATUS", "Paid")
    DEFAULT_PAYMENT_TERMS = os.getenv("DEFAULT_PAYMENT_TERMS", "Net 30")
    DEFAULT_FULFILLMENT_STATUS = os.getenv(
        "DEFAULT_FULFILLMENT_STATUS", "Delivered"
    )
    DEFAULT_CHANNEL = os.getenv("DEFAULT_CHANNEL", "in-store")
    DEFAULT_SOURCE = os.getenv("DEFAULT_SOURCE", "direct")
    DEFAULT_REGION = os.getenv("DEFAULT_REGION", "local")
    DEFAULT_SALES_REP = os.getenv("DEFAULT_SALES_REP", "")

    # Monitoring thresholds
    DAILY_SALES_TARGET = int(os.getenv("DAILY_SALES_TARGET", "10"))
    LOW_SALES_THRESHOLD = int(os.getenv("LOW_SALES_THRESHOLD", "5"))
    RESPONSE_TIME_TARGET_HOURS = int(os.getenv("RESPONSE_TIME_TARGET_HOURS", "2"))


def ensure_data_files():
    """Create folders and sample CSV files if missing."""
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    Config.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    Config.BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

    if not Config.PRODUCTS_FILE.exists():
        rows = [
            {
                "name": "CRM Pro",
                "price": "99",
                "features": "Contact management, email tracking, basic reporting",
                "best_for": "Small teams",
            },
            {
                "name": "Analytics Suite",
                "price": "149",
                "features": "Dashboards, predictive insights, custom reports",
                "best_for": "Data teams",
            },
            {
                "name": "Marketing Tool",
                "price": "79",
                "features": "Email campaigns, social scheduling, A/B testing",
                "best_for": "Marketing teams",
            },
        ]
        with open(Config.PRODUCTS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "price", "features", "best_for"])
            writer.writeheader()
            writer.writerows(rows)

    if not Config.SALES_LOG_FILE.exists():
        sample_products = [
            ("CRM Pro", 99),
            ("Analytics Suite", 149),
            ("Marketing Tool", 79),
        ]
        today = datetime.now().date()
        rows = []
        for i in range(7):
            product, amount = sample_products[i % len(sample_products)]
            rows.append(
                {
                    "date": (today - timedelta(days=i)).isoformat(),
                    "product": product,
                    "amount": str(amount),
                    "customer": f"Sample Customer {i + 1}",
                    "status": "Completed",
                }
            )
        with open(Config.SALES_LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["date", "product", "amount", "customer", "status"]
            )
            writer.writeheader()
            writer.writerows(rows)

    if not Config.INTERACTIONS_FILE.exists():
        with open(Config.INTERACTIONS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["timestamp", "customer", "question", "response", "status"]
            )
            writer.writeheader()


def validate_config():
    warnings = []

    if Config.LLM_PROVIDER not in ("none", "openai_compatible"):
        warnings.append(
            f"Unknown LLM_PROVIDER='{Config.LLM_PROVIDER}'. Use 'none' or 'openai_compatible'."
        )

    if Config.MAX_TOKENS <= 0:
        warnings.append("MAX_TOKENS must be greater than 0.")

    if Config.TEMPERATURE < 0 or Config.TEMPERATURE > 1:
        warnings.append("TEMPERATURE should be between 0 and 1.")

    if Config.DAILY_SALES_TARGET < 0:
        warnings.append("DAILY_SALES_TARGET should be 0 or higher.")

    if Config.LOW_SALES_THRESHOLD < 0:
        warnings.append("LOW_SALES_THRESHOLD should be 0 or higher.")

    if Config.DB_TIMEOUT <= 0:
        warnings.append("DB_TIMEOUT should be greater than 0.")

    if Config.MAX_RECENT_PURCHASES <= 0:
        warnings.append("MAX_RECENT_PURCHASES should be greater than 0.")

    if Config.DEFAULT_TAX_RATE < 0 or Config.DEFAULT_TAX_RATE > 1:
        warnings.append("DEFAULT_TAX_RATE should be between 0 and 1.")

    if not Config.DEFAULT_CURRENCY:
        warnings.append("DEFAULT_CURRENCY should not be empty.")

    return warnings
