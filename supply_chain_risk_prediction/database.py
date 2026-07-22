import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'supply_chain.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create suppliers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            reliability_score INTEGER DEFAULT 100,
            past_delays_ratio REAL DEFAULT 0.0,
            political_risk TEXT DEFAULT 'Low'
        )
    ''')
    
    # Create warehouses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            current_stock INTEGER DEFAULT 0,
            min_stock_threshold INTEGER DEFAULT 100
        )
    ''')
    
    # Create shipments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_number TEXT UNIQUE NOT NULL,
            supplier_id INTEGER NOT NULL,
            warehouse_id INTEGER NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            distance_km REAL NOT NULL,
            transport_mode TEXT NOT NULL, -- Truck, Rail, Air, Sea
            status TEXT NOT NULL,         -- In Transit, Delivered, Delayed
            weather_condition TEXT NOT NULL, -- Clear, Light Rain, Heavy Rain, Snow, Storm
            traffic_level TEXT NOT NULL,     -- Low, Medium, High
            fuel_price REAL NOT NULL,
            holiday_season INTEGER DEFAULT 0, -- 0 or 1
            departure_date TEXT NOT NULL,
            delivery_days INTEGER,        -- actual delivery time in days
            delay_days INTEGER DEFAULT 0,  -- delay in days
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
        )
    ''')
    
    # Create inventory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_cost REAL NOT NULL,
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Supplier operations
def add_supplier(name, email, phone, reliability_score=100, past_delays_ratio=0.0, political_risk='Low'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO suppliers (name, email, phone, reliability_score, past_delays_ratio, political_risk)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, email, phone, reliability_score, past_delays_ratio, political_risk))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def get_all_suppliers():
    conn = get_db_connection()
    suppliers = conn.execute('SELECT * FROM suppliers').fetchall()
    conn.close()
    return [dict(s) for s in suppliers]

def update_supplier(supplier_id, reliability_score, past_delays_ratio, political_risk):
    conn = get_db_connection()
    conn.execute('''
        UPDATE suppliers
        SET reliability_score = ?, past_delays_ratio = ?, political_risk = ?
        WHERE id = ?
    ''', (reliability_score, past_delays_ratio, political_risk, supplier_id))
    conn.commit()
    conn.close()

# Warehouse operations
def add_warehouse(name, location, capacity, current_stock=0, min_stock_threshold=100):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO warehouses (name, location, capacity, current_stock, min_stock_threshold)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, location, capacity, current_stock, min_stock_threshold))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def get_all_warehouses():
    conn = get_db_connection()
    warehouses = conn.execute('SELECT * FROM warehouses').fetchall()
    conn.close()
    return [dict(w) for w in warehouses]

def update_warehouse_stock(warehouse_id):
    conn = get_db_connection()
    # Calculate sum of quantity in inventory for this warehouse
    row = conn.execute('SELECT SUM(quantity) as total_stock FROM inventory WHERE warehouse_id = ?', (warehouse_id,)).fetchone()
    total_stock = row['total_stock'] if row['total_stock'] is not None else 0
    
    conn.execute('UPDATE warehouses SET current_stock = ? WHERE id = ?', (total_stock, warehouse_id))
    conn.commit()
    conn.close()

# Inventory operations
def add_inventory_item(warehouse_id, item_name, quantity, unit_cost):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO inventory (warehouse_id, item_name, quantity, unit_cost)
        VALUES (?, ?, ?, ?)
    ''', (warehouse_id, item_name, quantity, unit_cost))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    update_warehouse_stock(warehouse_id)
    return new_id

def get_warehouse_inventory(warehouse_id):
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM inventory WHERE warehouse_id = ?', (warehouse_id,)).fetchall()
    conn.close()
    return [dict(i) for i in items]

def get_all_inventory():
    conn = get_db_connection()
    items = conn.execute('''
        SELECT i.*, w.name as warehouse_name 
        FROM inventory i
        JOIN warehouses w ON i.warehouse_id = w.id
    ''').fetchall()
    conn.close()
    return [dict(i) for i in items]

def update_inventory_item(item_id, quantity, unit_cost):
    conn = get_db_connection()
    row = conn.execute('SELECT warehouse_id FROM inventory WHERE id = ?', (item_id,)).fetchone()
    if row:
        warehouse_id = row['warehouse_id']
        conn.execute('''
            UPDATE inventory
            SET quantity = ?, unit_cost = ?
            WHERE id = ?
        ''', (quantity, unit_cost, item_id))
        conn.commit()
        conn.close()
        update_warehouse_stock(warehouse_id)
        return True
    conn.close()
    return False

