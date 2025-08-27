# ✈️ Flight Path Weather Monitoring & Safety App (FastAPI + Matplotlib)

This app analyzes a flight path between two cities or airports, checks live weather conditions at waypoints along the route, and provides recommendations on whether it’s safe to continue or if an emergency landing is advised.  
It uses **OpenWeather APIs** for geocoding + weather, **Matplotlib** for plotting the route, and a CSV dataset for nearest-airport/city lookup.

---

## 1) Setup

```bash
cd flight-safety-app
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt


Create a .env file or set an environment variable with your OpenWeather API key:

OPENWEATHER_API_KEY=<your_api_key>

2) Run Locally
uvicorn app.main:app --reload --port 8000
# Open http://localhost:8000


You’ll see a form to enter Departure City and Arrival City.
The app will:

Geocode both cities

Generate intermediate waypoints

Fetch weather for each waypoint

Show a plotted map with safety status + nearest city names

Display a summary table with temperature, wind, condition, and safety recommendation.

3) Build Docker Image
docker build -t flight-safety-app:latest .
docker run -p 8000:8000 -e OPENWEATHER_API_KEY=<your_api_key> flight-safety-app:latest


Open http://localhost:8000
 inside your browser.

4) Push to Azure Container Registry (ACR)
az acr create -g <rg> -n <acrName> --sku Basic
az acr login -n <acrName>

docker tag flight-safety-app:latest <acrName>.azurecr.io/flight-safety-app:latest
docker push <acrName>.azurecr.io/flight-safety-app:latest

5) Deploy to Azure App Service (Linux)
az appservice plan create -g <rg> -n flight-safety-plan --sku B1 --is-linux
az webapp create -g <rg> -p flight-safety-plan -n <webAppName> \
   -i <acrName>.azurecr.io/flight-safety-app:latest

Set required environment variables:
az webapp config appsettings set -g <rg> -n <webAppName> --settings \
  OPENWEATHER_API_KEY=<your_api_key> \
  WEBSITES_PORT=8000 \
  WEBSITE_HEALTHCHECK_PATH=/healthz


If ACR authentication is required:

az webapp config container set -g <rg> -n <webAppName> \
  --docker-custom-image-name <acrName>.azurecr.io/flight-safety-app:latest \
  --docker-registry-server-url https://<acrName>.azurecr.io

Notes

Waypoint Cities: Determined by the nearest entry in app/airports_data.csv.
Replace with a richer dataset (e.g., OpenFlights Airports
) for global accuracy.

Safety thresholds:

❌ Unsafe if temp < -10°C or > 50°C

❌ Unsafe if wind > 15 m/s

❌ Unsafe if thunderstorms/extreme conditions (OpenWeather condition codes)

Results appear below the input form. No extra navigation required.

JSON API also available: POST /api/analyze with { "departure": "London", "arrival": "Tokyo" }.

License

MIT © 2025 Avinash Bellamkonda
EOF 
