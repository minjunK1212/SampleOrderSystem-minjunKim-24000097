from dataclasses import dataclass, field
from enum import Enum


class OrderStatus(str, Enum):
    RESERVED = "RESERVED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE = "RELEASE"
    REJECTED = "REJECTED"


def validate_order_fields(customer_name, quantity):
    if not customer_name or not customer_name.strip():
        raise ValueError("customer_name은 빈 문자열일 수 없습니다.")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
        raise ValueError("quantity는 1 이상의 정수여야 합니다.")


@dataclass(frozen=True)
class Order:
    order_id: str
    sample_id: str
    customer_name: str
    quantity: int
    status: OrderStatus = field(default=OrderStatus.RESERVED)

    def __post_init__(self):
        validate_order_fields(self.customer_name, self.quantity)

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "sample_id": self.sample_id,
            "customer_name": self.customer_name,
            "quantity": self.quantity,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            order_id=data["order_id"],
            sample_id=data["sample_id"],
            customer_name=data["customer_name"],
            quantity=data["quantity"],
            status=OrderStatus(data["status"]),
        )
