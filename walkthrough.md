# TRAFIQ360 Technical Walkthrough

I have implemented a complete, data-driven operational traffic system for the hackathon project, moving away from static prototypes into a fully functional backend intelligence server coupled with a government-grade Command Center UI.

---

## 1. Directory Structure

All components are fully integrated and executable in the workspace:

```text
TRAFIQ360/
├── Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv  # Base dataset
├── server.py                                                              # Flask API Server
├── index.html                                                             # Dispatcher UI Front-end
├── astram-plus.html                                                       # Backup of original file
└── C:\Users\Akshit aggarwal\.gemini\antigravity-ide\brain\ecc1739f-3df3-4ee0-9068-c356b4b61b90/
    ├── eda_report.md                                                      # Detailed EDA Report (Phase 1)
    ├── model_comparison_report.md                                         # Model Benchmark Report (Phase 2)
    ├── models/                                                            # Serialized ML Encoders & Models
    │   ├── best_impact_model.joblib
    │   ├── best_duration_model.joblib
    │   ├── best_closure_model.joblib
    │   ├── label_encoders.joblib
    │   └── cause_means.joblib
    └── scratch/                                                           # Intelligence Scripts
        ├── eda.py
        ├── train_models.py
        ├── gis_twin.py
        ├── optimizer.py
        └── test_endpoints.py
```

---

## 2. Phase Implementations

### Phase 1: Data Understanding & EDA
* File: `eda.py` & [eda_report.md](file:///C:/Users/Akshit%20aggarwal/.gemini/antigravity-ide/brain/ecc1739f-3df3-4ee0-9068-c356b4b61b90/eda_report.md)
* Analyzed missing data, spatial fields, hourly peaks (bimodal peaks at 05:00-07:00 and 19:00-22:00), corridor closure rates, and junction hotspots.

### Phase 2: Predictive Modeling
* File: `train_models.py` & [model_comparison_report.md](file:///C:/Users/Akshit%20aggarwal/.gemini/antigravity-ide/brain/ecc1739f-3df3-4ee0-9068-c356b4b61b90/model_comparison_report.md)
* Trained **XGBoost Regressor** (for composite impact score), **XGBoost Regressor** (for log expected duration in minutes), and **LightGBM Classifier** (for road closure probability).
* Benchmark outcomes:
  - *Impact Score*: XGBoost RMSE ~0.59
  - *Duration (minutes)*: LightGBM / XGBoost MAE ~2309 minutes (long-duration outliers like potholes skewed results, so a log-duration target was chosen).
  - *Road Closure*: LightGBM Classifier ROC-AUC ~0.76.

### Phase 3 & 4: GIS Digital Twin & Diversion Simulation
* File: `gis_twin.py`
* Built a geospatial network graph of Bengaluru using `NetworkX`.
* Edges represent major corridors, nodes represent top junctions with real lat/long.
* Edge weights are based on Haversine distance. When a road is closed, edges are removed, and Dijkstra/K-Shortest Paths are recalculated.
* Diverted traffic is modeled, calculating secondary congestion loads on alternative corridors using a delay function.

### Phase 5: Resource Optimization
* File: `optimizer.py`
* Modeled as an **Integer Linear Programming (ILP)** problem using `PuLP`.
* Objective: Minimize total deployed officers and barricades while heavily penalizing safety requirement deficits (under-deploying resources at high-impact locations).
* Successfully distributes resources and outputs shift rotations based on event duration.

### Phase 6: Conflict Detection
* File: `server.py` (`/api/conflicts`)
* Automatically checks for overlapping events in time, shared corridors, adjacent nodes (junction bottlenecks), and total resource shortages.

### Phase 7: Post-Event Learning Loop
* File: `server.py` (`/api/feedback` & `/api/retrain`)
* Dispatchers can submit feedback (actual impact/duration) which is saved to `feedback_data.csv`. Triggers retraining of model files on demand.

### Phase 8 & 9: Enterprise Command Center & Playbook Exporter
* Files: `index.html` & `server.py` (`/api/playbook/<id>`)
* Replicates the **Q-Shield, Palantir, and ArcGIS Enterprise** clean-spacing, light-theme design system.
* **Unified Map Operations Layout**: GIS Operations (Page 3), Diversion Simulator (Page 4), and Resource Optimization (Page 5) share a persistent fullscreen Leaflet map on the left 75% of the screen, with dynamic sidebar panel tabs switching on the right 25%.
* **Animated Traffic Flow**: When simulating segment closures, the bypass routes are color-coded (Green for free flow, Orange for moderate traffic, Red for congested) and animated dynamically with dash-offset CSS transitions reflecting the BPR deceleration speed.
* **Optimal Allocation Map Overlays**: PuLP solver outputs dynamically project officer and barricade counts onto interactive Leaflet map tooltips when budget sliders are updated.
* **Printable Playbooks**: Generates PDF operational manuals containing the exact ML severity statistics, NetworkX diversion paths, and PuLP resource allocations using `ReportLab`.

---

## 3. How to Run & Verify

1. Open a terminal in the project directory:
   `c:\Users\Akshit aggarwal\Downloads\TRAFIQ360`
2. Start the backend server:
   `python server.py`
3. Open a browser and navigate to:
   `http://localhost:5000`
4. Run the Hackathon Demo Flow:
   - **Step 1 (Dashboard)**: View city telemetries and critical alarms. Click "Start Event Planning Wizard".
   - **Step 2 (Incident Planner)**: Keep default IPL event settings, click "Run Prediction Model & Log" to run XGBoost/LightGBM engines.
   - **Step 3 (GIS Operations)**: View the digital twin map. Click standard nodes to route along actual OpenStreetMap geometries (centerlines and flyovers).
   - **Step 4 (Diversion Simulator)**: Select the logged IPL event. Observe the route segment close, alternate bypass paths calculate, and vehicle flow animate at speed according to congestion.
   - **Step 5 (Resource Optimization)**: Move officer/barricade sliders and watch the PuLP solver recalculate safety coverage. Hover map nodes to view allocated counts in real time.
   - **Step 6 (Timeline & Playbook)**: View the 72h protocol timeline, select the event, and click "Download PDF Playbook" to print the report.
   - **Step 7 (Post-Event Learning)**: Submit resolving feedback to update ML model weights dynamically.
5. All components are tested and verify successfully.
