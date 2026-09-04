# Sea Scan

A maritime trade route intelligence platform that visualizes global sea routes with live risk and efficiency scoring. Built as an M.Sc. Data Science specialization project at CHRIST (Deemed to be University).

**Live demo:** [sea-scan on Render](https://sea-scan.onrender.com/)
**Repository:** https://github.com/adwaithpajith/sea-scan

---

## Overview

Global maritime trade funnels through a small set of geographic chokepoints (the Suez and Panama Canals, the Straits of Hormuz and Malacca, Bab el-Mandeb, and others) whose risk profile shifts with weather and geopolitical conditions largely independently of one another. Most existing tracking tools compress these dimensions into a single composite "risk score," obscuring the trade-off a shipping planner actually needs to weigh.

Sea Scan takes a different approach. Given a source and destination port, it computes up to five distinct maritime corridors and scores each one on two **independent** axes:

- **Risk Score** — live weather along the route combined with curated, auto-refreshed conflict-advisory data at any chokepoints crossed
- **Efficiency Score** — distance, estimated CO2 emissions, and cost per TEU, normalized across the alternative corridors

There is no composite score and no single "recommended" route. The platform surfaces both scores independently and lets the user make the trade-off.

## Key Features

- **Land-safe multi-corridor routing** across up to five named corridors (Suez, Cape of Good Hope, Panama, Lombok, Cape Horn), built on the `searoute` library rather than a hand-coded waypoint graph
- **Live weather scoring** using ETA-shifted Open-Meteo Marine forecasts sampled along each route's geometry
- **Automated conflict-risk pipeline** that scrapes and scores four sources (MARAD MSCI, Maritime Executive, gCaptain, UKMTO) daily via GitHub Actions, quoting the actual matching advisory or headline behind each score rather than a bare keyword count
- **K-Means port risk clustering** of the full NGA World Port Index (3,804 ports) into five risk tiers, using a live exposure feature (risk combined with proximity decay) rather than a static snapshot
- **Two-objective route comparison UI** with neutral "Lowest Risk" / "Most Efficient" badges — never a single ranked recommendation
- **Fully automated data refresh** — conflict-advisory data daily, NGA port data monthly — with commits only made when the underlying data actually changes

## Architecture

```
Frontend (Leaflet.js)
        |
   API layer (FastAPI)
        |
Routing & scoring engine
   |      |       |         |
Routing Weather Conflict Clustering
        |
External data sources:
  NGA World Port Index, Open-Meteo Marine API,
  MARAD / Maritime Executive / gCaptain / UKMTO
```

The backend is stateless. Ports are loaded from a CSV into memory at startup and the K-Means clustering model is built once at boot. Conflict-advisory data is not fetched live per request — it is pre-computed offline by a scheduled job and committed into the repository as a static, importable module (`backend/conflict.py`), which the API reads directly.

## Repository Structure

```
sea-scan/
├── backend/
│   ├── main.py            FastAPI application and REST endpoints
│   ├── engine.py          searoute integration, multi-corridor generation, chokepoint detection
│   ├── weather.py         ETA-shifted Open-Meteo weather scoring
│   ├── conflict.py        Auto-generated daily — chokepoint risk lookup table (do not edit manually)
│   ├── clustering.py      K-Means port risk clustering
│   ├── metrics.py         Risk Score, Efficiency Score, and extreme-tagging logic
│   └── data/
│       └── UpdatedPub150.csv   NGA World Port Index (refreshed monthly)
├── frontend/
│   └── index.html          Leaflet.js map UI, route comparison cards, weather popups
├── update_conflict.py      Conflict-advisory scraper and scorer, run by the daily workflow
├── update_ports.py         NGA port data refresher, run by the monthly workflow
├── requirements.txt
└── .github/
    └── workflows/
        ├── update_conflict.yml   Daily conflict-risk update (06:00 UTC)
        └── update_ports.yml      Monthly port data update
```

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Pydantic |
| Data processing / ML | pandas, NumPy, scikit-learn (K-Means) |
| Routing | searoute |
| Web scraping | requests, BeautifulSoup4 |
| Frontend | HTML5, CSS3, vanilla JavaScript, Leaflet.js |
| Deployment | Render |
| Automation | GitHub Actions |

See `requirements.txt` for exact pinned versions.

## Running Locally

**Prerequisites:** Python 3.11+

```bash
git clone https://github.com/adwaithpajith/sea-scan.git
cd sea-scan
pip install -r requirements.txt --break-system-packages
uvicorn backend.main:app --reload
```

The application will be available at `http://localhost:8000`.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Service health check |
| GET | `/api/ports` | All ports with cluster assignments |
| GET | `/api/port-search?q=` | Port name autocomplete search |
| GET | `/api/chokepoints` | All chokepoints with current risk ratings |
| POST | `/api/routes` | Compute and score routes between a source and destination port |

## Automation

Two scheduled GitHub Actions workflows keep the platform's data current without manual intervention:

- **Daily Conflict Risk Update** (`0 6 * * *`) — fetches current advisory data from MARAD, Maritime Executive, gCaptain, and UKMTO, rescoring all chokepoints and committing an updated `backend/conflict.py` only when scores actually changed.
- **Monthly Port Data Update** (`0 5 1 * *`) — refreshes the NGA World Port Index from source.

Both workflows can also be triggered manually from the Actions tab.

## Known Limitations

This project documents its limitations rather than hiding them:

- **UKMTO** cannot currently be scraped reliably. Its incident pages are client-side rendered (a JavaScript single-page application), so a plain HTTP request returns an empty shell regardless of what data actually exists behind it. This would require headless-browser scraping (e.g. Playwright) to fix.
- **MARAD** is blocked at the network level for requests originating from cloud/datacenter IP ranges, confirmed by testing from two independent origins (GitHub Actions and an unrelated Render-hosted server) and observing the same HTTP 403 from both. A fallback relay path exists, but is subject to the same underlying block.
- **Baseline conflict-risk scores** are hardcoded starting points per chokepoint. Live keyword-based adjustments are capped (-0.3 to +2.5), so for most chokepoints the static baseline — not live data — determines which risk tier is shown.

## Project Team

Developed by Adwaith P Ajith (2548304) and Mariya K Joby (2548323), under the guidance of Dr. Priya Stella Mary I, Department of Computer Science, CHRIST (Deemed to be University), Bangalore Yeshwanthpur Campus.

## License

This project was developed for academic purposes as part of an M.Sc. Data Science specialization project.
