import pandas as pd
import src.config as config

def date_range(csv_path=config.EVENTS_CSV):
    ts = pd.read_csv(csv_path, usecols=["timestamp"])["timestamp"]
    lo = pd.to_datetime(ts.min(), unit="ms", utc=True)
    hi = pd.to_datetime(ts.max(), unit="ms", utc=True)
    return lo, hi

def period_bounds(period):
    # timestamp retail rocket dalam milidetik, batas akhir dibuat eksklusif
    start = pd.Timestamp(period[0], tz="UTC")
    end = pd.Timestamp(period[1], tz="UTC") + pd.Timedelta(days=1)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)

def filter_csv(src, dst, period, chunksize=500_000):
    lo, hi = period_bounds(period)
    total = 0
    first = True
    for chunk in pd.read_csv(src, chunksize=chunksize):
        part = chunk[(chunk["timestamp"] >= lo) & (chunk["timestamp"] < hi)]
        part.to_csv(dst, mode="w" if first else "a", header=first, index=False)
        first = False
        total += len(part)
    return total

def build_periods(src=config.EVENTS_CSV):
    config.DATA_DIR.mkdir(exist_ok=True)
    n1 = filter_csv(src, config.P1_CSV, config.P1)
    n2 = filter_csv(src, config.P2_CSV, config.P2)
    return {"P1": n1, "P2": n2}

def summary(csv_path):
    df = pd.read_csv(csv_path)
    return {
        "rows": len(df),
        "visitors": df["visitorid"].nunique(),
        "items": df["itemid"].nunique(),
        "events": df["event"].value_counts().to_dict(),
    }