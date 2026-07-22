import datetime
import random
import sqlite3
import os
from database import DB_PATH, init_db, add_supplier, add_warehouse, add_inventory_item, add_shipment
from ml_engine import generate_synthetic_data

def seed_database():
    print("Initializing Database...")
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM suppliers")
    if cursor.fetchone()[0] > 0:
        print("Database already seeded.")
        conn.close()
        return

    print("Seeding Suppliers...")
    suppliers = [
        ("Apex Logistics Inc.", "contact@apexlogistics.com", "+1-555-0199", 92, 0.08, "Low"),
        ("Global Tech Parts", "sales@globaltechparts.com", "+91-22-5550-1244", 65, 0.35, "Medium"),
        ("Vanguard Materials", "orders@vanguardmaterials.com", "+44-20-7946-0958", 96, 0.04, "Low"),
        ("Horizon Agritech", "support@horizonagri.com", "+61-2-5550-1122", 82, 0.18, "High"),
        ("Synergy Industrial Steel", "info@synergysteel.com", "+49-30-901820", 55, 0.45, "Medium"),
        ("Nexus Pharma Corp", "supply@nexuspharma.com", "+41-44-222-3344", 98, 0.02, "Low")
    ]
    
    supplier_ids = []
    for s in suppliers:
        s_id = add_supplier(s[0], s[1], s[2], s[3], s[4], s[5])
        supplier_ids.append(s_id)

    print("Seeding Warehouses...")
    warehouses = [
        ("Mumbai Distribution Hub", "Mumbai, MH, India", 50000, 0, 5000),
        ("Delhi Logistics Center", "Delhi, NCR, India", 30000, 0, 3000),
        ("Bangalore Tech Depot", "Bangalore, KA, India", 20000, 0, 2000),
        ("Chennai Port Facility", "Chennai, TN, India", 40000, 0, 4000)
    ]
    
    warehouse_ids = []
    for w in warehouses:
        w_id = add_warehouse(w[0], w[1], w[2], w[3], w[4])
        warehouse_ids.append(w_id)

    print("Seeding Inventory...")
    inventory_templates = [
        ("Semiconductor Chips", 1500, 45.0),
        ("High-Grade Steel Sheets", 3000, 120.0),
        ("Active Pharma Ingredients", 800, 350.0),
        ("Packaging Cartons", 12000, 1.5),
        ("Lithium-Ion Battery Packs", 600, 180.0),
        ("Precision Screws & Fasteners", 25000, 0.25)
    ]
    
    for w_id in warehouse_ids:
        # Seed random 3-4 items per warehouse
        chosen_items = random.sample(inventory_templates, k=random.randint(3, 5))
        for item, qty, cost in chosen_items:
            add_inventory_item(w_id, item, random.randint(int(qty*0.5), int(qty*1.5)), cost)

    print("Seeding Shipments (Historical & Active)...")
    # We will generate historical shipments dating back 6 months
    start_date = datetime.date(2026, 1, 15)
    
    transport_modes = ['Truck', 'Rail', 'Air', 'Sea']
    weather_conditions = ['Clear', 'Light Rain', 'Heavy Rain', 'Snow', 'Storm']
    traffic_levels = ['Low', 'Medium', 'High']
    origins = ['Pune', 'Shanghai', 'Frankfurt', 'Sydney', 'Tokyo', 'Munich', 'Ahmedabad', 'Singapore']
    
    # Generate 150 historical shipments and 10 active ones
    for i in range(160):
        sup_id = random.choice(supplier_ids)
        wh_id = random.choice(warehouse_ids)
        
        # Get supplier parameters
        cursor.execute("SELECT reliability_score, past_delays_ratio, political_risk FROM suppliers WHERE id = ?", (sup_id,))
        sup_row = cursor.fetchone()
        rel_score, past_delays, pol_risk = sup_row
        
        # Determine locations
        origin = random.choice(origins)
        wh_name = warehouses[wh_id-1][0]
        destination = wh_name.split()[0] # e.g. "Mumbai"
        
        distance = random.uniform(200, 1500) if destination != 'Mumbai' else random.uniform(100, 800)
        mode = random.choice(transport_modes)
        weather = random.choice(weather_conditions)
        traffic = random.choice(traffic_levels)
        fuel = round(random.uniform(3.0, 4.2), 2)
        
        # Departure date: spread across past 6 months
        days_offset = random.randint(0, 180)
        dep_date = start_date + datetime.timedelta(days=days_offset)
        
        # Holiday season modifier
        is_holiday = 1 if dep_date.month in [11, 12, 1] else 0
        
        tracking_num = f"TRK-{dep_date.strftime('%y%m%d')}-{random.randint(1000, 9999)}"
        
        # Is active or historical
        is_active = i >= 150
        
        if is_active:
            status = 'In Transit'
            delivery_days = None
            delay_days = 0
        else:
            # Decide status based on probabilities similar to ml_engine logic
            prob = 0.05
            # Weather
            weather_mods = {'Clear': 0.0, 'Light Rain': 0.08, 'Heavy Rain': 0.3, 'Snow': 0.25, 'Storm': 0.5}
            prob += weather_mods[weather]
            # Supplier
            prob += (1.0 - (rel_score / 100.0)) * 0.35
            # Transport mode vs weather
            if weather in ['Heavy Rain', 'Storm'] and mode in ['Truck', 'Air']:
                prob += 0.2
            # Traffic
            traffic_mods = {'Low': 0.0, 'Medium': 0.04, 'High': 0.18}
            prob += traffic_mods[traffic]
            # Political
            political_mods = {'Low': 0.0, 'Medium': 0.12, 'High': 0.35}
            prob += political_mods[pol_risk]
            # Distance
            prob += distance / 4000.0
            
            prob = max(0.01, min(0.99, prob))
            
            is_delayed = 1 if random.random() < prob else 0
            
            if is_delayed:
                status = 'Delayed'
                delay_days = random.randint(1, 5)
                if weather in ['Storm', 'Snow']:
                    delay_days += random.randint(1, 3)
            else:
                status = 'Delivered'
                delay_days = 0
                
            # Travel base days
            speed_mods = {'Air': 1, 'Truck': 3, 'Rail': 5, 'Sea': 15}
            base_travel_time = speed_mods[mode] + int(distance / 400.0)
            delivery_days = base_travel_time + delay_days
            
        add_shipment(
            tracking_number=tracking_num,
            supplier_id=sup_id,
            warehouse_id=wh_id,
            origin=origin,
            destination=destination,
            distance_km=round(distance, 1),
            transport_mode=mode,
            status=status,
            weather_condition=weather,
            traffic_level=traffic,
            fuel_price=fuel,
            holiday_season=is_holiday,
            departure_date=dep_date.isoformat(),
            delivery_days=delivery_days,
            delay_days=delay_days
        )
        
    conn.commit()
    conn.close()
    print("Database seeding completed.")

if __name__ == '__main__':
    seed_database()
