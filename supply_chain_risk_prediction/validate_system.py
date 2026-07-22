import os
import sqlite3
import joblib

def validate_system():
    print("==========================================")
    print("      AEGIS SYSTEM VALIDATION CHECKER     ")
    print("==========================================")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'supply_chain.db')
    classifier_path = os.path.join(current_dir, 'delay_classifier.joblib')
    regressor_path = os.path.join(current_dir, 'delay_regressor.joblib')
    
    # 1. Check Database File & Schema
    print("\n[1] Checking Database Status...")
    if not os.path.exists(db_path):
        print("FAIL: SQLite Database file 'supply_chain.db' not found. Run seed.py first.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verify tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        required_tables = ['suppliers', 'warehouses', 'shipments', 'inventory']
        
        for table in required_tables:
            if table not in tables:
                print(f"FAIL: Table '{table}' is missing from the database.")
                conn.close()
                return False
            
        print("SUCCESS: Database file exists and has correct table schemas.")
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        sup_cnt = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM warehouses")
        wh_cnt = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM shipments")
        ship_cnt = cursor.fetchone()[0]
        
        print(f"  - Registered Suppliers: {sup_cnt}")
        print(f"  - Registered Warehouses: {wh_cnt}")
        print(f"  - Logged Shipments: {ship_cnt}")
        conn.close()
    except Exception as e:
        print(f"FAIL: Database connection or query failed: {e}")
        return False
        
    # 2. Check AI Models Status
    print("\n[2] Checking Machine Learning Pipelines...")
    if not os.path.exists(classifier_path) or not os.path.exists(regressor_path):
        print("WARNING: ML model pipeline files (.joblib) are missing. Initiating training...")
        try:
            from ml_engine import train_and_save_models
            train_and_save_models()
        except Exception as e:
            print(f"FAIL: Machine learning training failed: {e}")
            return False
            
    if os.path.exists(classifier_path) and os.path.exists(regressor_path):
        print("SUCCESS: ML pipelines loaded successfully.")
    else:
        print("FAIL: Model pipelines could not be found or loaded.")
        return False

    # 3. Test Offline ML Inference
    print("\n[3] Running Sample ML Prediction Checks...")
    try:
        from ml_engine import predict_shipment_risk
        
        test_inputs = [
            {
                # High Risk Scenario
                'transport_mode': 'Truck',
                'weather_condition': 'Storm',
                'traffic_level': 'High',
                'political_risk': 'High',
                'distance_km': 1400.0,
                'supplier_reliability': 55,
                'supplier_past_delays': 0.45,
                'fuel_price': 4.10,
                'holiday_season': 1
            },
            {
                # Nominal Low Risk Scenario
                'transport_mode': 'Rail',
                'weather_condition': 'Clear',
                'traffic_level': 'Low',
                'political_risk': 'Low',
                'distance_km': 450.0,
                'supplier_reliability': 98,
                'supplier_past_delays': 0.02,
                'fuel_price': 3.10,
                'holiday_season': 0
            }
        ]
        
        scenario_names = ["HIGH CORRIDOR HAZARD", "NOMINAL LOW RISK"]
        
        for name, test_input in zip(scenario_names, test_inputs):
            print(f"\nScenario: {name}")
            print(f"  Route: Distance: {test_input['distance_km']} km, Mode: {test_input['transport_mode']}")
            print(f"  Env: Weather: {test_input['weather_condition']}, Traffic: {test_input['traffic_level']}")
            
            result = predict_shipment_risk(test_input)
            
            print(f"  Result Risk Score: {result['risk_score']}%")
            print(f"  Result Delay Prob: {result['delay_probability']}%")
            print(f"  Result Expected Delay Days: {result['expected_delay_days']} days")
            print("  Result Actionable Suggestions:")
            for reco in result['recommendations']:
                print(f"    - {reco}")
                
            assert 0 <= result['risk_score'] <= 100, "Risk score bounds error"
            assert 0 <= result['delay_probability'] <= 100, "Probability bounds error"
            assert result['expected_delay_days'] >= 0, "Delay days bounds error"
            
        print("\nSUCCESS: Inference engine checks passed. Output values are within bounds.")
    except Exception as e:
        print(f"FAIL: ML Inference test failed: {e}")
        return False
        
    print("\n==========================================")
    print("      ALL VALIDATION CHECKS PASSED        ")
    print("==========================================")
    return True

if __name__ == '__main__':
    validate_system()
