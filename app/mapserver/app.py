import sqlite3
from fastapi import FastAPI
import uvicorn
import math

app = FastAPI()
DB = "places.db"

@app.get("/geo")
def geo(q: str, lat: float, lon: float, limit: int = 8):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    
    normalized = (
        q.lower()
         .replace(",", " ")
         .replace(".", " ")
    )
    search_q = "%" + normalized + "%"
    
    rows = conn.execute("""
        SELECT
            name,
            lat,
            lon,
            type,
            address,
            (
                (lat - ?) * (lat - ?) +
                (lon - ?) * (lon - ?)
            ) AS dist_sq
        FROM places
        WHERE
            REPLACE(
                REPLACE(LOWER(name), ',', ' '),
                '.',
                ' '
            ) LIKE ?
            OR
            REPLACE(
                REPLACE(LOWER(address), ',', ' '),
                '.',
                ' '
            ) LIKE ?
        ORDER BY
            dist_sq ASC
        LIMIT ?
    """, (
        lat, lat,
        lon, lon,
        search_q,
        search_q,
        limit
    )).fetchall()
    
    conn.close()
    return [dict(r) for r in rows]

@app.get("/health")
def health():
    conn = sqlite3.connect(DB)
    count = conn.execute("SELECT COUNT(*) FROM places").fetchone()[0]
    conn.close()
    return {"status": "ok", "places": count}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)