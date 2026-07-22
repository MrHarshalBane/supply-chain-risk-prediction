import os
import sys
from seed import seed_database
from ml_engine import train_and_save_models
from app import app

def main():
    print("==========================================================")
    print("   AEGIS - AI-BASED SUPPLY CHAIN RISK PREDICTOR SYSTEM   ")
    print("==========================================================")
    
    # 1. Initialize and seed DB
    print("\n[1/3] Setting up SQLite Database & Historical Records...")
    seed_database()
    
    # 2. Train Machine Learning Models
    print("\n[2/3] Executing ML Pipeline (Scikit-Learn Random Forest)...")
    train_and_save_models()
    
    # 3. Start Flask Web Server
    print("\n[3/3] Bootstrapping Flask Backend Server...")
    print("Open http://127.0.0.1:5000 in your web browser to view the system dashboard.")
    print("Press CTRL+C to terminate the server.\n")
    
    # Run the Flask app
    app.run(debug=False, host='127.0.0.1', port=5000)

if __name__ == '__main__':
    main()