# Shipment operations
def add_shipment(tracking_number, supplier_id, warehouse_id, origin, destination, distance_km, transport_mode,
                 status, weather_condition, traffic_level, fuel_price, holiday_season, departure_date,
                 delivery_days=None, delay_days=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO shipments (
            tracking_number, supplier_id, warehouse_id, origin, destination, distance_km, transport_mode,
            status, weather_condition, traffic_level, fuel_price, holiday_season, departure_date,
            delivery_days, delay_days
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tracking_number, supplier_id, warehouse_id, origin, destination, distance_km, transport_mode,
          status, weather_condition, traffic_level, fuel_price, holiday_season, departure_date,
          delivery_days, delay_days))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def get_all_shipments():
    conn = get_db_connection()
    shipments = conn.execute('''
        SELECT s.*, sup.name as supplier_name, w.name as warehouse_name 
        FROM shipments s
        JOIN suppliers sup ON s.supplier_id = sup.id
        JOIN warehouses w ON s.warehouse_id = w.id
        ORDER BY s.id DESC
    ''').fetchall()
    conn.close()
    return [dict(s) for s in shipments]

def update_shipment_status(shipment_id, status, delivery_days=None, delay_days=0):
    conn = get_db_connection()
    conn.execute('''
        UPDATE shipments
        SET status = ?, delivery_days = ?, delay_days = ?
        WHERE id = ?
    ''', (status, delivery_days, delay_days, shipment_id))
    conn.commit()
    conn.close()

# Dashboard Stats Aggregation
def get_dashboard_data():
    conn = get_db_connection()
    
    # 1. Card stats
    total_shipments = conn.execute('SELECT COUNT(*) FROM shipments').fetchone()[0]
    delayed_orders = conn.execute("SELECT COUNT(*) FROM shipments WHERE status = 'Delayed'").fetchone()[0]
    high_risk_suppliers = conn.execute("SELECT COUNT(*) FROM suppliers WHERE reliability_score < 70 OR political_risk = 'High'").fetchone()[0]
    
    # Inventory status (warehouses below threshold)
    low_stock_warehouses = conn.execute("SELECT COUNT(*) FROM warehouses WHERE current_stock < min_stock_threshold").fetchone()[0]
    
    # Weather alerts (Heavy Rain, Snow, Storm in active transit shipments)
    weather_alerts = conn.execute('''
        SELECT COUNT(*) FROM shipments 
        WHERE status = 'In Transit' AND weather_condition IN ('Heavy Rain', 'Snow', 'Storm')
    ''').fetchone()[0]
    
    # 2. Charts data
    # Delay Trends (delayed vs total by month/departure_date)
    # We will aggregate shipments by month. Since date is stored as string 'YYYY-MM-DD', we can extract YYYY-MM
    delay_trends = conn.execute('''
        SELECT substr(departure_date, 1, 7) as month,
               COUNT(*) as total,
               SUM(CASE WHEN status = 'Delayed' OR delay_days > 0 THEN 1 ELSE 0 END) as delayed
        FROM shipments
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    ''').fetchall()
    
    # Supplier Performance (reliability score vs past delays ratio)
    supplier_perf = conn.execute('SELECT name, reliability_score, past_delays_ratio FROM suppliers LIMIT 8').fetchall()
    
    # Monthly delivery success rates
    delivery_success = conn.execute('''
        SELECT substr(departure_date, 1, 7) as month,
               SUM(CASE WHEN status = 'Delivered' AND delay_days = 0 THEN 1 ELSE 0 END) as on_time,
               SUM(CASE WHEN status = 'Delivered' AND delay_days > 0 THEN 1 ELSE 0 END) as delayed_delivered,
               COUNT(*) as total
        FROM shipments
        WHERE status = 'Delivered'
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    ''').fetchall()
    
    # Risk Heatmap details (Group by origin & destination to show average delay days and risk)
    route_risk = conn.execute('''
        SELECT origin, destination, 
               AVG(delay_days) as avg_delay_days,
               COUNT(*) as total_trips,
               SUM(CASE WHEN status = 'Delayed' OR delay_days > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as delay_pct
        FROM shipments
        GROUP BY origin, destination
        LIMIT 10
    ''').fetchall()

    conn.close()
    
    return {
        "stats": {
            "total_shipments": total_shipments,
            "delayed_orders": delayed_orders,
            "high_risk_suppliers": high_risk_suppliers,
            "low_stock_warehouses": low_stock_warehouses,
            "weather_alerts": weather_alerts
        },
        "charts": {
            "delay_trends": [dict(r) for r in reversed(delay_trends)],
            "supplier_perf": [dict(s) for s in supplier_perf],
            "delivery_success": [dict(d) for d in reversed(delivery_success)],
            "route_risk": [dict(r) for r in route_risk]
        }
    }
