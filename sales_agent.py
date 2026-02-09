import csv
from datetime import datetime
from config import Config, ensure_data_files
from llm_client import LLMClient
from db import ProductDB
from logger import get_logger

logger = get_logger(__name__)


class SalesAgent:
    """Simple sales assistant with optional LLM support."""

    def __init__(self):
        ensure_data_files()
        self.product_db = ProductDB()
        self.products = self._load_products()
        self.llm = LLMClient()

    def _load_products(self):
        try:
            products = self.product_db.list_products(active_only=True)
            if products:
                # Normalize keys to match the existing format
                return [
                    {
                        "name": p["name"],
                        "price": p["price"],
                        "features": p["features"],
                        "best_for": p["best_for"],
                    }
                    for p in products
                ]
        except Exception as exc:
            logger.warning("Failed to load products from DB: %s", exc)

        try:
            with open(Config.PRODUCTS_FILE, newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except FileNotFoundError:
            logger.warning("Products file missing. Recreating sample products.")
            ensure_data_files()
            with open(Config.PRODUCTS_FILE, newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))

    def _parse_price(self, value):
        try:
            return float(value)
        except ValueError:
            return 0.0

    def _choose_product(self, question):
        q = question.lower()
        best = None
        best_score = -1
        for product in self.products:
            text = f"{product['name']} {product['features']} {product['best_for']}".lower()
            score = sum(1 for w in q.split() if w in text)
            if score > best_score:
                best_score = score
                best = product

        if best is None and self.products:
            best = self.products[0]

        if best_score <= 0 and self.products:
            best = min(self.products, key=lambda p: self._parse_price(p["price"]))

        return best

    def _build_product_context(self):
        lines = []
        for p in self.products:
            lines.append(
                f"- {p['name']} (${p['price']}): {p['features']} (Best for: {p['best_for']})"
            )
        return "\n".join(lines)

    def _call_llm(self, system_prompt, user_prompt):
        return self.llm.complete(system_prompt, user_prompt)

    def _fallback_response(self, question, customer_name):
        product = self._choose_product(question)
        if product is None:
            return (
                f"Hi {customer_name}, thanks for the question ... "
                f"Could you share your team size, budget, and timeline? "
                f"You can also reach us at {Config.COMPANY_EMAIL}."
            )

        name = product["name"]
        price = product["price"]
        features = product["features"]
        return (
            f"Hi {customer_name}, based on what you shared, {name} could be a good fit. "
            f"It is ${price} and includes {features}. "
            "A couple quick questions to help me to guide you: "
            "What is your budget, how many users, and when do you want to start? "
            "If you want, I can set up a short demo or send more details. "
            f"You can also reach us at {Config.COMPANY_EMAIL}."
        )

    def handle_customer_inquiry(self, customer_question, customer_name="Customer"):
        if not customer_question.strip():
            return "Please provide a question so I can help."

        product_context = self._build_product_context()

        system_prompt = (
            f"You are a professional sales assistant for {Config.COMPANY_NAME}.\n"
            "Your responsibilities:\n"
            "1. Answer customer questions accurately\n"
            "2. Recommend products based on needs\n"
            "3. Ask clarifying questions when needed\n"
            "4. Never invent features or prices\n"
            "5. End with a clear next step\n\n"
            f"Available products:\n{product_context}"
        )

        user_prompt = (
            f"Customer name: {customer_name}\n"
            f"Question: {customer_question}"
        )

        response = self._call_llm(system_prompt, user_prompt)
        if not response:
            response = self._fallback_response(customer_question, customer_name)

        self.log_interaction(customer_name, customer_question, response)
        return response

    def log_interaction(self, customer_name, question, response):
        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "customer": customer_name,
            "question": question,
            "response": response,
            "status": "Completed",
        }

        try:
            with open(Config.INTERACTIONS_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "timestamp",
                        "customer",
                        "question",
                        "response",
                        "status",
                    ],
                )
                writer.writerow(row)
        except Exception as exc:
            logger.error("Failed to write interaction: %s", exc)
