import os
import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
CLASSIFIER_PATH = os.path.join(MODEL_DIR, 'delay_classifier.joblib')
REGRESSOR_PATH = os.path.join(MODEL_DIR, 'delay_regressor.joblib')
DB_PATH = os.path.join(MODEL_DIR, 'supply_chain.db')

CATEGORICAL_FEATURES = ['transport_mode', 'weather_condition', 'traffic_level', 'political_risk']
NUMERIC_FEATURES = ['distance_km', 'supplier_reliability', 'supplier_past_delays', 'fuel_price', 'holiday_season']

def generate_synthetic_data(num_samples=1200):
    """
    Generates realistic historical shipment data with correlations:
    - Storm/Heavy Rain + Truck/Air -> higher delay probability and delay days.
    - High political risk -> higher delay probability.
    - Low supplier reliability -> higher delay probability.
    - High traffic -> minor delays.
    - Higher distance -> slight increase in delay probability.
    """
    np.random.seed(42)
    
    # Categories
    transport_modes = ['Truck', 'Rail', 'Air', 'Sea']
    weather_conditions = ['Clear', 'Light Rain', 'Heavy Rain', 'Snow', 'Storm']
    traffic_levels = ['Low', 'Medium', 'High']
    political_risks = ['Low', 'Medium', 'High']
    
    # Generate random features
    data = {
        'transport_mode': np.random.choice(transport_modes, size=num_samples, p=[0.5, 0.25, 0.15, 0.10]),
        'weather_condition': np.random.choice(weather_conditions, size=num_samples, p=[0.5, 0.25, 0.12, 0.08, 0.05]),
        'traffic_level': np.random.choice(traffic_levels, size=num_samples, p=[0.4, 0.4, 0.2]),
        'political_risk': np.random.choice(political_risks, size=num_samples, p=[0.7, 0.2, 0.1]),
        'distance_km': np.random.uniform(50, 2000, size=num_samples),
        'supplier_reliability': np.random.randint(50, 100, size=num_samples),
        'fuel_price': np.random.uniform(2.8, 4.5, size=num_samples),
        'holiday_season': np.random.choice([0, 1], size=num_samples, p=[0.8, 0.2])
    }
    
    df = pd.DataFrame(data)
    df['supplier_past_delays'] = (100 - df['supplier_reliability']) / 100.0 + np.random.normal(0, 0.05, num_samples)
    df['supplier_past_delays'] = df['supplier_past_delays'].clip(0.0, 1.0)
    
    # Calculate Delay Probability (ground truth simulation)
    # Base probability
    prob = 0.05 
    
    # Weather modifiers
    weather_mods = {'Clear': 0.0, 'Light Rain': 0.1, 'Heavy Rain': 0.35, 'Snow': 0.3, 'Storm': 0.6}
    prob += df['weather_condition'].map(weather_mods)
    
    # Transport mode modifiers based on weather
    # Truck/Air affected more by rain/storm; Rail/Sea affected differently
    for idx, row in df.iterrows():
        mode = row['transport_mode']
        weather = row['weather_condition']
        if weather in ['Heavy Rain', 'Storm']:
            if mode == 'Truck':
                prob.iloc[idx] += 0.2
            elif mode == 'Air':
                prob.iloc[idx] += 0.35
            elif mode == 'Rail':
                prob.iloc[idx] += 0.05 # rail is safer in rain
        elif weather == 'Snow':
            if mode == 'Truck':
                prob.iloc[idx] += 0.3
            elif mode == 'Rail':
                prob.iloc[idx] += 0.1
                
    # Distance modifier
    prob += df['distance_km'] / 4000.0
    
    # Supplier modifiers
    prob += (1.0 - (df['supplier_reliability'] / 100.0)) * 0.4
    
    # Traffic modifier
    traffic_mods = {'Low': 0.0, 'Medium': 0.05, 'High': 0.2}
    prob += df['traffic_level'].map(traffic_mods)
    
    # Political risk modifier
    political_mods = {'Low': 0.0, 'Medium': 0.15, 'High': 0.4}
    prob += df['political_risk'].map(political_mods)
    
    # Holiday modifier
    prob += df['holiday_season'] * 0.15
    
    # Add noise and clip probability
    prob += np.random.normal(0, 0.05, num_samples)
    prob = prob.clip(0.01, 0.99)
    
    # Simulate delays (is_delayed)
    df['is_delayed'] = np.random.binomial(1, prob)
    
    # Simulate actual delay days
    # Base delay days if delayed
    delay_days = np.zeros(num_samples)
    delayed_indices = df['is_delayed'] == 1
    
    # Delay duration factors
    base_delays = np.random.exponential(scale=2.0, size=num_samples) + 1.0
    
    # Heavy weather/storm increases delay length
    weather_days = {'Clear': 0, 'Light Rain': 1, 'Heavy Rain': 3, 'Snow': 4, 'Storm': 6}
    mode_sensitivity = {'Truck': 1.2, 'Rail': 0.8, 'Air': 1.5, 'Sea': 2.0}
    
    for idx in range(num_samples):
        if delayed_indices[idx]:
            w_day = weather_days[df.loc[idx, 'weather_condition']]
            m_sens = mode_sensitivity[df.loc[idx, 'transport_mode']]
            dist_factor = df.loc[idx, 'distance_km'] / 500.0
            
            # Expected delay days
            delay_days[idx] = int(round(base_delays[idx] + (w_day * m_sens) + dist_factor))
            
    df['delay_days'] = delay_days.astype(int)
    
    # Actual delivery days (base delivery days + delay days)
    # Base delivery days: speed depends on transport mode: Air (1-2 days), Truck (2-5 days), Rail (3-7 days), Sea (10-25 days)
    speed_mods = {'Air': 1, 'Truck': 3, 'Rail': 5, 'Sea': 15}
    base_travel_time = df['transport_mode'].map(speed_mods) + (df['distance_km'] / 400.0).astype(int)
    df['delivery_days'] = base_travel_time + df['delay_days']
    
    return df

