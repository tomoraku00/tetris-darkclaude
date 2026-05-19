"""日付範囲クラス"""
from datetime import date


class DateRange:
    def __init__(self, start: date, end: date):
        if start > end:
            raise ValueError(f"start ({start}) must be <= end ({end})")
        self.start = start
        self.end = end

    def _is_valid_date(self, d: date) -> bool:
        # バグ: end を排他的に扱っているため、end 当日が範囲外になる
        return self.start <= d < self.end

    def contains(self, d: date) -> bool:
        return self._is_valid_date(d)

    def overlaps(self, other: "DateRange") -> bool:
        return self.start <= other.end and other.start <= self.end

    def duration_days(self) -> int:
        return (self.end - self.start).days

    def clamp(self, d: date) -> date:
        if d < self.start:
            return self.start
        if not self._is_valid_date(d):
            return self.end
        return d

    def to_dict(self) -> dict:
        return {"start": self.start.isoformat(), "end": self.end.isoformat()}
