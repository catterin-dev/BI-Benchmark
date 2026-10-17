import argparse, csv, time
from pathlib import Path
from db import reset_db, upsert_events

def read_events(path):
    with open(path,newline="",encoding="utf-8") as f:
        return [{"event_id":int(r["event_id"]),"event_time":r["event_time"],"category":r["category"],
                 "campus":r["campus"],"amount":float(r["amount"])} for r in csv.DictReader(f)]

def run_lambda(events, db):
    # Prototipo de dos rutas: lote histórico + ventana incremental reciente.
    split=max(1,int(len(events)*0.8))
    upsert_events(events[:split],db); upsert_events(events[split:],db)
    upsert_events(events[-min(100,len(events)):],db)  # reconciliación idempotente por clave

def run_kappa(events, db):
    # Prototipo de ruta única de eventos, procesados en bloques.
    for start in range(0,len(events),500): upsert_events(events[start:start+500],db)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--input",default="data/events.csv")
    p.add_argument("--runs",type=int,default=5); p.add_argument("--output",default="results/ingest_benchmark.csv")
    p.add_argument("--db",default="data/bi_events.sqlite"); a=p.parse_args()
    events=read_events(a.input); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); rows=[]
    for name,fn in [("Lambda_simplificada",run_lambda),("Kappa_simplificada",run_kappa)]:
        for run in range(1,a.runs+1):
            reset_db(a.db); t=time.perf_counter(); fn(events,a.db); elapsed=time.perf_counter()-t
            row={"architecture":name,"run":run,"records":len(events),"elapsed_seconds":round(elapsed,6),
                 "records_per_second":round(len(events)/elapsed,2)}
            rows.append(row); print(row)
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print("Guardado:",out)
if __name__=="__main__": main()
