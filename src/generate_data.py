import argparse, csv, random
from datetime import datetime, timedelta, timezone
from pathlib import Path

def generate(rows, output, seed=42):
    random.seed(seed)
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    categories = ["matricula", "constancia", "certificado", "record", "solicitud"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["event_id","event_time","category","campus","amount"])
        w.writeheader()
        for i in range(1, rows+1):
            w.writerow({"event_id":i,"event_time":(start+timedelta(seconds=i*7)).isoformat(),
                "category":random.choice(categories),"campus":random.choice(["Chupa","Puno","Juliaca"]),
                "amount":round(random.uniform(1,500),2)})
    print(f"Generados {rows} eventos sintéticos en {path}")

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--rows",type=int,default=10000)
    p.add_argument("--output",default="data/events.csv"); p.add_argument("--seed",type=int,default=42)
    a=p.parse_args(); generate(a.rows,a.output,a.seed)
