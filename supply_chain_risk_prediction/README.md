# Aegis - AI-Based Supply Chain Risk Prediction System

Aegis is an end-to-end predictive risk-management and decision-support dashboard for supply chains. It does not simply track shipments—it predicts disruptions before they happen using machine learning and recommends optimal fallback actions (alternate routes, suppliers, or transport modes) to save costs and maintain continuity.

Designed for manufacturing, logistics, retail, and pharmaceutical industries (such as Amazon, Reliance, Tata, or food industries) needing early hazard warnings.

---

## 🌟 Key Features

1. **AI Risk Prediction Console**
   - Simulates delay hazards in real time using Random Forest pipelines trained on historical shipment variables (weather, mode, distance, supplier reliability, highway traffic, fuel price indices, and seasonal loading).
   - Returns a normalized **Risk Score (0-100)**, **Delay Probability (%)**, and **Expected Late Margin (Days)**.
2. **Mitigation Recommendation Engine**
   - Suggests logical re-routing, switching transit modes (e.g. Road to Rail during typhoons), supplier failover sourcing, and warehouse safety-stock buffers based on predictive inputs and active database inventories.
3. **Interactive Threat Simulator**
   - Tests supply chain resilience by injecting global scenarios like *Monsoon Storms*, *Crude Price Spikes*, or *Maritime Port Strikes* to instantly recalculate pipeline hazards.
4. **Supplier Roster & Geopolitics**
   - Monitors vendor reliability scores, historical delay metrics, and active geopolitical risk classifications (Low/Medium/High).
5. **Warehouse Stock & Inventory Matrix**
   - Manages capacity boundaries, triggers warning badges for depots dropping below safety stock parameters, and maintains unified SKU valuations.
6. **Unified Analytics Dashboard**
   - Features responsive visual charts:
     - *Delay Trends*: 6-month line graph of total shipment volumes vs delays.
     - *Delivery Success Ratio*: Proportion of on-time vs delayed finished transits.
     - *Supplier Reliability Benchmark*: Bar chart comparison of vendor efficiency.
     - *Corridor Heatmap*: Grid overview of average days delayed and disruption percentages by route.

---

## 🛠️ Technology Stack

- **Backend Web Server**: Python, Flask (Microframework serving REST APIs & HTML pages)
- **Database Engine**: SQLite (Persistent, relational, embedded database)
- **AI/ML Infrastructure**: Scikit-Learn, Pandas, Numpy, Joblib (Random Forest Classifier & Regressor pipelines)
- **Frontend Design**: Semantic HTML5, Vanilla CSS3 (Custom Glassmorphism theme, CSS variables, keyframe animations), Vanilla JavaScript (AJAX, DOM mutation events)
- **Visual Libraries**: Chart.js (Interactive canvas charts), FontAwesome (Icon typography)

---

## 📂 Repository Structure

```directory
supply_chain_risk_prediction/
│
├── app.py                # Flask Web Server & REST API Gateway
├── database.py           # SQLite database schema, connections, and CRUD helper queries
├── ml_engine.py          # Synthetic data generator, RF training pipelines, and recommender rules
├── seed.py               # Seeds DB with initial supplier, warehouse, inventory, and shipment rows
├── run.py                # Bootstraps the application (seeds DB, trains models, starts server)
├── validate_system.py    # Console checker verifying database schema and ML offline inference
├── requirements.txt      # Python package declarations
├── .gitignore            # Excludes python binaries, local database files, and model dumps
│
├── templates/
│   └── index.html        # Main dashboard SPA template
│
└── static/
    ├── css/
    │   └── style.css     # Glassmorphism dark layout stylesheet
    └── js/
        ├── app.js        # Form controls, page transitions, and scenario scripts
        └── charts.js     # Chart.js initialization and data update binds
```

---

## 🚀 Setup & Installation Instructions

Follow these steps to run Aegis locally on your machine:

### 1. Clone the Repository
```bash
git clone <your-github-repo-url>
cd supply_chain_risk_prediction
```

### 2. Create and Activate a Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize and Start the System
Run the bootstrap file which automatically creates the SQLite database, seeds it with 160 realistic transits, trains the Random Forest classifier/regressor models, and boots up the local server:
```bash
python run.py
```

### 5. Access the Web App
Open your web browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🤖 Machine Learning Model Approach

Aegis implements a dual-stage machine learning system:
1. **Delay Classifier** (`RandomForestClassifier`): Uses variables to output the probability of a shipment arriving late.
2. **Delay Regressor** (`RandomForestRegressor`): Trained specifically on historical late shipments, it predicts the expected duration of the delay (in days).
3. **Risk Scoring Matrix**: Combining the classifier's delay probability, predicted delay duration, supplier past delays, and weather/political hazard weights, the engine computes a normalized Risk Score between 0 and 100.
4. **Dynamic Training**: Adding a new shipment via the dashboard automatically invokes the training pipeline, updating the `.joblib` model binaries with fresh observations in real time.

---

## 🔒 License
Licensed under the [MIT License](LICENSE).
