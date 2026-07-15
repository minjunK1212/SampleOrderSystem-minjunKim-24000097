from dataclasses import dataclass


def validate_production_queue_fields(required_quantity, production_quantity, queue_position):
    for field_name, value in (
        ("required_quantity", required_quantity),
        ("production_quantity", production_quantity),
        ("queue_position", queue_position),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{field_name}는 1 이상의 정수여야 합니다.")


@dataclass(frozen=True)
class ProductionQueueItem:
    order_id: str
    sample_id: str
    required_quantity: int
    production_quantity: int
    queue_position: int

    def __post_init__(self):
        validate_production_queue_fields(
            self.required_quantity, self.production_quantity, self.queue_position
        )

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "sample_id": self.sample_id,
            "required_quantity": self.required_quantity,
            "production_quantity": self.production_quantity,
            "queue_position": self.queue_position,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            order_id=data["order_id"],
            sample_id=data["sample_id"],
            required_quantity=data["required_quantity"],
            production_quantity=data["production_quantity"],
            queue_position=data["queue_position"],
        )
