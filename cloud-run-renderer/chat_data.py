"""chat_data.py — reusable data-atom fetchers for the Chat render deck.

Each source here is declared in atoms/data-sources.yaml (workspace_status,
open_meteo) -- this module is the one place that actually calls the
declared upstream and shapes the response into ready-to-render atom blocks
(service_status_board/incident_log/stat_pulse, weather_now/weather_outlook).
Any future consumer (a different Chat command, a scheduled digest, a web
page) should import from here rather than re-deriving the fetch/parse logic.

Both fetchers are plain stdlib (urllib) -- no new dependency, matching the
rest of cloud-run-renderer.
"""
import json
import statistics
import urllib.request
from datetime import datetime, timedelta, timezone

WORKSPACE_STATUS_URL = "https://www.google.com/appsstatus/dashboard/incidents.json"
OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
    "&current=temperature_2m,relative_humidity_2m,weathercode,windspeed_10m"
    "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode"
    "&timezone=Europe%2FParis&forecast_days=3"
)
TOULOUSE = {"lat": 43.6047, "lon": 1.4442}

# Canonical tracked-service list for the board -- the incidents feed only
# ever lists services that HAD an incident, not a full roster, so the "all
# quiet" board needs its own declared list to show as all-operational.
TRACKED_SERVICES = [
    "Gmail", "Google Meet", "Google Drive", "Apps Script", "Google Calendar",
    "Workspace Studio", "Google Docs", "Admin Console", "Google Chat", "Gemini",
]

_IMPACT_TO_STATE = {
    "SERVICE_OUTAGE": "critical",
    "SERVICE_DISRUPTION": "disruption",
    "SERVICE_INFORMATION": "information",
}


