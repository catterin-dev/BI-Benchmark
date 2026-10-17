from fastapi import FastAPI
from src.db import summary
app=FastAPI(title="BI Benchmark REST",version="1.0.0")
@app.get("/summary")
def get_summary():
    return summary()
