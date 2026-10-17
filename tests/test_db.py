from src.db import reset_db, upsert_events, summary

def test_upsert_is_idempotent(tmp_path):
    db=str(tmp_path/"test.sqlite"); reset_db(db)
    row=[{"event_id":1,"event_time":"2026-01-01T00:00:00+00:00",
          "category":"matricula","campus":"Chupa","amount":10.0}]
    upsert_events(row,db); upsert_events(row,db)
    assert summary(db)["total_events"] == 1
