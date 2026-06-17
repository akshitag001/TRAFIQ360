---
title: Trafiq360
emoji: 🚦
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# TRAFIQ360
### Event-Driven Congestion Digital Twin & Predictive Operations Platform

TRAFIQ360 is an AI-powered traffic operations platform built for the Bengaluru Traffic Police that predicts the congestion impact of planned and unplanned events, optimally deploys officers using Integer Linear Programming, and simulates real-time road network diversions — all from a single browser dashboard. Unlike passive dashboards, TRAFIQ360 closes the loop: it learns from post-event officer feedback and automatically retrains its ML models to improve future predictions.

---

## System Architecture

```
Dataset (8,173 rows)
     │
     ▼
Feature Engineering  ──►  [XGBoost Impact] [XGBoost Duration] [LightGBM Closure]
     │                              │
     │                       Flask REST API (server.py)
     │                              │
     ├─── OSM Graph (NetworkX) ────►├─── /api/simulate-diversion
     ├─── ILP Optimizer (PuLP) ────►├─── /api/optimize
     ├─── SHAP Explainer ──────────►├─── /api/predict
     ├─── BTP Event Scraper ───────►├─── /api/btp/events
     └─── Model Registry ──────────►└─── /api/model-versions
                                          │
                                    Leaflet.js Frontend (index.html)
                                          │
                              PDF/Excel/CSV Export
```

| Component | Role |
|---|---|
| `server.py` | Flask API — 30+ endpoints; model inference, ILP, graph routing, PDF generation |
| `index.html` | Single-page React-less UI with Leaflet maps, Chart.js graphs, 7 functional tabs |
| `scratch/gis_twin.py` | OSM NetworkX digital twin — junction mapping, k-shortest path routing |
| `scratch/optimizer.py` | PuLP ILP resource allocator — officers + barricades with soft constraints |
| `scratch/retrain_pipeline.py` | Auto-promotes new model versions if AUC improves by ≥0.005 |
| `services/btp_event_service.py` | BTP event scraper with 5 production-quality fallback advisories |
| `data/model_versions.json` | Model registry — version, AUC, RMSE, active status |

---

## Machine Learning Models

| Model | Task | Algorithm | Key Metric | Score |
|---|---|---|---|---|
| Impact Score | Regression (1–10) | XGBoost | RMSE | ~0.42 |
| Duration | Regression (minutes) | XGBoost (log scale) | RMSE | ~18 min |
| Road Closure | Binary Classification | LightGBM | AUC-ROC | ~0.83 |

**Features used:** `event_cause`, `corridor`, `zone`, `junction`, `hour`, `day_of_week`, `event_type`, `priority`, `historical_severity`

**SHAP explainability** is computed for every prediction, returning the top 3 feature contributions with direction (up/down) to the impact score.

---

## Installation

1. `git clone https://github.com/akshitag001/TRAFIQ360.git`
2. `cd TRAFIQ360`
3. `pip install -r requirements.txt`
4. `python server.py`
5. Open `http://127.0.0.1:5000`

> **Note:** The OSM graph file (`data/bengaluru_graph.graphml`, ~24 MB) is included in the repo. First startup takes ~15–20 seconds to load the graph and ML models.

---

## Judge Demo — 6 Step Walkthrough

1. **Forecast tab** → Fill in: Event Cause = `IPL Match (public_event)`, Corridor = `CBD 2`, Hour = `19`, Priority = `High` → Click **"Analyze Impact"** → See impact score, closure probability, SHAP drivers rendered.

2. **Wait 2 seconds** → The prediction result panel shows score in red (≥7) with 3 SHAP feature explanations below.

3. **GIS Digital Twin tab** → Map auto-loads with Bengaluru road network. Click **"Simulate Diversion"** with Origin = `MekhriCircle`, Destination = `SilkBoardJunc` → 3 ranked alternate routes drawn on map with load percentages.

4. **Resources tab** → Adjust officer slider to 30 → Click **"Run ILP Optimization"** → Junction deployment table appears with optimal officer/barricade allocation per junction.

5. **Forecast tab** → Click **"Generate Operational Playbook (PDF)"** → 5-page PDF auto-downloads with cover page, SHAP table, ILP deployment table, diversion routes.

6. **Learning tab** → Click **"Trigger Retraining"** → Progress bar updates every 2 seconds → On completion, new model version appears in the Model Registry chart.

> **Keyboard shortcut:** `Ctrl+D` triggers the judge demo sequence automatically.

---

## API Reference

