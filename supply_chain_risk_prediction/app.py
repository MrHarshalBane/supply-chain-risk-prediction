import os
import random
from flask import Flask, render_template, jsonify, request
import database
import ml_engine

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

# Suppliers API
@app.route('/api/suppliers', methods=['GET', 'POST'])
def handle_suppliers():
    if request.method == 'GET':
        suppliers = database.get_all_suppliers()
        return jsonify(suppliers)
    elif request.method == 'POST':
        data = request.json
        if not data or 'name' not in data:
            return jsonify({"error": "Supplier name is required"}), 400
        
        name = data.get('name')
        email = data.get('email', '')
        phone = data.get('phone', '')
        reliability_score = int(data.get('reliability_score', 100))
        past_delays_ratio = float(data.get('past_delays_ratio', 0.0))
        political_risk = data.get('political_risk', 'Low')
        
        new_id = database.add_supplier(name, email, phone, reliability_score, past_delays_ratio, political_risk)
        
        # Trigger training async or sync since it takes 1 sec
        ml_engine.train_and_save_models()
        
        return jsonify({"message": "Supplier added successfully", "id": new_id}), 201

# Warehouses API
@app.route('/api/warehouses', methods=['GET', 'POST'])
def handle_warehouses():
    if request.method == 'GET':
        warehouses = database.get_all_warehouses()
        return jsonify(warehouses)
    elif request.method == 'POST':
        data = request.json
        if not data or 'name' not in data or 'location' not in data or 'capacity' not in data:
            return jsonify({"error": "Name, location, and capacity are required"}), 400
        
        name = data.get('name')
        location = data.get('location')
        capacity = int(data.get('capacity'))
        min_stock = int(data.get('min_stock_threshold', 100))
        
        new_id = database.add_warehouse(name, location, capacity, 0, min_stock)
        return jsonify({"message": "Warehouse added successfully", "id": new_id}), 201

# Inventory API
@app.route('/api/inventory', methods=['GET', 'POST'])
def handle_inventory():
    if request.method == 'GET':
        items = database.get_all_inventory()
        return jsonify(items)
    elif request.method == 'POST':
        data = request.json
        if not data or 'warehouse_id' not in data or 'item_name' not in data or 'quantity' not in data or 'unit_cost' not in data:
            return jsonify({"error": "warehouse_id, item_name, quantity, and unit_cost are required"}), 400
        
        warehouse_id = int(data.get('warehouse_id'))
        item_name = data.get('item_name')
        quantity = int(data.get('quantity'))
        unit_cost = float(data.get('unit_cost'))
        
        # Check if item exists in this warehouse to update, otherwise insert
        existing_items = database.get_warehouse_inventory(warehouse_id)
        existing_item = next((i for i in existing_items if i['item_name'].lower() == item_name.lower()), None)
        
        if existing_item:
            database.update_inventory_item(existing_item['id'], quantity, unit_cost)
            item_id = existing_item['id']
            msg = "Inventory updated successfully"
        else:
            item_id = database.add_inventory_item(warehouse_id, item_name, quantity, unit_cost)
            msg = "Inventory item added successfully"
            
        return jsonify({"message": msg, "id": item_id}), 200

# Shipments API
@app.route('/api/shipments', methods=['GET', 'POST'])
def handle_shipments():
    if request.method == 'GET':
        shipments = database.get_all_shipments()
        return jsonify(shipments)
    elif request.method == 'POST':
        data = request.json
        required_fields = ['supplier_id', 'warehouse_id', 'origin', 'destination', 'distance_km', 'transport_mode', 'weather_condition', 'traffic_level']
        if not data or not all(k in data for k in required_fields):
            return jsonify({"error": f"Missing required fields. Required: {required_fields}"}), 400
        
        tracking_number = data.get('tracking_number')
        if not tracking_number:
            tracking_number = f"TRK-{random.randint(10, 99)}{random.randint(10, 99)}{random.randint(100, 999)}"
            
        supplier_id = int(data.get('supplier_id'))
        warehouse_id = int(data.get('warehouse_id'))
        origin = data.get('origin')
        destination = data.get('destination')
        distance_km = float(data.get('distance_km'))
        transport_mode = data.get('transport_mode')
        weather_condition = data.get('weather_condition')
        traffic_level = data.get('traffic_level')
        fuel_price = float(data.get('fuel_price', 3.5))
        holiday_season = int(data.get('holiday_season', 0))
        departure_date = data.get('departure_date', '')
        
        # If departure_date is not set, use today
        if not departure_date:
            import datetime
            departure_date = datetime.date.today().isoformat()
            
        status = data.get('status', 'In Transit')
        
        # Check if actual delay is supplied (for historical inputs)
        delay_days = int(data.get('delay_days', 0))
        delivery_days = data.get('delivery_days')
        if delivery_days is not None:
            delivery_days = int(delivery_days)
            
        new_id = database.add_shipment(
            tracking_number=tracking_number,
            supplier_id=supplier_id,
            warehouse_id=warehouse_id,
            origin=origin,
            destination=destination,
            distance_km=distance_km,
            transport_mode=transport_mode,
            status=status,
            weather_condition=weather_condition,
            traffic_level=traffic_level,
            fuel_price=fuel_price,
            holiday_season=holiday_season,
            departure_date=departure_date,
            delivery_days=delivery_days,
            delay_days=delay_days
        )
        
        # Re-train models to incorporate new data
        ml_engine.train_and_save_models()
        
        return jsonify({"message": "Shipment added successfully", "id": new_id, "tracking_number": tracking_number}), 201

# Predict API
@app.route('/api/predict', methods=['POST'])
def predict_risk():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    # Extract supplier details if supplier_id is provided
    supplier_id = data.get('supplier_id')
    reliability = float(data.get('supplier_reliability', 85))
    past_delays = float(data.get('supplier_past_delays', 0.15))
    pol_risk = data.get('political_risk', 'Low')
    
    if supplier_id:
        conn = database.get_db_connection()
        row = conn.execute('SELECT reliability_score, past_delays_ratio, political_risk FROM suppliers WHERE id = ?', (supplier_id,)).fetchone()
        conn.close()
        if row:
            reliability = float(row['reliability_score'])
            past_delays = float(row['past_delays_ratio'])
            pol_risk = row['political_risk']
            
    # Compile input data dictionary for the ML engine
    input_data = {
        'transport_mode': data.get('transport_mode', 'Truck'),
        'weather_condition': data.get('weather_condition', 'Clear'),
        'traffic_level': data.get('traffic_level', 'Medium'),
        'political_risk': pol_risk,
        'distance_km': float(data.get('distance_km', 500)),
        'supplier_reliability': reliability,
        'supplier_past_delays': past_delays,
        'fuel_price': float(data.get('fuel_price', 3.5)),
        'holiday_season': int(data.get('holiday_season', 0)),
        'supplier_id': supplier_id
    }
    
    prediction = ml_engine.predict_shipment_risk(input_data)
    return jsonify(prediction)

# Dashboard Stats API
@app.route('/api/dashboard/stats', methods=['GET'])
def get_stats():
    data = database.get_dashboard_data()
    return jsonify(data)

# Re-train Model API
@app.route('/api/train', methods=['POST'])
def train_model():
    success = ml_engine.train_and_save_models()
    if success:
        return jsonify({"message": "AI Models trained successfully on current shipment records."})
    else:
        return jsonify({"error": "Model training failed"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
