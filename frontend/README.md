# AgroSmart Frontend

React 18 + Vite + Tailwind CSS dashboard.

## Prerequisites

- Node.js 18+ and npm — download from [nodejs.org](https://nodejs.org)

## Quick Start

```bash
# From the frontend/ directory:
npm install
npm run dev      # starts at http://localhost:3000
```

> The Vite dev server proxies all `/api` requests to `http://localhost:5000`
> (the Flask backend). Start the backend first:
> ```bash
> # From backend/
> python run.py
> ```

## Build for production

```bash
npm run build    # output in frontend/dist/
```

## Project structure

```
src/
  App.jsx                  # Router + layout
  main.jsx                 # React entry point
  index.css                # Tailwind + global styles
  pages/                   # 6 route pages
  components/
    layout/                # Sidebar, Navbar, PageWrapper
    sensors/               # SensorCard, SensorGrid, SensorChart
    shared/                # StatusBadge, LoadingSpinner, ErrorAlert
  hooks/                   # useSensorData, useAnalysis, useHistory
  services/api.js          # All axios API calls
  store/sensorStore.js     # Zustand live sensor state
  utils/                   # formatters.js, constants.js
```