| Endpoint | Method | Description | Key Inputs | Key Outputs |
|---|---|---|---|---|
| `/api/predict` | POST | ML impact prediction + SHAP | event_cause, corridor, hour | impact_score, closure_prob, duration, shap_drivers |
| `/api/optimize` | POST | ILP resource allocation | corridor, impact_score, available_officers | junction_deployments, total_officers |
| `/api/simulate-diversion` | POST | k-shortest path routing | origin_junction, dest_junction, blocked_corridor | alternate_routes, blocked_segment |
| `/api/detect-conflicts` | POST | Multi-event conflict detection | events[] | conflicts[], severity_summary |
| `/api/generate-playbook` | POST | 5-page PDF playbook | prediction, optimization, diversion | download_url |
| `/api/btp/events` | GET | BTP advisory import | — | events[] with matched junction/corridor |
| `/api/btp/import` | POST | Save event to XLSX | event | success |
| `/api/retrain` | POST | Background model retrain | — | job_id |
| `/api/retrain/status/<id>` | GET | Retrain progress | job_id | status, progress%, message |
| `/api/model-versions` | GET | Registry of all model versions | — | versions[] with AUC/RMSE |
| `/api/active-model` | GET | Currently active model | — | version, metrics |
| `/api/rollback-model` | POST | Hot-swap active model version | version | success |
| `/api/feedback/submit` | POST | Post-event feedback | actual_impact, actual_duration | feedback_id |
| `/api/feedback/list` | GET | All feedback records | — | records[], stats |
| `/api/feedback/approve/<id>` | POST | Approve feedback for training | approver | success |
| `/api/dashboard/summary` | GET | Dashboard summary cards | — | active_incidents, avg_impact |
| `/api/dashboard/hourly` | GET | Hourly event distribution | — | hour→count data |
| `/api/generate-timeline` | GET | Pre-event 72h milestones | event_cause, corridor | milestones[] |
| `/api/system-health` | GET | Model file presence, sizes | — | models dict, active_version |
| `/api/corridors` | GET | Corridor geometry list | — | corridors[] with coordinates |
| `/api/causes` | GET | Unique event causes | — | causes[] |
| `/download/playbook/<file>` | GET | Force-download PDF | filename | PDF binary |
| `/api/incidents` | GET/POST | Active incidents | event data | incidents[] |
| `/api/audit/logs` | GET | Audit trail | — | logs[] |
| `/api/audit/export` | GET | Download audit XLSX | — | Excel file |

---

## Dataset

**Source:** Astram (Bengaluru Traffic Management) — anonymized event records  
**Size:** 8,173 rows × 15+ columns  
**Period:** November 2023 – April 2024  
**City:** Bengaluru, Karnataka, India

**Key features:** `event_cause`, `corridor`, `zone`, `junction`, `start_datetime`, `closed_datetime`, `event_type`, `priority`, `requires_road_closure`, `resolution_mins`

**Computed features:** `hour`, `day_of_week`, `historical_severity` (per-cause mean impact), `calculated_impact_score` (derived from cause severity × time multiplier × closure + duration factors)

---

## Project Structure

```
TRAFIQ360/
├── server.py                    # Flask API — 30+ endpoints, ML inference, PDF gen
├── index.html                   # Single-page frontend — 7 tabs, Leaflet, Chart.js
├── requirements.txt             # Pinned Python dependencies
├── models/
│   ├── best_impact_model.joblib # Active XGBoost impact regressor
│   ├── best_duration_model.joblib
│   ├── best_closure_model.joblib
│   ├── label_encoders.joblib    # Fitted LabelEncoders for all categorical cols
│   ├── cause_means.joblib       # Historical severity per event cause
│   ├── active_version.txt       # Currently active model version string
│   └── xgb_imp_v1.x.pkl        # Versioned model snapshots
├── data/
│   ├── model_versions.json      # Model registry — version, AUC, RMSE, is_active
│   ├── bengaluru_graph.graphml  # OSM road network (NetworkX MultiDiGraph)
│   ├── road_network.geojson     # Corridor geometry for map rendering
│   ├── key_junctions.json       # Junction metadata (lat/lon, degree)
│   ├── post_event_feedback.xlsx # Officer feedback for continuous learning
│   └── audit_log.xlsx           # Full action audit trail
├── scratch/
│   ├── gis_twin.py              # OSM Digital Twin — routing, flow simulation
│   ├── optimizer.py             # PuLP ILP resource allocator
│   ├── retrain_pipeline.py      # Auto-retraining with registry + promotion
│   └── train_models.py          # Initial model training script
├── services/
│   └── btp_event_service.py     # BTP event scraper + normalization
├── playbooks/                   # Generated PDF playbooks (auto-created)
└── static/                      # Icons, CCTV images
```

---

## Known Limitations

The OSM road network is pre-cached (`bengaluru_graph.graphml`) and reflects the road topology at download time — live traffic incidents are not fetched from a real-time source. The CCTV intelligence pipeline uses simulated image inputs with Gemini Vision analysis; a real deployment would require authenticated CCTV feed APIs. Model retraining must be manually triggered from the Learning tab — there is no automated scheduler for production deployment. The ILP solver uses a 3-second time limit to guarantee UI responsiveness; very large officer pools with many junctions may return a proportional fallback rather than the true optimal. SHAP values are computed on the fly and may be slow (~200ms) for the first prediction after server start.

---

## Built for

**Flipkart Grid 7.0 — 2025**  
**Track:** Smart City / Event-Driven Congestion (Planned & Unplanned)  
**Team:** TRAFIQ360
