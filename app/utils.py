import io
import base64
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from geopy.distance import geodesic

# NEW: pooled requests session with retries
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

AIRPORTS = None

def _make_session():
    s = requests.Session()
    retries = Retry(
        total=2,                # small number of retries
        connect=2,
        read=2,
        backoff_factor=0.4,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=16, pool_maxsize=16)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update({"User-Agent": "flight-safety-app/1.0"})
    return s

_SESSION = _make_session()

def load_airports(csv_path: str):
    """Lazy-load and validate airports CSV."""
    global AIRPORTS
    if AIRPORTS is None:
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip().str.lower()
        required = {"airport name", "city", "country", "latitude", "longitude"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"airports_data.csv missing columns: {', '.join(sorted(missing))}")
        AIRPORTS = df
    return AIRPORTS

# ---- MODIFIED: use HTTPS + pooled session + timeout ----
def get_city_coordinates(city_name: str, api_key: str):
    base_url = "https://api.openweathermap.org/geo/1.0/direct"
    try:
        r = _SESSION.get(f"{base_url}?q={city_name}&appid={api_key}&limit=1", timeout=8)
        if r.status_code == 200 and r.json():
            d = r.json()[0]
            return (d["lat"], d["lon"])
    except Exception:
        pass
    return None

def generate_waypoints(start_coords, end_coords, num_points=6):
    lat = np.linspace(start_coords[0], end_coords[0], num_points)
    lon = np.linspace(start_coords[1], end_coords[1], num_points)
    return list(zip(lat, lon))

# ---- MODIFIED: parallel weather fetch with retries + HTTPS + timeouts ----
def _fetch_weather(lat, lon, api_key: str, timeout=8):
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    )
    try:
        r = _SESSION.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        return {"error": f"http {r.status_code}: {r.text[:120]}"}  # structured stub
    except Exception as e:
        return {"error": str(e)}

def get_current_weather_for_route(waypoints, api_key: str):
    results = [None] * len(waypoints)
    with ThreadPoolExecutor(max_workers=min(8, len(waypoints))) as ex:
        futs = {ex.submit(_fetch_weather, lat, lon, api_key): i
                for i, (lat, lon) in enumerate(waypoints)}
        for fut in as_completed(futs):
            idx = futs[fut]
            try:
                results[idx] = fut.result()
            except Exception as e:
                results[idx] = {"error": str(e)}
    return results

def find_nearest_airport(waypoint, airport_df: pd.DataFrame):
    nearest_airport = nearest_city = nearest_country = None
    nearest_coords = None
    min_d = float("inf")
    for _, row in airport_df.iterrows():
        coords = (row["latitude"], row["longitude"])
        d = geodesic(waypoint, coords).kilometers
        if d < min_d:
            min_d = d
            nearest_airport = row.get("airport name")
            nearest_city = row.get("city")
            nearest_country = row.get("country")
            nearest_coords = coords
    return nearest_airport, nearest_city, nearest_country, nearest_coords

def get_waypoint_city_labels(waypoints, airport_df):
    labels = []
    for wp in waypoints:
        nearest_airport, city, country, _ = find_nearest_airport(wp, airport_df)
        if city and country:
            labels.append(f"{city}, {country}")
        elif city:
            labels.append(city)
        elif nearest_airport:
            labels.append(nearest_airport)
        else:
            labels.append("Unknown")
    return labels

def analyze_weather(weather_data):
    recs, unsafe_idx = [], -1
    for i, data in enumerate(weather_data):
        loc = f"Waypoint {i+1}"
        if not data or ("error" in data):
            recs.append((loc, "Data unavailable"))
            continue
        safe = True
        temp = data["main"]["temp"]
        wind = data["wind"]["speed"]
        wid  = data["weather"][0]["id"]
        if temp < -10 or temp > 50: safe = False
        if wind > 15: safe = False
        if wid <= 232 or wid > 900: safe = False
        recs.append((loc, "Safe to continue" if safe else "Unsafe to continue"))
        if not safe:
            unsafe_idx = i
    return recs, unsafe_idx

