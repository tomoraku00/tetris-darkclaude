"""日付パース関数 (リファクタリング前の可読性が低いバージョン)"""
import re
from datetime import datetime


def parse_date(date_str):
    date_str = date_str.strip()
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return datetime.strptime(date_str[:10], '%Y-%m-%d').date()
    elif re.match(r'\d{2}/\d{2}/\d{4}', date_str):
        return datetime.strptime(date_str[:10], '%m/%d/%Y').date()
    elif re.match(r'\d{2}\.\d{2}\.\d{4}', date_str):
        return datetime.strptime(date_str[:10], '%d.%m.%Y').date()
    else:
        raise ValueError(f"Unknown date format: {date_str}")
