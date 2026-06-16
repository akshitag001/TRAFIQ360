# TRAFIQ360 🚦

**An Event-Driven Congestion Digital Twin & Predictive Operations Platform for Bengaluru Traffic Police (BTP).**

TRAFIQ360 is a comprehensive web-based platform designed specifically for traffic command centers. It bridges the gap between predictive machine learning, real-world Geographic Information Systems (GIS), and operations research to help city authorities plan for, simulate, and mitigate massive traffic disruptions such as VIP movements, IPL matches, and protests.

---

## 🌟 Core Modules and Workflows

TRAFIQ360 is broken down into an intuitive 6-step operational workflow:

### 1. Executive Operations Dashboard & CCTV Intelligence
A high-level telemetry view of the Bengaluru road corridor networks. 
- **Digital Twin:** Displays active blockages, predicted congestion levels, and overall officer resource availability on a real-world map mapping exact OpenStreetMap (OSM) junction curves and road contours.
- **Incident Roster:** Tracks all active incidents and their real-time impact status.
- **CCTV Pipeline:** Live ingestion simulation of real Bengaluru traffic cameras (Silk Board, Hebbal Flyover, Mekhri Circle). Allows operators to verify congestion and extract text data directly into the planning pipeline.

### 2. Traffic Incident Forecast Planner
Before a disruption happens, authorities log the incident parameters here.
- **BTP Upcoming Events Feed:** Integrates directly with Bengaluru Traffic Police advisories (via scraping/API), allowing operators to click "Import" and auto-fill the planner with live city data.
- **Predictive Engine:** Uses serialized machine learning models (XGBoost, LightGBM, Random Forest) to forecast Impact Scores (1-10), Duration, Required Officers, and Road Closure probabilities before the incident happens.

### 3. GIS Operations & Digital Twin
A full-screen interactive Digital Twin of Bengaluru mapping precise road networks.
- Operators can simulate road segments *With* or *Without* officers deployed to observe the real-time effect on congestion scores.
- Nodes represent exact geographic junctions, and edges map to actual road geometries rather than just straight lines, providing true-to-life visualization.

### 4. Advanced Cascade Diversion Simulator
When a road is closed due to a high-impact incident, the system computes the next-best paths while managing secondary spillover congestion.
- **NetworkX Graph Algorithms:** Automatically severs the blocked nodes/corridors from the loaded 24MB Bengaluru OSM graph and computes the `k=3` shortest alternative paths.
- **Secondary Load Scoring:** Employs heuristics to estimate how much extra capacity will be dumped onto backup corridors, proactively warning operators if an alternative route exceeds 40% secondary load.
- Visually draws the blocked segment as a dashed red line and color-codes backup routes (Green, Amber, Gray) on the GIS map.

### 5. Resource Optimization
A mathematical operations module to distribute physical resources (Traffic Police officers and Barricades).
- **PuLP ILP Solver:** Runs an Integer Linear Programming (ILP) algorithm to allocate resources across 14 Bengaluru Traffic Police Stations (TPS) to ensure maximum coverage while minimizing mobilization distances.

### 6. 72h Timeline & Production-Quality Playbook Generator
Generates an operational timeline tracking pre-event staging (24h out), barricade setups (12h out), and officer mobilization (6h out).
- **Production-Quality PDF Export:** An automated reporting engine leveraging `reportlab`, `folium`, and `selenium`.
- Aggregates the ML predictions, SHAP driver analysis, exact ILP resource allocations, and Diversion simulation tables into a professional 5-page PDF document.
- Uses headless Chromium to instantly snap a high-resolution screenshot of the geographic blockages and detours to embed directly into the playbook for on-ground officers.

