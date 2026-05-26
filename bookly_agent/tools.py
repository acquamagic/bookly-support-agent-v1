from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_name: str
    email: str
    status: str
    eta: str
    item: str
    delivered_on: str | None
    returnable: bool


ORDERS: dict[str, Order] = {
    "BLY-1001": Order(
        order_id="BLY-1001",
        customer_name="Maya Chen",
        email="maya@example.com",
        status="In transit",
        eta="May 28, 2026",
        item="Tomorrow, and Tomorrow, and Tomorrow",
        delivered_on=None,
        returnable=False,
    ),
    "BLY-1002": Order(
        order_id="BLY-1002",
        customer_name="Jordan Lee",
        email="jordan@example.com",
        status="Delivered",
        eta=None,
        item="Project Hail Mary",
        delivered_on="May 22, 2026",
        returnable=True,
    ),
    "BLY-1003": Order(
        order_id="BLY-1003",
        customer_name="Avery Patel",
        email="avery@example.com",
        status="Processing",
        eta="Ships by May 27, 2026",
        item="The Design of Everyday Things",
        delivered_on=None,
        returnable=False,
    ),
}


POLICIES = {
    "shipping": (
        "Standard shipping takes 3-5 business days after fulfillment. "
        "Expedited shipping is available before an order ships. "
        "Overnight air shipping is available for orders placed before 1 PM local time — "
        "your book will be delivered the next business day via air courier. "
        "Overnight shipping is not available for P.O. boxes or APO/FPO addresses."
    ),
    "overnight": (
        "Bookly offers overnight air shipping for orders placed before 1 PM local time. "
        "Your book will be delivered the next business day via air courier. "
        "Overnight shipping costs $24.99 and is available to most US addresses. "
        "Not available for P.O. boxes or APO/FPO addresses. "
        "Orders placed after 1 PM or on weekends ship the following business day."
    ),
    "returns": (
        "Bookly accepts returns for most delivered books within 30 days. "
        "Final-sale items and damaged-by-customer items are not eligible."
    ),
    "refunds": (
        "Refunds are issued to the original payment method after the return is scanned by the carrier. "
        "Most refunds post within 5-7 business days."
    ),
    "password": (
        "Customers can reset their password from the sign-in page. "
        "A reset email is valid for 30 minutes."
    ),
}


def lookup_order(order_id: str) -> dict[str, Any]:
    """Mock order-management lookup."""
    order = ORDERS.get(order_id.upper())
    if not order:
        return {"found": False, "order_id": order_id.upper()}
    return {"found": True, **order.__dict__}


def create_return(order_id: str, reason: str) -> dict[str, Any]:
    """Mock return creation in a support system."""
    order = ORDERS.get(order_id.upper())
    if not order:
        return {"created": False, "reason": "order_not_found", "order_id": order_id.upper()}
    if not order.returnable:
        return {
            "created": False,
            "reason": "not_eligible",
            "order_id": order.order_id,
            "status": order.status,
        }
    return {
        "created": True,
        "return_id": f"RET-{date.today().strftime('%m%d')}-{order.order_id[-4:]}",
        "order_id": order.order_id,
        "label_status": "emailed",
        "reason": reason,
    }


def search_policy(topic: str) -> dict[str, Any]:
    """Mock knowledge-base retrieval."""
    normalized = topic.lower()
    for key, answer in POLICIES.items():
        if key in normalized:
            return {"topic": key, "answer": answer, "confidence": "high"}
    return {
        "topic": "general",
        "answer": (
            "I found general support guidance, but I need a more specific topic like shipping, "
            "overnight shipping, returns, refunds, or password reset to answer accurately."
        ),
        "confidence": "low",
    }