def _fetch_json(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": "a2ui-catalogue/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def _parse_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _fmt_duration(begin: datetime, end: datetime) -> str:
    mins = int((end - begin).total_seconds() // 60)
    h, m = divmod(mins, 60)
    return f"{h}h {m}m" if h else f"{m}m"


# -- Workspace status: real feed, "now" or a labeled historical replay --

def fetch_workspace_incidents() -> list:
    """Raw incident list from the declared workspace_status source."""
    return _fetch_json(WORKSPACE_STATUS_URL)


def _active_at(incidents: list, as_of: datetime) -> list:
    """Incidents whose [begin, end) window contains as_of."""
    active = []
    for inc in incidents:
        begin = _parse_dt(inc["begin"])
        end = _parse_dt(inc["end"]) if inc.get("end") else None
        if begin <= as_of and (end is None or as_of < end):
            active.append(inc)
    return active


def largest_incident_as_of(incidents: list) -> datetime:
    """The 'interesting example' convenience for a bare demo/replay request
    with no specific date: the real incident affecting the most services,
    20 minutes into its window."""
    biggest = max(incidents, key=lambda i: len(i.get("affected_products") or [i.get("service_name", "")]))
    return _parse_dt(biggest["begin"]) + timedelta(minutes=20)


def build_workspace_cards(incidents: list, as_of: datetime = None) -> list:
    """Returns [service_status_board, incident_log, stat_pulse] block dicts,
    health-as-of a point in time -- real now by default, or any requested
    datetime (a genuine point-in-time query, not just a canned replay).
    Historical queries are labeled 'AS OF' in the stamp so a rendered card
    is never mistaken for live status; a request within 10 minutes of real
    now reads as plain live status."""
    now = datetime.now(timezone.utc)
    as_of = now if as_of is None else as_of
    is_live = abs((now - as_of).total_seconds()) < 600
    stamp = as_of.strftime("%d %b %Y · %H:%M UTC")
    if not is_live:
        stamp = f"AS OF {stamp}"

    active = _active_at(incidents, as_of)
    active_by_service = {}
    for inc in active:
        for prod in (inc.get("affected_products") or [{"title": inc.get("service_name", "")}]):
            active_by_service[prod["title"]] = inc

    services = []
    for name in TRACKED_SERVICES:
        inc = active_by_service.get(name)
        state = _IMPACT_TO_STATE.get(inc["status_impact"], "disruption") if inc else "operational"
        services.append({"name": name, "state": state})

    if active:
        worst = max(active, key=lambda i: {"SERVICE_OUTAGE": 3, "SERVICE_DISRUPTION": 2,
                                            "SERVICE_INFORMATION": 1}.get(i["status_impact"], 0))
        n = len(active_by_service)
        level = {"SERVICE_OUTAGE": "crit", "SERVICE_DISRUPTION": "warn",
                 "SERVICE_INFORMATION": "warn"}.get(worst["status_impact"], "warn")
        verdict = {
            "level": level,
            "text": f"{n} active {'disruption' if n == 1 else 'disruptions'}",
            "detail": f"{worst.get('service_name', '')} — {_first_line(worst.get('external_desc', ''))}",
        }
    else:
        verdict = {"level": "ok", "text": "All services operational", "detail": ""}

    board = {
        "type": "service_status_board",
        "title": "GOOGLE WORKSPACE — SERVICE STATUS",
        "stamp": stamp,
        "verdict": verdict,
        "services": services,
    }

    # Last 7 days (relative to as_of), from the real feed
    week = []
    for i in range(6, -1, -1):
        day_start = (as_of - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_incidents = [inc for inc in incidents if day_start <= _parse_dt(inc["begin"]) < day_end]
        sev = "none"
        for inc in day_incidents:
            s = inc.get("severity", "low")
            if s == "high" or (s == "medium" and sev != "high"):
                sev = "medium" if s == "medium" else "high"
            elif sev == "none":
                sev = "low"
        week.append({"label": day_start.strftime("%a")[:3].upper()[:1] + day_start.strftime("%a")[1:3],
                     "count": len(day_incidents), "severity": "medium" if sev == "high" else sev})

    recent = sorted(incidents, key=lambda i: _parse_dt(i["begin"]), reverse=True)[:4]
    inc_rows = []
    for inc in recent:
        begin = _parse_dt(inc["begin"])
        end = _parse_dt(inc["end"]) if inc.get("end") else as_of
        inc_rows.append({
            "service": inc.get("service_name", ""),
            "summary": _first_line(inc.get("external_desc", "")),
            "severity": inc.get("severity", "low"),
            "duration": _fmt_duration(begin, end),
            "when": begin.strftime("%a %d"),
            "ongoing": inc.get("end") is None,
        })

    log = {
        "type": "incident_log",
        "title": "LAST 7 DAYS — INCIDENT LOG",
        "stamp": f"{(as_of - timedelta(days=6)).strftime('%d')} – {as_of.strftime('%d %b')}",
        "week": week,
        "incidents": inc_rows,
    }

    thirty_ago = as_of - timedelta(days=30)
    sixty_ago = as_of - timedelta(days=60)
    last_30 = [i for i in incidents if thirty_ago <= _parse_dt(i["begin"]) <= as_of]
    prior_30 = [i for i in incidents if sixty_ago <= _parse_dt(i["begin"]) < thirty_ago]
    durations = [(_parse_dt(i["end"]) - _parse_dt(i["begin"])).total_seconds() / 60
                 for i in last_30 if i.get("end")]
    median_min = int(statistics.median(durations)) if durations else 0
    delta_n = len(last_30) - len(prior_30)
    counts_by_service = {}
    for i in last_30:
        counts_by_service[i.get("service_name", "?")] = counts_by_service.get(i.get("service_name", "?"), 0) + 1
    top_service, top_count = max(counts_by_service.items(), key=lambda kv: kv[1]) if counts_by_service else ("—", 0)

    weeks = [[] for _ in range(4)]
    for i in last_30:
        age_days = (as_of - _parse_dt(i["begin"])).days
        idx = min(age_days // 7, 3)
        weeks[3 - idx].append(i)
    bars = [len(w) for w in weeks]

    pulse = {
        "type": "stat_pulse",
        "title": "30-DAY PULSE",
        "stamp": f"{thirty_ago.strftime('%d %b')} – {as_of.strftime('%d %b')}",
        "stats": [
            {"value": str(len(last_30)), "label": "Incidents",
             "delta": f"{'▼' if delta_n < 0 else '▲' if delta_n > 0 else '—'} {abs(delta_n)} vs prior 30d",
             "tone": "good" if delta_n < 0 else "bad" if delta_n > 0 else "flat"},
            {"value": f"{median_min // 60}h {median_min % 60}m" if median_min >= 60 else f"{median_min}m",
             "label": "Median resolve", "delta": "—", "tone": "flat"},
            {"value": top_service, "label": "Most affected",
             "delta": f"{top_count} of {len(last_30)} incidents", "tone": "flat"},
        ],
        "trend": {"bars": bars, "labels": ["W1", "W2", "W3", "W4 · now"], "hot_index": 3},
    }

    return [board, log, pulse]


def _first_line(desc: str) -> str:
    for line in desc.replace("**Title**", "").splitlines():
        line = line.strip()
        if line and not line.startswith("**"):
            return line[:110]
    return desc[:110]


# -- Weather: Open-Meteo, Toulouse by default --

_WMO_CODE = {
    0: ("sun", "Ensoleillé"), 1: ("sun", "Ensoleillé"), 2: ("partly", "Partiellement nuageux"),
    3: ("cloud", "Nuageux"), 45: ("cloud", "Brumeux"), 48: ("cloud", "Brumeux"),
    51: ("rain", "Bruine légère"), 53: ("rain", "Bruine"), 55: ("rain", "Bruine forte"),
    56: ("rain", "Bruine verglaçante"), 57: ("rain", "Bruine verglaçante"),
    61: ("rain", "Pluie légère"), 63: ("rain", "Pluie"), 65: ("rain", "Pluie forte"),
    66: ("rain", "Pluie verglaçante"), 67: ("rain", "Pluie verglaçante"),
    71: ("rain", "Neige légère"), 73: ("rain", "Neige"), 75: ("rain", "Neige forte"), 77: ("rain", "Grains de neige"),
    80: ("rain", "Averses légères"), 81: ("rain", "Averses"), 82: ("rain", "Averses violentes"),
    85: ("rain", "Averses de neige"), 86: ("rain", "Averses de neige fortes"),
    95: ("storm", "Orage"), 96: ("storm", "Orage avec grêle"), 99: ("storm", "Orage avec grêle"),
}


def _wmo(code: int) -> tuple:
    return _WMO_CODE.get(code, ("cloud", "Couvert"))


def fetch_weather(lat: float = None, lon: float = None) -> dict:
    lat = TOULOUSE["lat"] if lat is None else lat
    lon = TOULOUSE["lon"] if lon is None else lon
    return _fetch_json(OPEN_METEO_URL.format(lat=lat, lon=lon))


def build_weather_cards(data: dict, city_line: str = "TOULOUSE — LA VILLE ROSE",
                         city: str = "Toulouse") -> list:
    cur = data["current"]
    daily = data["daily"]
    code, condition = _wmo(cur["weathercode"])
    now_dt = datetime.now(timezone.utc)

    now_card = {
        "type": "weather_now",
        "city_line": city_line,
        "stamp": now_dt.strftime("%a %d %b · %H:%M"),
        "temp": round(cur["temperature_2m"]),
        "condition": condition,
        "code": code,
        "hi": round(daily["temperature_2m_max"][0]),
        "lo": round(daily["temperature_2m_min"][0]),
        "stats": [
            {"value": f"{daily['precipitation_probability_max'][0]}%", "label": "Precip"},
            {"value": f"{round(cur['windspeed_10m'])} km/h", "label": "Wind"},
            {"value": str(round(daily['precipitation_probability_max'][0] / 10)), "label": "UV"},
            {"value": f"{cur['relative_humidity_2m']}%", "label": "Humidity"},
        ],
    }

    days = []
    for i in range(min(3, len(daily["time"]))):
        d_code, _ = _wmo(daily["weathercode"][i])
        d_date = datetime.fromisoformat(daily["time"][i])
        days.append({
            "label": d_date.strftime("%a").upper(),
            "date": d_date.strftime("%d %b"),
            "code": d_code,
            "hi": round(daily["temperature_2m_max"][i]),
            "lo": round(daily["temperature_2m_min"][i]),
            "precip": daily["precipitation_probability_max"][i],
        })
    lo_bound = min(d["lo"] for d in days) - 4
    hi_bound = max(d["hi"] for d in days) + 4
    outlook_card = {
        "type": "weather_outlook",
        "title": "NEXT 3 DAYS — OUTLOOK",
        "city": city,
        "scale": {"min": lo_bound, "max": hi_bound},
        "days": days,
    }
    return [now_card, outlook_card]
