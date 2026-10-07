from fastapi import FastAPI, Response, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import json

app = FastAPI()


# --------------------------------------------------
# FORCE CORS HEADERS ON EVERY RESPONSE
# --------------------------------------------------

@app.middleware("http")
async def force_cors(request: Request, call_next):
    if request.method == "OPTIONS":
        response = PlainTextResponse("OK", status_code=200)
    else:
        response = await call_next(request)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"

    return response


# --------------------------------------------------
# TELEMETRY DATA
# --------------------------------------------------

DATA = json.loads(r'''
[
  {"region":"apac","latency_ms":141.66,"uptime_pct":98.447},
  {"region":"apac","latency_ms":170.48,"uptime_pct":98.85},
  {"region":"apac","latency_ms":136.98,"uptime_pct":99.184},
  {"region":"apac","latency_ms":203.63,"uptime_pct":97.764},
  {"region":"apac","latency_ms":209.56,"uptime_pct":97.848},
  {"region":"apac","latency_ms":191.23,"uptime_pct":98.807},
  {"region":"apac","latency_ms":192.86,"uptime_pct":97.954},
  {"region":"apac","latency_ms":219.22,"uptime_pct":97.896},
  {"region":"apac","latency_ms":199.37,"uptime_pct":97.961},
  {"region":"apac","latency_ms":190.33,"uptime_pct":98.397},
  {"region":"apac","latency_ms":223.81,"uptime_pct":98.098},
  {"region":"apac","latency_ms":198.14,"uptime_pct":99.467},

  {"region":"emea","latency_ms":116.33,"uptime_pct":97.807},
  {"region":"emea","latency_ms":202.3,"uptime_pct":99.077},
  {"region":"emea","latency_ms":134.88,"uptime_pct":99.032},
  {"region":"emea","latency_ms":196.47,"uptime_pct":98.614},
  {"region":"emea","latency_ms":118.41,"uptime_pct":99.175},
  {"region":"emea","latency_ms":193.74,"uptime_pct":98.724},
  {"region":"emea","latency_ms":196.89,"uptime_pct":97.571},
  {"region":"emea","latency_ms":122.53,"uptime_pct":99.394},
  {"region":"emea","latency_ms":178.13,"uptime_pct":98.797},
  {"region":"emea","latency_ms":158.34,"uptime_pct":98.182},
  {"region":"emea","latency_ms":134.79,"uptime_pct":98.186},
  {"region":"emea","latency_ms":194.72,"uptime_pct":97.647},

  {"region":"amer","latency_ms":125.99,"uptime_pct":98.739},
  {"region":"amer","latency_ms":196.07,"uptime_pct":98.191},
  {"region":"amer","latency_ms":211.83,"uptime_pct":97.726},
  {"region":"amer","latency_ms":214.15,"uptime_pct":97.694},
  {"region":"amer","latency_ms":160.51,"uptime_pct":97.145},
  {"region":"amer","latency_ms":221.79,"uptime_pct":98.774},
  {"region":"amer","latency_ms":137.26,"uptime_pct":98.268},
  {"region":"amer","latency_ms":200.07,"uptime_pct":97.162},
  {"region":"amer","latency_ms":198.94,"uptime_pct":97.133},
  {"region":"amer","latency_ms":237.6,"uptime_pct":99.163},
  {"region":"amer","latency_ms":213.98,"uptime_pct":98.889},
  {"region":"amer","latency_ms":183.47,"uptime_pct":97.221}
]
''')


# --------------------------------------------------
# REQUEST MODEL
# --------------------------------------------------

class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float


# --------------------------------------------------
# 95th PERCENTILE
# --------------------------------------------------

def percentile_95(values: list[float]) -> float:
    values = sorted(values)

    if not values:
        return 0.0

    position = (len(values) - 1) * 0.95
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower

    return values[lower] + (
        values[upper] - values[lower]
    ) * fraction


# --------------------------------------------------
# API ENDPOINT
# --------------------------------------------------

@app.post("/")
def analytics(
    request: AnalyticsRequest,
    response: Response
):
    # Explicit CORS header on successful POST response
    response.headers["Access-Control-Allow-Origin"] = "*"

    result = []

    for region in request.regions:

        rows = [
            item
            for item in DATA
            if item["region"] == region
        ]

        if not rows:
            continue

        latencies = [
            item["latency_ms"]
            for item in rows
        ]

        uptimes = [
            item["uptime_pct"]
            for item in rows
        ]

        result.append({
            "region": region,
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile_95(latencies),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(
                1
                for latency in latencies
                if latency > request.threshold_ms
            )
        })

    return result