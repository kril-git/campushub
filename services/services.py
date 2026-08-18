from datetime import datetime


def get_timestamp() -> str:
    now = datetime.now()
    ts = now.timestamp()
    ts_int = int(ts)
    return str(ts)
