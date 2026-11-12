# AgroSmart Frontend

React 18 + Vite + Tailwind CSS dashboard for the AgroSmart Flask backend.

## Run

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000  (proxies /api -> http://localhost:5000)
npm run build      # production build in dist/
```

Start the backend first (`python run.py` in `backend/`). If the backend is not reachable the
UI automatically switches to **demo mode** with sample data (an amber banner is shown), so you
can still present the project.

## Options (`.env`)

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | API base URL (default `/api`, uses the Vite proxy) |
| `VITE_USE_MOCK=true` | Always use demo data, never call the backend |

## Pages

| Route | Page |
|-------|------|
| `/` | Dashboard: live sensor cards, NPK, trend chart, latest AI recommendation |
| `/sensors` | Live sensors (5 s polling), history chart, manual reading form, paginated log |
| `/analysis`, `/analysis/:id` | Run full AI pipeline, view saved analyses |
| `/scanner` | Upload soil image, CNN soil-type result with class probabilities |
| `/history` | Analyses and predictions history, crop frequency chart |
| `/system` | Backend health, models, data flow, endpoint list |

## Structure

```
src/
  pages/       6 route pages
  components/  Layout, ui (Card/Badge/...), StatCard, TrendChart, RecommendationGrid
  hooks/       useAsync (fetch + polling), useData (typed data hooks)
  services/    api.js (axios), mockData.js (demo fallback), status.js
  utils/       normalize.js (response mapping), metrics.js (ranges + formatting)
```

## If your API field names differ

All response mapping lives in `src/utils/normalize.js`. Each field accepts several aliases
(e.g. `soil_moisture` / `moisture`); add your own key name to the alias list if something shows `—`.
Optimal ranges for the sensor bars are in `src/utils/metrics.js`.