### 7. Post-Event Learning Pipeline (Feedback Loop)
A system is only as good as its ability to learn from reality.
- **Operational Feedback:** Operators submit the *actual* impact, duration, and resource counts after an event concludes.
- **Approval Queue:** Administrators review the submitted feedback through the Approval Queue tab.
- **Dynamic Retraining:** Once approved, administrators can trigger a model retraining loop directly from the UI. The system appends the real-world feedback to the original training dataset and trains new XGBoost and LightGBM models, logging the decline in RMSE and tracking model versions.

---

## 🧠 Machine Learning Architecture in Detail

TRAFIQ360 relies on a hybrid ensemble of machine learning models trained on historical Bengaluru traffic data (weather conditions, public holidays, time of day, and event causality).

### The Prediction Models
1. **Impact Score (XGBoost Regressor):** Predicts the severity of the congestion on a scale of 1-10.
2. **Expected Duration (LightGBM Regressor):** Forecasts how long the congestion will last in minutes.
3. **Road Closure Probability (Random Forest Classifier):** A binary classifier predicting the likelihood that physical barricading and road closures will be required.

### The Retraining Feedback Loop
Instead of relying on static, decaying models, TRAFIQ360 features a Continuous Integration pipeline for data:
1. When actual event metrics are submitted and approved, they are logged into `data/post_event_feedback.xlsx`.
2. The Admin clicks **"⚡ Retrain Models"**.
3. A background Python thread spins up `scratch/retrain_pipeline.py`.
4. The pipeline merges the historical dataset with the newly acquired ground truth data.
5. The models are re-fitted.
6. The system evaluates the new Mean Squared Error (MSE), Root Mean Squared Error (RMSE), and Area Under Curve (AUC).
7. If the metrics improve, a new model version (e.g., `v1.1`) is compiled, saved, and hot-swapped into production without system downtime.

---

## 🗺️ GIS & OpenStreetMap (OSM) Integration

Initially, maps often connect junctions using simple "as the crow flies" straight lines. TRAFIQ360 implements an advanced `gis_twin.py` script that:
- Queries the Overpass API for Bengaluru's bounding box.
- Downloads the physical road network (highways, trunks, primary roads) and projects it into a local UTM coordinate system.
- Simplifies the network into a routing graph using `osmnx`.
- Traces the actual geographic curves, flyovers, and turns of 31 critical Bengaluru corridors (e.g., Outer Ring Road, Silk Board Junction, Mekhri Circle).
- Pushes these true geometries as GeoJSON paths to the frontend Leaflet maps.

---

## ⚙️ Installation & Running the Platform

### Prerequisites
- Python 3.9+
- Pip package manager

### 1. Install Dependencies
```bash
pip install flask pandas scikit-learn xgboost lightgbm networkx pulp openpyxl requests beautifulsoup4 lxml osmnx reportlab folium selenium
```

### 2. Start the Application
Run the Flask server from the root directory:
```bash
python server.py
```

### 3. Access the Dashboard
Open your web browser and navigate to:
```text
http://127.0.0.1:5000/
```

### 4. Judge Demo Mode
For a quick overview of all features during a presentation, click the **Judge Demo** button in the top right corner of the header. The system will run an automated 6-step walkthrough demonstrating the full power of TRAFIQ360.

---

## 🗂️ Project Structure

- `server.py`: The main Flask backend containing API endpoints and the ML inference logic.
- `index.html`: The single-page application (SPA) frontend utilizing vanilla JS, HTML/CSS, and Leaflet.js.
- `services/`: Contains backend integrations, such as `btp_event_service.py` for fetching live advisories.
- `scratch/`: Contains complex algorithmic implementations such as `gis_twin.py` (OSM graphs) and `retrain_pipeline.py`.
- `data/`: Contains the stateful databases (Excel/CSV) tracking active incidents, audit logs, and post-event feedback.
- `models/`: Directory where the `pickle` and `joblib` machine learning models are serialized.
- `static/`: Contains icons and CSS assets.

*Built for the Smart City Hackathon. Empowering the Bengaluru Traffic Police with proactive intelligence.*
