import argparse,csv,time,statistics
from pathlib import Path
import requests

def percentile(values,p):
    s=sorted(values); return s[min(len(s)-1,max(0,round((p/100)*(len(s)-1))))] if s else None

def summarize(name,times,errors,n,total):
    return {"api":name,"requests":n,"errors":errors,"error_rate_pct":round(errors/n*100,2),
      "mean_latency_ms":round(statistics.mean(times),3),"median_latency_ms":round(statistics.median(times),3),
      "p95_latency_ms":round(percentile(times,95),3),"throughput_success_req_s":round((n-errors)/total,2),
      "total_seconds":round(total,4)}

def rest(url,n):
    endpoint=url.rstrip("/")+"/summary"; requests.get(endpoint,timeout=10)
    ts=[]; err=0; start=time.perf_counter()
    for _ in range(n):
        t=time.perf_counter()
        try:
            r=requests.get(endpoint,timeout=10)
            if r.status_code!=200: err+=1
            else: r.json()
        except requests.RequestException: err+=1
        ts.append((time.perf_counter()-t)*1000)
    return summarize("REST",ts,err,n,time.perf_counter()-start)

def graphql(url,n):
    endpoint=url.rstrip("/")+"/graphql"
    payload={"query":"{ summary { totalEvents totalAmount byCategory { category count averageAmount } } }"}
    requests.post(endpoint,json=payload,timeout=10)
    ts=[]; err=0; start=time.perf_counter()
    for _ in range(n):
        t=time.perf_counter()
        try:
            r=requests.post(endpoint,json=payload,timeout=10); data=r.json()
            if r.status_code!=200 or "errors" in data: err+=1
        except (requests.RequestException,ValueError): err+=1
        ts.append((time.perf_counter()-t)*1000)
    return summarize("GraphQL",ts,err,n,time.perf_counter()-start)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--requests",type=int,default=300)
    p.add_argument("--rest-url",default="http://127.0.0.1:8000")
    p.add_argument("--graphql-url",default="http://127.0.0.1:8001")
    p.add_argument("--output",default="results/api_benchmark.csv"); a=p.parse_args()
    rows=[rest(a.rest_url,a.requests),graphql(a.graphql_url,a.requests)]
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    for row in rows: print(row)
    print("Guardado:",out)
if __name__=="__main__": main()
