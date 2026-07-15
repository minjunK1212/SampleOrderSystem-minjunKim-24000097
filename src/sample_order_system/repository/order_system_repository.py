import json
import os
import tempfile
from pathlib import Path

from sample_order_system.model.sample import Sample


class OrderSystemRepository:
    """통합 JSON({"samples", "orders", "production_queue"})을 다루는 리포지토리.

    Cycle 1에서는 samples 관련 메서드만 구현한다. orders/production_queue는
    로드한 그대로(빈 리스트 포함) 보존만 하고 조작하지 않는다.
    """

    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self._samples = {}
        self._orders_raw = []
        self._production_queue_raw = []
        self._load()

    def _load(self):
        if not self.data_path.exists() or self.data_path.stat().st_size == 0:
            self._samples = {}
            self._orders_raw = []
            self._production_queue_raw = []
            return

        raw = json.loads(self.data_path.read_text(encoding="utf-8"))
        samples_raw = raw.get("samples", [])
        self._samples = {item["sample_id"]: Sample.from_dict(item) for item in samples_raw}
        self._orders_raw = raw.get("orders", [])
        self._production_queue_raw = raw.get("production_queue", [])

    def _save(self):
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "samples": [sample.to_dict() for sample in self._samples.values()],
            "orders": self._orders_raw,
            "production_queue": self._production_queue_raw,
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