def plot_route_with_recommendations(
    waypoints, recommendations, departure_coords, arrival_coords,
    departure_city, arrival_city, waypoint_city_labels,
    emergency=None
):
    lat, lon = zip(*waypoints)
    colors = ["green" if r[1] == "Safe to continue" else "red" for r in recommendations]

    # ---- MODIFIED: slightly smaller figure for faster render + smaller payload ----
    fig = plt.figure(figsize=(8, 6), dpi=100)
    plt.scatter(lon, lat, c=colors, marker="o", s=100, label="Waypoints")
    plt.plot(lon, lat, linestyle="--", color="blue", label="Flight Path")

    plt.scatter(departure_coords[1], departure_coords[0], c="blue", marker="*", s=200, label=f"Departure: {departure_city}")
    plt.scatter(arrival_coords[1],   arrival_coords[0],   c="brown", marker="*", s=200, label=f"Arrival: {arrival_city}")

    for i, rec in enumerate(recommendations):
        plt.annotate(rec[1], (lon[i], lat[i]), textcoords="offset points", xytext=(0, 10), ha="center")
        if waypoint_city_labels and i < len(waypoint_city_labels):
            plt.annotate(waypoint_city_labels[i], (lon[i], lat[i]), textcoords="offset points", xytext=(0, -15), ha="center", fontsize=9)

    if emergency:
        e_coords, e_airport, e_city, e_country = emergency
        plt.scatter(e_coords[1], e_coords[0], c="red", marker="X", s=200, label="Emergency Landing Airport")
        plt.annotate(f"{e_airport} ({e_city}, {e_country})",
                     (e_coords[1], e_coords[0]), textcoords="offset points", xytext=(0, -18), ha="center", color="red")

    plt.title("Flight Path with Safety Recommendations")
    plt.legend()
    plt.grid()
    plt.xticks([]); plt.yticks([])

    buf = io.BytesIO()
    # ---- MODIFIED: set dpi in savefig, too ----
    plt.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("utf-8")

def build_response(departure_city: str, arrival_city: str, api_key: str, airports_csv_path: str):
    airports = load_airports(airports_csv_path)

    dep = get_city_coordinates(departure_city, api_key)
    arr = get_city_coordinates(arrival_city, api_key)
    if not dep or not arr:
        return {"error": "Could not fetch coordinates. Check city/airport names."}

    # (optional) reduce to 5 waypoints to cut one API call:
    waypoints = generate_waypoints(dep, arr, num_points=6)
    labels    = get_waypoint_city_labels(waypoints, airports)
    weather   = get_current_weather_for_route(waypoints, api_key)
    recs, unsafe_idx = analyze_weather(weather)

    alert = "All clear on current check."
    emergency = None
    if recs[0][1] == "Unsafe to continue":
        alert = f"Delay departure at {departure_city}. First waypoint is unsafe."
    elif recs[1][1] == "Unsafe to continue":
        alert = f"Delay departure at {departure_city}. Second waypoint is unsafe."
    elif unsafe_idx > 1:
        prev = unsafe_idx - 1
        nearest_airport, e_city, e_country, e_coords = find_nearest_airport(waypoints[prev], airports)
        alert = f"Emergency landing recommended at {nearest_airport} ({e_city}, {e_country})."
        emergency = (e_coords, nearest_airport, e_city, e_country)

    plot_b64 = plot_route_with_recommendations(
        waypoints, recs, dep, arr, departure_city, arrival_city, labels, emergency=emergency
    )

    rows = []
    for i, w in enumerate(weather):
        rows.append({
            "waypoint": f"Waypoint {i+1}",
            "nearest_city": labels[i],
            "safety": recs[i][1],
            "temp_c": (w.get("main", {}).get("temp") if isinstance(w, dict) else None),
            "wind_ms": (w.get("wind", {}).get("speed") if isinstance(w, dict) else None),
            "condition": (w.get("weather", [{}])[0].get("description") if isinstance(w, dict) else None),
        })

    return {
        "alert": alert,
        "plot": plot_b64,
        "rows": rows,
        "departure": departure_city,
        "arrival": arrival_city
    }