def train_and_save_models(df=None):
    """Trains the Classifier and Regressor models on historical data and saves them."""
    if df is None:
        # Check if database has shipments to train on
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            try:
                # Query historic shipments with supplier details
                query = '''
                    SELECT s.transport_mode, s.weather_condition, s.traffic_level, 
                           sup.political_risk, s.distance_km, sup.reliability_score as supplier_reliability,
                           sup.past_delays_ratio as supplier_past_delays, s.fuel_price, s.holiday_season,
                           (CASE WHEN s.status = 'Delayed' OR s.delay_days > 0 THEN 1 ELSE 0 END) as is_delayed,
                           s.delay_days
                    FROM shipments s
                    JOIN suppliers sup ON s.supplier_id = sup.id
                '''
                df = pd.read_sql_query(query, conn)
            except Exception as e:
                print(f"Error querying database for training: {e}. Generating synthetic data instead.")
            finally:
                conn.close()
                
        if df is None or len(df) < 50:
            print("Insufficient database data. Training with synthetic data.")
            df = generate_synthetic_data(1200)

    # Features and Target split
    X = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y_class = df['is_delayed']
    y_reg = df['delay_days']

    # Preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES),
            ('num', 'passthrough', NUMERIC_FEATURES)
        ])

    # Classifier pipeline
    clf_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10))
    ])

    # Regressor pipeline (train regressor on samples that were actually delayed to predict delay duration)
    reg_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10))
    ])

    # Fit Classifier
    clf_pipeline.fit(X, y_class)
    
    # Fit Regressor (only on delayed cases to learn actual delay size, or all cases. Let's train on all cases where delay_days > 0)
    df_delayed = df[df['delay_days'] > 0]
    if len(df_delayed) > 10:
        X_reg = df_delayed[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
        y_reg_filtered = df_delayed['delay_days']
        reg_pipeline.fit(X_reg, y_reg_filtered)
    else:
        reg_pipeline.fit(X, y_reg)

    # Save models
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(clf_pipeline, CLASSIFIER_PATH)
    joblib.dump(reg_pipeline, REGRESSOR_PATH)
    print("Models trained and saved successfully.")
    return True

def predict_shipment_risk(input_data):
    """
    input_data: dict containing keys:
      - transport_mode, weather_condition, traffic_level, political_risk
      - distance_km, supplier_reliability, supplier_past_delays, fuel_price, holiday_season
      - supplier_id (optional, used for recommendation lookup)
    
    Returns:
      - risk_score (0-100)
      - delay_probability (0-100%)
      - expected_delay_days (float/int)
      - recommendations (list of strings)
    """
    # Load models
    if not os.path.exists(CLASSIFIER_PATH) or not os.path.exists(REGRESSOR_PATH):
        # Train initial model
        train_and_save_models()
        
    clf = joblib.load(CLASSIFIER_PATH)
    reg = joblib.load(REGRESSOR_PATH)

    # Convert single dictionary input to DataFrame
    df_input = pd.DataFrame([input_data])
    
    # Ensure all required columns exist, fill default values if missing
    for col in CATEGORICAL_FEATURES:
        if col not in df_input.columns:
            df_input[col] = 'Low' if col == 'political_risk' else 'Clear' if col == 'weather_condition' else 'Medium'
            
    for col in NUMERIC_FEATURES:
        if col not in df_input.columns:
            df_input[col] = 100.0 if col == 'supplier_reliability' else 0.0 if col == 'supplier_past_delays' else 3.5 if col == 'fuel_price' else 0

    # Predictions
    # 1. Delay Probability
    prob_arr = clf.predict_proba(df_input[CATEGORICAL_FEATURES + NUMERIC_FEATURES])[0]
    # Class order is typically [0, 1], so probability of delay is index 1
    delay_prob = float(prob_arr[1]) if len(prob_arr) > 1 else float(prob_arr[0])
    
    # 2. Expected Delay Days
    exp_delay_days = float(reg.predict(df_input[CATEGORICAL_FEATURES + NUMERIC_FEATURES])[0])
    # If not classified as delayed, expected delay is close to 0 or scaled down
    if delay_prob < 0.2:
        exp_delay_days = max(0.0, exp_delay_days * (delay_prob / 0.2))
        
    # Round expected delay
    exp_delay_days = round(exp_delay_days, 1)

    # 3. Overall Risk Score (0 to 100)
    # Risk is a combination of delay probability, expected delay duration, supplier past delays, and weather/political risks
    # Normalizing expected delay days: 5+ days is high delay (1.0 factor)
    delay_duration_factor = min(1.0, exp_delay_days / 5.0)
    
    # Supplier factor
    supplier_factor = (100.0 - input_data.get('supplier_reliability', 100.0)) / 100.0
    
    # Weather and political risk weights
    weather_weight = 0.8 if input_data.get('weather_condition') in ['Heavy Rain', 'Snow', 'Storm'] else 0.1
    political_weight = 0.8 if input_data.get('political_risk') == 'High' else 0.3 if input_data.get('political_risk') == 'Medium' else 0.0
    
    risk_score = (delay_prob * 0.45 + delay_duration_factor * 0.25 + supplier_factor * 0.15 + max(weather_weight, political_weight) * 0.15) * 100.0
    risk_score = round(min(100.0, max(0.0, risk_score)), 0)

    # 4. Actionable Recommendations
    recommendations = []
    
    # Weather Recommendations
    weather = input_data.get('weather_condition')
    mode = input_data.get('transport_mode')
    if weather in ['Heavy Rain', 'Storm', 'Snow'] and risk_score > 35:
        if mode == 'Truck':
            recommendations.append("Switch transport mode from Truck to Rail. Rail shipping is significantly less disrupted by heavy precipitation and ground congestion.")
        elif mode == 'Air':
            recommendations.append("Switch transport mode from Air to Rail or Sea. Severe storm/snow forecast introduces airport ground handling delays and potential flight cancellations.")
        recommendations.append(f"Consider delaying departure by 24-48 hours until the {weather} system clears to ensure transit safety.")

    # Supplier Recommendations
    supplier_id = input_data.get('supplier_id')
    supplier_reliability = input_data.get('supplier_reliability', 100)
    
    if (supplier_reliability < 75 or risk_score > 50) and os.path.exists(DB_PATH):
        # Fetch alternate suppliers from DB
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query alternate suppliers with higher reliability
            if supplier_id:
                cursor.execute('''
                    SELECT name, reliability_score, past_delays_ratio FROM suppliers 
                    WHERE id != ? AND reliability_score > ? AND political_risk != 'High'
                    ORDER BY reliability_score DESC LIMIT 2
                ''', (supplier_id, supplier_reliability))
            else:
                cursor.execute('''
                    SELECT name, reliability_score, past_delays_ratio FROM suppliers 
                    WHERE reliability_score > 85 AND political_risk != 'High'
                    ORDER BY reliability_score DESC LIMIT 2
                ''')
            
            alts = cursor.fetchall()
            if alts:
                alt_names = [f"{alt['name']} (Reliability: {alt['reliability_score']}%)" for alt in alts]
                recommendations.append(f"Source inventory from alternative supplier(s) with lower risk profiles: {', '.join(alt_names)}.")
            else:
                recommendations.append("Source from an alternate, pre-vetted local supplier to bypass transit risk.")
            conn.close()
        except Exception as e:
            print(f"Error fetching alt suppliers: {e}")
            recommendations.append("Source from an alternate supplier with a reliability score above 90%.")

    # Inventory Recommendations
    if risk_score > 60:
        recommendations.append("Increase warehouse buffer stock levels at the destination by 15-25% to prevent out-of-stock situations caused by this delayed transit.")

    # Distance / Traffic Recommendations
    traffic = input_data.get('traffic_level')
    if traffic == 'High':
        recommendations.append("Re-route shipment via a secondary non-highway route to bypass heavy urban congestion, or schedule departure during off-peak hours (10:00 PM - 05:00 AM).")

    # Political Risk Recommendation
    pol_risk = input_data.get('political_risk')
    if pol_risk == 'High':
        recommendations.append("High political risk along transit corridors. Purchase transit insurance, verify security protocols, and consider splitting the cargo across multiple smaller shipments.")
        
    # Default recommendation if risk is very low
    if risk_score <= 35:
        recommendations.append("Current route and supplier parameters are nominal. Proceed with standard shipment schedule.")

    return {
        "risk_score": int(risk_score),
        "delay_probability": round(delay_prob * 100, 1),
        "expected_delay_days": exp_delay_days,
        "recommendations": recommendations
    }

if __name__ == '__main__':
    # Test generation and training
    df = generate_synthetic_data(100)
    train_and_save_models(df)
    
    # Test prediction
    test_input = {
        'transport_mode': 'Truck',
        'weather_condition': 'Heavy Rain',
        'traffic_level': 'High',
        'political_risk': 'Low',
        'distance_km': 850.0,
        'supplier_reliability': 70,
        'supplier_past_delays': 0.3,
        'fuel_price': 3.5,
        'holiday_season': 0
    }
    pred = predict_shipment_risk(test_input)
    print("Test Prediction Output:")
    print(pred)
