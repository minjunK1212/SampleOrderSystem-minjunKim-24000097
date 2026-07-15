import dataclasses
import json
import math
import os
import re
import tempfile
from pathlib import Path

from sample_order_system.model.order import Order, OrderStatus
from sample_order_system.model.production_queue import ProductionQueueItem
from sample_order_system.model.sample import Sample

_ORDER_ID_PATTERN = re.compile(r"^ORD-(\d+)$")


def _format_order_id(n: int) -> str:
    return f"ORD-{n:04d}"


class OrderSystemDataError(Exception):
    """저장된 JSON 파일을 읽을 수 없을 때 발생한다(문법 오류 등)."""


class OrderSystemRepository:
    """통합 JSON({"samples", "orders", "production_queue"})을 다루는 리포지토리."""

    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self._samples = {}
        self._orders = {}
        self._production_queue = []
        self._load()

    def _load(self):
        if not self.data_path.exists() or self.data_path.stat().st_size == 0:
            self._samples = {}
            self._orders = {}
            self._production_queue = []
            return

        try:
            raw = json.loads(self.data_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise OrderSystemDataError(f"JSON 문법이 잘못되었습니다: {self.data_path} (사유: {e})") from e

        samples_raw = raw.get("samples", [])
        self._samples = {item["sample_id"]: Sample.from_dict(item) for item in samples_raw}
        orders_raw = raw.get("orders", [])
        self._orders = {item["order_id"]: Order.from_dict(item) for item in orders_raw}
        queue_raw = raw.get("production_queue", [])
        self._production_queue = sorted(
            (ProductionQueueItem.from_dict(item) for item in queue_raw), key=lambda i: i.queue_position
        )

    def _next_order_id(self):
        max_n = 0
        for order_id in self._orders:
            match = _ORDER_ID_PATTERN.match(order_id)
            if match:
                max_n = max(max_n, int(match.group(1)))
        return _format_order_id(max_n + 1)

    def _next_queue_position(self):
        if not self._production_queue:
            return 1
        return max(item.queue_position for item in self._production_queue) + 1

    def _save(self):
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "samples": [sample.to_dict() for sample in self._samples.values()],
            "orders": [order.to_dict() for order in self._orders.values()],
            "production_queue": [item.to_dict() for item in self._production_queue],
        }
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{self.data_path.name}.", suffix=".tmp", dir=str(self.data_path.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp_name, self.data_path)
        except BaseException:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def _find_sample_by_name(self, name):
        return next((s for s in self._samples.values() if s.name == name), None)

    def register_sample(self, sample: Sample) -> Sample:
        if sample.sample_id in self._samples:
            raise ValueError(f"이미 존재하는 시료 ID입니다: {sample.sample_id}")
        if self._find_sample_by_name(sample.name) is not None:
            raise ValueError(f"이미 존재하는 시료 이름입니다: {sample.name}")
        self._samples[sample.sample_id] = sample
        self._save()
        return sample

    def get_sample(self, sample_id):
        return self._samples.get(sample_id)

    def list_samples(self):
        return list(self._samples.values())

    def search_samples_by_name(self, keyword):
        keyword_lower = keyword.lower()
        return [s for s in self._samples.values() if keyword_lower in s.name.lower()]

    def reserve_order(self, sample_id, customer_name, quantity) -> Order:
        if sample_id not in self._samples:
            raise ValueError(f"존재하지 않는 시료 ID입니다: {sample_id}")
        order = Order(
            order_id=self._next_order_id(),
            sample_id=sample_id,
            customer_name=customer_name,
            quantity=quantity,
        )
        self._orders[order.order_id] = order
        self._save()
        return order

    def get_order(self, order_id):
        return self._orders.get(order_id)

    def list_orders(self):
        return list(self._orders.values())

    def list_orders_by_status(self, status: OrderStatus):
        return [order for order in self._orders.values() if order.status == status]

    def reject_order(self, order_id) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise ValueError(f"존재하지 않는 주문입니다: {order_id}")
        if order.status != OrderStatus.RESERVED:
            raise ValueError(
                f"RESERVED 상태의 주문만 거절할 수 있습니다: {order_id} (현재 상태: {order.status.value})"
            )
        rejected = dataclasses.replace(order, status=OrderStatus.REJECTED)
        self._orders[order_id] = rejected
        self._save()
        return rejected

    def approve_order(self, order_id) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise ValueError(f"존재하지 않는 주문입니다: {order_id}")
        if order.status != OrderStatus.RESERVED:
            raise ValueError(
                f"RESERVED 상태의 주문만 승인할 수 있습니다: {order_id} (현재 상태: {order.status.value})"
            )
        sample = self._samples.get(order.sample_id)
        if sample is None:
            raise ValueError(f"주문이 참조하는 시료를 찾을 수 없습니다: {order.sample_id}")
        if sample.inventory < order.quantity:
            required_quantity = max(order.quantity - sample.inventory, 1)
            production_quantity = math.ceil(required_quantity / sample.yield_rate)
            queue_item = ProductionQueueItem(
                order_id=order.order_id,
                sample_id=order.sample_id,
                required_quantity=required_quantity,
                production_quantity=production_quantity,
                queue_position=self._next_queue_position(),
            )
            self._production_queue.append(queue_item)
            producing = dataclasses.replace(order, status=OrderStatus.PRODUCING)
            self._orders[order_id] = producing
            self._save()
            return producing

        confirmed = dataclasses.replace(order, status=OrderStatus.CONFIRMED)
        self._orders[order_id] = confirmed
        self._save()
        return confirmed

    def list_production_queue(self):
        return list(self._production_queue)

    def release_order(self, order_id) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise ValueError(f"존재하지 않는 주문입니다: {order_id}")
        if order.status != OrderStatus.CONFIRMED:
            raise ValueError(
                f"CONFIRMED 상태의 주문만 출고할 수 있습니다: {order_id} (현재 상태: {order.status.value})"
            )
        sample = self._samples[order.sample_id]
        updated_sample = dataclasses.replace(sample, inventory=sample.inventory - order.quantity)
        self._samples[sample.sample_id] = updated_sample

        released = dataclasses.replace(order, status=OrderStatus.RELEASE)
        self._orders[order_id] = released
        self._save()
        return released

    def get_current_production_job(self):
        return self._production_queue[0] if self._production_queue else None

    def complete_current_production(self) -> Order:
        if not self._production_queue:
            raise ValueError("현재 진행 중인 생산 작업이 없습니다.")

        current = self._production_queue[0]
        sample = self._samples[current.sample_id]
        order = self._orders[current.order_id]

        updated_sample = dataclasses.replace(sample, inventory=sample.inventory + current.production_quantity)
        self._samples[sample.sample_id] = updated_sample

        confirmed_order = dataclasses.replace(order, status=OrderStatus.CONFIRMED)
        self._orders[order.order_id] = confirmed_order

        self._production_queue.pop(0)
        self._save()
        return confirmed_order
