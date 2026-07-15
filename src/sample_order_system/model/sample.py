from dataclasses import dataclass


def validate_sample_fields(sample_id, name, average_production_time, yield_rate, inventory):
    if not sample_id or not sample_id.strip():
        raise ValueError("sample_id는 빈 문자열일 수 없습니다.")
    if not name or not name.strip():
        raise ValueError("name은 빈 문자열일 수 없습니다.")
    if average_production_time <= 0:
        raise ValueError("average_production_time은 0보다 커야 합니다.")
    if not (0 < yield_rate <= 1):
        raise ValueError("yield_rate는 0보다 크고 1 이하여야 합니다.")
    if isinstance(inventory, bool) or not isinstance(inventory, int) or inventory < 0:
        raise ValueError("inventory는 0 이상의 정수여야 합니다.")


@dataclass(frozen=True)
class Sample:
    sample_id: str
    name: str
    average_production_time: float
    yield_rate: float
    inventory: int

    def __post_init__(self):
        validate_sample_fields(
            self.sample_id, self.name, self.average_production_time, self.yield_rate, self.inventory
        )

    def to_dict(self):
        return {
            "sample_id": self.sample_id,
            "name": self.name,
            "average_production_time": self.average_production_time,
            "yield_rate": self.yield_rate,
            "inventory": self.inventory,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            sample_id=data["sample_id"],
            name=data["name"],
            average_production_time=data["average_production_time"],
            yield_rate=data["yield_rate"],
            inventory=data["inventory"],
        )
