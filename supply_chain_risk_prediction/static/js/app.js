/* ==========================================================================
   AEGIS SUPPLY CHAIN RISK PREDICTOR - FRONTEND LOGIC
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize components
    initApp();
});

function initApp() {
    // Initialize Chart.js objects
    initCharts();

    // Setup Tab Navigation
    setupNavigation();

    // Fetch initial data
    loadAllData();

    // Setup Form submission handlers
    setupFormHandlers();

    // Setup UI interactivity (collapse panels, slider updates)
    setupUIControls();
}

/* ==========================================================================
   TAB NAVIGATION
   ========================================================================== */
const tabSubtitles = {
    'dashboard': 'Real-time status, predictive risks, and mitigation strategies',
    'suppliers': 'Directory, vendor reliability monitoring, and geopolitical metrics',
    'warehouses': 'Facility details, dynamic safety stock, and inventory matrices',
    'shipments': 'Logistics monitoring, actual transit timelines, and status updates',
    'predictor': 'Machine learning model simulation and automated cargo recommendations',
    'disruptions': 'Active shipping disruptions and global corridor threat simulations'
};

const tabTitles = {
    'dashboard': 'Supply Chain Overview',
    'suppliers': 'Supplier Roster & Geopolitics',
    'warehouses': 'Inventory & Warehouses',
    'shipments': 'Logistics Pipeline',
    'predictor': 'AI Prediction & Simulation Console',
    'disruptions': 'Threat Matrix Simulator'
};

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabViews = document.querySelectorAll('.tab-view');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute('data-tab');

            // Toggle active nav class
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');

            // Toggle active tab view
            tabViews.forEach(view => {
                view.classList.remove('active');
                if (view.id === `tab-${targetTab}`) {
                    view.classList.add('active');
                }
            });

            // Update Header titles
            document.getElementById('current-tab-title').innerText = tabTitles[targetTab];
            document.getElementById('current-tab-subtitle').innerText = tabSubtitles[targetTab];
            
            // Perform context loads
            if (targetTab === 'dashboard') {
                loadDashboardData();
            } else if (targetTab === 'suppliers') {
                loadSuppliers();
            } else if (targetTab === 'warehouses') {
                loadWarehousesAndInventory();
            } else if (targetTab === 'shipments') {
                loadShipments();
            }
        });
    });

    // Header actions quick navigations
    document.getElementById('btn-add-shipment-header').addEventListener('click', () => {
        // Switch tab to shipments and expand form
        const shipmentsNav = document.querySelector('.nav-item[data-tab="shipments"]');
        shipmentsNav.click();
        
        const shipmentPanel = document.getElementById('panel-add-shipment');
        if (!shipmentPanel.classList.contains('open')) {
            document.getElementById('btn-show-add-shipment').click();
        }
    });
}

/* ==========================================================================
   UI CONTROLS & EVENT LISTENERS
   ========================================================================== */
function setupUIControls() {
    // 1. Expandable Panels (Forms)
    setupCollapsePanel('btn-show-add-supplier', 'panel-add-supplier', 'btn-close-supplier-form', 'btn-cancel-supplier');
    setupCollapsePanel('btn-show-add-warehouse', 'panel-add-warehouse', 'btn-close-warehouse-form', 'btn-cancel-warehouse');
    setupCollapsePanel('btn-show-add-inventory', 'panel-add-inventory', 'btn-close-inventory-form', 'btn-cancel-inventory');
    setupCollapsePanel('btn-show-add-shipment', 'panel-add-shipment', 'btn-close-shipment-form', 'btn-cancel-shipment');

    // Set default date picker to today in shipments form
    const dateInput = document.getElementById('ship-date');
    if (dateInput) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }

    // Toggle delay-days visible only if status is Delivered/Delayed in shipments form
    const statusSelect = document.getElementById('ship-status');
    const delayGroup = document.querySelector('.historical-only');
    if (statusSelect && delayGroup) {
        statusSelect.addEventListener('change', () => {
            if (statusSelect.value === 'Delivered' || statusSelect.value === 'Delayed') {
                delayGroup.style.display = 'flex';
            } else {
                delayGroup.style.display = 'none';
            }
        });
    }

    // 2. AI Predictor Sliders values updates
    const distanceSlider = document.getElementById('pred-distance');
    const distanceVal = document.getElementById('pred-distance-val');
    distanceSlider.addEventListener('input', () => {
        distanceVal.innerText = `${distanceSlider.value} km`;
    });

    const fuelSlider = document.getElementById('pred-fuel');
    const fuelVal = document.getElementById('pred-fuel-val');
    fuelSlider.addEventListener('input', () => {
        fuelVal.innerText = `$${parseFloat(fuelSlider.value).toFixed(2)}`;
    });

    // 3. Sidebar Model Retrain Button
    const retrainBtnSidebar = document.getElementById('btn-retrain-sidebar');
    retrainBtnSidebar.addEventListener('click', () => triggerRetraining(retrainBtnSidebar));

    // Dynamic Predictor Supplier selection auto updates
    const predSupplierSelect = document.getElementById('pred-supplier');
    predSupplierSelect.addEventListener('change', () => {
        const option = predSupplierSelect.options[predSupplierSelect.selectedIndex];
        const reliability = option.getAttribute('data-reliability');
        const polRisk = option.getAttribute('data-political');
        const delays = option.getAttribute('data-delays');
        
        document.getElementById('pred-supplier-meta').innerText = 
            `Reliability: ${reliability}% | Geopolitical Risk: ${polRisk} | Delay Ratio: ${Math.round(delays * 100)}%`;
    });
}

function setupCollapsePanel(btnId, panelId, closeBtnId, cancelBtnId) {
    const btn = document.getElementById(btnId);
    const panel = document.getElementById(panelId);
    const closeBtn = document.getElementById(closeBtnId);
    const cancelBtn = document.getElementById(cancelBtnId);

    if (btn && panel) {
        btn.addEventListener('click', () => {
            panel.classList.toggle('open');
        });
    }
    
    const closeAction = () => { panel.classList.remove('open'); };

    if (closeBtn) closeBtn.addEventListener('click', closeAction);
    if (cancelBtn) cancelBtn.addEventListener('click', closeAction);
}

/* ==========================================================================
   DATA LOADING FUNCTIONS
   ========================================================================== */
function loadAllData() {
    loadDashboardData();
    loadSuppliers();
    loadWarehousesAndInventory();
    loadShipments();
    loadDisruptionThreats();
}

// 1. Load Dashboard metrics & charts
function loadDashboardData() {
    fetch('/api/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            // Update Metric Cards
            document.getElementById('stat-total-shipments').innerText = data.stats.total_shipments;
            document.getElementById('stat-delayed-orders').innerText = data.stats.delayed_orders;
            document.getElementById('stat-high-risk-suppliers').innerText = data.stats.high_risk_suppliers;
            document.getElementById('stat-low-stock-warehouses').innerText = data.stats.low_stock_warehouses;
            document.getElementById('stat-weather-alerts').innerText = data.stats.weather_alerts;

            // Update Charts
            updateChartsData(data.charts);

            // Update Route Heatmap table
            const heatmapBody = document.querySelector('#table-route-heatmap tbody');
            heatmapBody.innerHTML = '';
            
            const routes = data.charts.route_risk || [];
            if (routes.length === 0) {
                heatmapBody.innerHTML = '<tr><td colspan="6" class="text-center">No route data available.</td></tr>';
            } else {
                // Sample transport mode options to make list pretty
                const modes = ['Truck', 'Rail', 'Sea', 'Air'];
                routes.forEach(route => {
                    const mode = modes[Math.floor(Math.random() * modes.length)];
                    const delayPct = Math.round(route.delay_pct);
                    
                    let riskStatusClass = 'badge-success';
                    let riskStatusText = 'Low Risk';
                    if (delayPct > 35) {
                        riskStatusClass = 'badge-danger';
                        riskStatusText = 'High Risk';
                    } else if (delayPct > 15) {
                        riskStatusClass = 'badge-warning';
                        riskStatusText = 'Med Risk';
                    }

                    const row = `
                        <tr>
                            <td><strong>${route.origin} &rarr; ${route.destination}</strong></td>
                            <td><i class="fa-solid ${getTransportIcon(mode)}"></i> ${mode}</td>
                            <td>${route.total_trips}</td>
                            <td><strong class="text-indigo">${parseFloat(route.avg_delay_days).toFixed(1)} Days</strong></td>
                            <td>
                                <div class="perf-row">
                                    <span>${delayPct}%</span>
                                </div>
                                <div class="bar-container">
                                    <div class="bar-fill" style="width: ${delayPct}%; background-color: ${getRiskColor(delayPct)}"></div>
                                </div>
                            </td>
                            <td><span class="badge ${riskStatusClass}">${riskStatusText}</span></td>
                        </tr>
                    `;
                    heatmapBody.insertAdjacentHTML('beforeend', row);
                });
            }
        })
        .catch(err => console.error('Error fetching dashboard stats:', err));
}

// 2. Load Suppliers list and populate dropdowns
function loadSuppliers() {
    fetch('/api/suppliers')
        .then(response => response.json())
        .then(suppliers => {
            // Update Suppliers Cards Roster
            const listContainer = document.getElementById('suppliers-list');
            listContainer.innerHTML = '';

            // Update form dropdowns
            const shipSupplierSelect = document.getElementById('ship-supplier');
            const predSupplierSelect = document.getElementById('pred-supplier');

            shipSupplierSelect.innerHTML = '<option value="" disabled selected>Select Supplier...</option>';
            predSupplierSelect.innerHTML = '<option value="" disabled selected>Select Supplier...</option>';

            suppliers.forEach(supplier => {
                // Determine political risk badge
                let politicalBadge = 'badge-success';
                if (supplier.political_risk === 'High') politicalBadge = 'badge-danger';
                else if (supplier.political_risk === 'Medium') politicalBadge = 'badge-warning';

                const card = `
                    <div class="supplier-card">
                        <div class="supplier-card-header">
                            <div class="supplier-details">
                                <h4>${supplier.name}</h4>
                                <p><i class="fa-solid fa-envelope"></i> ${supplier.email || 'N/A'}</p>
                                <p><i class="fa-solid fa-phone"></i> ${supplier.phone || 'N/A'}</p>
                            </div>
                            <span class="badge ${politicalBadge}">${supplier.political_risk} Risk</span>
                        </div>
                        
                        <div class="supplier-perf-stats">
                            <div class="perf-row">
                                <span>Reliability Metric</span>
                                <strong>${supplier.reliability_score}%</strong>
                            </div>
                            <div class="bar-container">
                                <div class="bar-fill" style="width: ${supplier.reliability_score}%; background-color: ${getReliabilityColor(supplier.reliability_score)}"></div>
                            </div>
                            
                            <div class="perf-row mt-2">
                                <span>Past Delays Ratio</span>
                                <strong>${Math.round(supplier.past_delays_ratio * 100)}%</strong>
                            </div>
                            <div class="bar-container">
                                <div class="bar-fill" style="width: ${supplier.past_delays_ratio * 100}%; background-color: var(--color-amber)"></div>
                            </div>
                        </div>

                        <div class="supplier-card-footer">
                            <span>Supplier ID: #${supplier.id}</span>
                            <span>Rating: ${supplier.reliability_score >= 90 ? 'Tier 1 Preferred' : supplier.reliability_score >= 70 ? 'Tier 2 Vetted' : 'Tier 3 Probationary'}</span>
                        </div>
                    </div>
                `;
                listContainer.insertAdjacentHTML('beforeend', card);

                // Add to selects
                const optionHtml = `<option value="${supplier.id}" data-reliability="${supplier.reliability_score}" data-political="${supplier.political_risk}" data-delays="${supplier.past_delays_ratio}">${supplier.name}</option>`;
                shipSupplierSelect.insertAdjacentHTML('beforeend', optionHtml);
                predSupplierSelect.insertAdjacentHTML('beforeend', optionHtml);
            });
            
            // Trigger select update to fill metadata description on default selected index
            if (suppliers.length > 0) {
                predSupplierSelect.selectedIndex = 0;
                predSupplierSelect.dispatchEvent(new Event('change'));
            }
        })
        .catch(err => console.error('Error fetching suppliers:', err));
}

// 3. Load Warehouses & Inventory
function loadWarehousesAndInventory() {
    const warehouseSelects = [
        document.getElementById('inv-warehouse'),
        document.getElementById('ship-warehouse')
    ];

    warehouseSelects.forEach(sel => {
        sel.innerHTML = '<option value="" disabled selected>Select Warehouse...</option>';
    });

    // Load Warehouses Cards
    fetch('/api/warehouses')
        .then(response => response.json())
        .then(warehouses => {
            const whGrid = document.getElementById('warehouses-list');
            whGrid.innerHTML = '';

            warehouses.forEach(wh => {
                const stockPercent = Math.round((wh.current_stock / wh.capacity) * 100);
                const isUnderThreshold = wh.current_stock < wh.min_stock_threshold;
                
                const card = `
                    <div class="warehouse-card">
                        <div class="wh-card-header">
                            <h4>${wh.name}</h4>
                            <span>ID: #${wh.id}</span>
                        </div>
                        <div class="wh-gauge-row">
                            <div class="gauge-line-outer">
                                <div class="gauge-line-fill" style="width: ${Math.min(100, stockPercent)}%; background-color: ${isUnderThreshold ? 'var(--color-red)' : 'var(--color-primary)'}"></div>
                            </div>
                            <strong>${stockPercent}%</strong>
                        </div>
                        <div class="wh-footer ${isUnderThreshold ? 'alert-active' : ''}">
                            <span>Stock: ${wh.current_stock} / ${wh.capacity}</span>
                            <span>${isUnderThreshold ? '<i class="fa-solid fa-triangle-exclamation"></i> Low Stock Alert' : 'Stock level nominal'}</span>
                        </div>
                        <small class="helper-text mt-1 d-block"><i class="fa-solid fa-location-dot"></i> ${wh.location}</small>
                    </div>
                `;
                whGrid.insertAdjacentHTML('beforeend', card);

                // Add to dropdown selects
                const optionHtml = `<option value="${wh.id}">${wh.name}</option>`;
                warehouseSelects.forEach(sel => {
                    sel.insertAdjacentHTML('beforeend', optionHtml);
                });
            });
        })
        .catch(err => console.error('Error fetching warehouses:', err));

    // Load Consolidated Inventory list
    fetch('/api/inventory')
        .then(response => response.json())
        .then(items => {
            const tbody = document.getElementById('inventory-table-body');
            tbody.innerHTML = '';

            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center">No inventory logged. Add stock above.</td></tr>';
            } else {
                items.forEach(item => {
                    const totalAsset = item.quantity * item.unit_cost;
                    const row = `
                        <tr>
                            <td><strong>${item.item_name}</strong></td>
                            <td><i class="fa-solid fa-warehouse text-primary"></i> ${item.warehouse_name}</td>
                            <td><strong class="text-emerald">${item.quantity} Units</strong></td>
                            <td>$${parseFloat(item.unit_cost).toFixed(2)}</td>
                            <td><strong class="text-indigo">$${totalAsset.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</strong></td>
                        </tr>
                    `;
                    tbody.insertAdjacentHTML('beforeend', row);
                });
            }
        })
        .catch(err => console.error('Error fetching inventory:', err));
}

// 4. Load Shipments table list
function loadShipments() {
    fetch('/api/shipments')
        .then(response => response.json())
        .then(shipments => {
            const tbody = document.getElementById('shipments-table-body');
            tbody.innerHTML = '';

            if (shipments.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" class="text-center">No shipments recorded.</td></tr>';
            } else {
                shipments.forEach(ship => {
                    let statusBadge = 'badge-success';
                    if (ship.status === 'Delayed') statusBadge = 'badge-danger';
                    else if (ship.status === 'In Transit') statusBadge = 'badge-warning';

                    const row = `
                        <tr>
                            <td><code class="text-primary font-mono font-bold">${ship.tracking_number}</code></td>
                            <td>${ship.supplier_name}</td>
                            <td><strong>${ship.origin} &rarr; ${ship.destination}</strong></td>
                            <td>${ship.distance_km} km</td>
                            <td><i class="fa-solid ${getTransportIcon(ship.transport_mode)}"></i> ${ship.transport_mode}</td>
                            <td>${ship.departure_date}</td>
                            <td><span class="badge ${statusBadge}">${ship.status}</span></td>
                            <td><span class="text-secondary"><i class="fa-solid ${getWeatherIcon(ship.weather_condition)}"></i> ${ship.weather_condition}</span></td>
                            <td>${ship.traffic_level}</td>
                            <td><strong class="${ship.delay_days > 0 ? 'text-red' : 'text-emerald'}">${ship.delay_days} Days</strong></td>
                        </tr>
                    `;
                    tbody.insertAdjacentHTML('beforeend', row);
                });
            }
        })
        .catch(err => console.error('Error fetching shipments:', err));
}

// 5. Load Disruption threats list
function loadDisruptionThreats() {
    const threatContainer = document.getElementById('active-threats-container');
    threatContainer.innerHTML = '';

    // Create a list of active threats
    const threats = [
        { title: "Monsoon Depression in Arabian Sea", area: "West Coast Transit Corridors", severity: "High Weather Hazard", desc: "Expect heavy delays for standard container trucks travelling to Mumbai." },
        { title: "Borders Customs Congestion", area: "Global Ports", severity: "Medium Operational Hazard", desc: "Clearance delay ranges from 12-24 hours for sea cargo transits." }
    ];

    threats.forEach(t => {
        const item = `
            <div class="threat-item">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <div class="threat-info">
                    <h6>${t.title}</h6>
                    <p>Corridor: <strong>${t.area}</strong></p>
                    <p class="helper-text mt-1 text-secondary">${t.desc}</p>
                    <span class="badge badge-warning mt-2">${t.severity}</span>
                </div>
            </div>
        `;
        threatContainer.insertAdjacentHTML('beforeend', item);
    });
}

/* ==========================================================================
   FORM HANDLING & API POST CALLS
   ========================================================================== */
function setupFormHandlers() {
    // 1. Add Supplier Form Submit
    document.getElementById('form-add-supplier').addEventListener('submit', (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById('sup-name').value,
            email: document.getElementById('sup-email').value,
            phone: document.getElementById('sup-phone').value,
            reliability_score: parseInt(document.getElementById('sup-reliability').value),
            past_delays_ratio: parseFloat(document.getElementById('sup-delays').value),
            political_risk: document.getElementById('sup-political').value
        };

        fetch('/api/suppliers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            showToast("Supplier Registered", `${payload.name} was successfully registered and the AI model has been retrained.`);
            document.getElementById('form-add-supplier').reset();
            document.getElementById('panel-add-supplier').classList.remove('open');
            loadSuppliers();
            loadDashboardData();
        })
        .catch(err => {
            console.error('Error adding supplier:', err);
            showToast("Operation Failed", "Could not register supplier.", true);
        });
    });

    // 2. Add Warehouse Form Submit
    document.getElementById('form-add-warehouse').addEventListener('submit', (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById('wh-name').value,
            location: document.getElementById('wh-location').value,
            capacity: parseInt(document.getElementById('wh-capacity').value),
            min_stock_threshold: parseInt(document.getElementById('wh-threshold').value)
        };

        fetch('/api/warehouses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            showToast("Facility Registered", `${payload.name} has been added to warehouse grids.`);
            document.getElementById('form-add-warehouse').reset();
            document.getElementById('panel-add-warehouse').classList.remove('open');
            loadWarehousesAndInventory();
        })
        .catch(err => {
            console.error('Error adding warehouse:', err);
            showToast("Operation Failed", "Could not add warehouse facility.", true);
        });
    });

    // 3. Adjust Stock Form Submit
    document.getElementById('form-add-inventory').addEventListener('submit', (e) => {
        e.preventDefault();
        const payload = {
            warehouse_id: parseInt(document.getElementById('inv-warehouse').value),
            item_name: document.getElementById('inv-item').value,
            quantity: parseInt(document.getElementById('inv-qty').value),
            unit_cost: parseFloat(document.getElementById('inv-cost').value)
        };

        fetch('/api/inventory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            showToast("Stock Updated", `SKU ${payload.item_name} has been logged/adjusted.`);
            document.getElementById('form-add-inventory').reset();
            document.getElementById('panel-add-inventory').classList.remove('open');
            loadWarehousesAndInventory();
            loadDashboardData();
        })
        .catch(err => {
            console.error('Error updating inventory:', err);
            showToast("Operation Failed", "Could not update inventory metrics.", true);
        });
    });

    // 4. Log Shipment Form Submit
    document.getElementById('form-add-shipment').addEventListener('submit', (e) => {
        e.preventDefault();
        
        const statusVal = document.getElementById('ship-status').value;
        const delayDaysVal = statusVal !== 'In Transit' ? parseInt(document.getElementById('ship-delay-days').value) : 0;
        
        const payload = {
            tracking_number: document.getElementById('ship-tracking').value || null,
            supplier_id: parseInt(document.getElementById('ship-supplier').value),
            warehouse_id: parseInt(document.getElementById('ship-warehouse').value),
            origin: document.getElementById('ship-origin').value,
            destination: document.getElementById('ship-dest').value,
            distance_km: parseFloat(document.getElementById('ship-distance').value),
            transport_mode: document.getElementById('ship-mode').value,
            weather_condition: document.getElementById('ship-weather').value,
            traffic_level: document.getElementById('ship-traffic').value,
            fuel_price: parseFloat(document.getElementById('ship-fuel').value),
            holiday_season: parseInt(document.getElementById('ship-holiday').value),
            departure_date: document.getElementById('ship-date').value,
            status: statusVal,
            delay_days: delayDaysVal,
            delivery_days: statusVal === 'Delivered' ? 3 : null // Mock normal base delivery time
        };

        fetch('/api/shipments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            showToast("Shipment Logged", `Shipment reference code ${data.tracking_number} is registered in active grids.`);
            document.getElementById('form-add-shipment').reset();
            document.getElementById('panel-add-shipment').classList.remove('open');
            // Reset dates
            document.getElementById('ship-date').value = new Date().toISOString().split('T')[0];
            loadShipments();
            loadDashboardData();
        })
        .catch(err => {
            console.error('Error logging shipment:', err);
            showToast("Operation Failed", "Could not log cargo transit details.", true);
        });
    });

    // 5. AI Risk Predictor Form Submit
    document.getElementById('form-ai-predictor').addEventListener('submit', (e) => {
        e.preventDefault();
        
        const supplierSelect = document.getElementById('pred-supplier');
        const selectedOption = supplierSelect.options[supplierSelect.selectedIndex];
        
        const payload = {
            supplier_id: parseInt(supplierSelect.value),
            transport_mode: document.getElementById('pred-mode').value,
            weather_condition: document.getElementById('pred-weather').value,
            traffic_level: document.getElementById('pred-traffic').value,
            distance_km: parseFloat(document.getElementById('pred-distance').value),
            fuel_price: parseFloat(document.getElementById('pred-fuel').value),
            holiday_season: parseInt(document.getElementById('pred-holiday').value),
            // These will be auto-resolved by backend, but we send them just in case
            supplier_reliability: parseFloat(selectedOption.getAttribute('data-reliability')),
            supplier_past_delays: parseFloat(selectedOption.getAttribute('data-delays')),
            political_risk: selectedOption.getAttribute('data-political')
        };

        const predictBtn = document.getElementById('btn-predict-risk');
        const originalText = predictBtn.innerHTML;
        predictBtn.disabled = true;
        predictBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running RF Pipeline...';

        fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(pred => {
            updatePredictorResultsUI(pred);
            predictBtn.disabled = false;
            predictBtn.innerHTML = originalText;
        })
        .catch(err => {
            console.error('Error computing risk prediction:', err);
            predictBtn.disabled = false;
            predictBtn.innerHTML = originalText;
            showToast("Simulation Failed", "AI models failed to compute route parameters.", true);
        });
    });
}

// Retrain model from API
function triggerRetraining(btnElement) {
    const originalHtml = btnElement.innerHTML;
    btnElement.disabled = true;
    btnElement.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Training...';

    fetch('/api/train', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            showToast("AI Retrained", "Scikit-Learn models successfully re-fit on current shipments database.");
            btnElement.disabled = false;
            btnElement.innerHTML = originalHtml;
            loadDashboardData();
        })
        .catch(err => {
            console.error('Error retraining model:', err);
            showToast("Retraining Failed", "Models failed to optimize weights.", true);
            btnElement.disabled = false;
            btnElement.innerHTML = originalHtml;
        });
}

/* ==========================================================================
   UI UPDATERS & INTERACTION HELPERS
   ========================================================================== */
function updatePredictorResultsUI(pred) {
    const riskScore = pred.risk_score;
    const delayProb = pred.delay_probability;
    const delayDays = pred.expected_delay_days;
    const recos = pred.recommendations || [];

    // 1. Update Gauge Circular SVG
    const gaugeCircle = document.getElementById('gauge-fill-circle');
    const riskLabel = document.getElementById('predicted-risk-score');
    const riskBadge = document.getElementById('predicted-risk-level');
    
    // Formula for dashoffset (251.2 total stroke-dasharray)
    const offset = 251.2 - (251.2 * riskScore) / 100;
    gaugeCircle.style.strokeDashoffset = offset;
    
    riskLabel.innerText = `${riskScore}%`;

    // Reset indicator border color
    let strokeColor = 'var(--color-emerald)';
    let badgeClass = 'badge-success';
    let riskLevel = 'Low Risk';

    if (riskScore > 65) {
        strokeColor = 'var(--color-red)';
        badgeClass = 'badge-danger';
        riskLevel = 'High Risk';
    } else if (riskScore > 35) {
        strokeColor = 'var(--color-amber)';
        badgeClass = 'badge-warning';
        riskLevel = 'Medium Risk';
    }

    gaugeCircle.style.stroke = strokeColor;
    
    // Apply styling to gauge glow effect
    const riskGaugeCard = document.getElementById('card-risk-gauge');
    riskGaugeCard.style.boxShadow = `0 10px 30px rgba(${riskScore > 65 ? '239, 68, 68' : riskScore > 35 ? '245, 158, 11' : '16, 185, 129'}, 0.08)`;

    // Update risk badge classes
    riskBadge.className = `badge ${badgeClass}`;
    riskBadge.innerText = riskLevel;

    // 2. Update stats cards
    document.getElementById('predicted-delay-prob').innerText = `${delayProb}%`;
    document.getElementById('prob-progress-bar').style.width = `${delayProb}%`;
    document.getElementById('prob-progress-bar').style.backgroundColor = strokeColor;
    
    document.getElementById('predicted-delay-days').innerText = `${delayDays} ${delayDays === 1 ? 'Day' : 'Days'}`;

    // 3. Update Recommendations list
    const recoListContainer = document.getElementById('recommendation-list-container');
    recoListContainer.innerHTML = '';

    if (recos.length === 0) {
        recoListContainer.innerHTML = `
            <li class="reco-placeholder">
                <i class="fa-solid fa-circle-check text-emerald"></i>
                <p>Standard schedule nominal. No critical risks detected along corridor.</p>
            </li>
        `;
    } else {
        recos.forEach(reco => {
            // Pick an icon based on words in recommendation
            let icon = 'fa-solid fa-circle-nodes';
            if (reco.toLowerCase().includes('rail')) icon = 'fa-solid fa-train-subway';
            else if (reco.toLowerCase().includes('supplier')) icon = 'fa-solid fa-handshake-angle';
            else if (reco.toLowerCase().includes('stock') || reco.toLowerCase().includes('warehouse')) icon = 'fa-solid fa-dolly';
            else if (reco.toLowerCase().includes('route') || reco.toLowerCase().includes('bypass')) icon = 'fa-solid fa-map-location-dot';
            else if (reco.toLowerCase().includes('delay') || reco.toLowerCase().includes('date')) icon = 'fa-solid fa-clock';
            else if (reco.toLowerCase().includes('political') || reco.toLowerCase().includes('insurance')) icon = 'fa-solid fa-building-shield';

            const item = `
                <li>
                    <i class="${icon}"></i>
                    <p>${reco}</p>
                </li>
            `;
            recoListContainer.insertAdjacentHTML('beforeend', item);
        });
    }
}

// Threat matrix scenarios
function simulateDisruption(scenario) {
    const predictorNav = document.querySelector('.nav-item[data-tab="predictor"]');
    
    showToast("Threat Simulated", `Scenario: ${scenario.toUpperCase()} activated. Evaluating predictor corridor...`);
    
    // Switch to Predictor tab to show results
    predictorNav.click();
    
    const modeSelect = document.getElementById('pred-mode');
    const weatherSelect = document.getElementById('pred-weather');
    const trafficSelect = document.getElementById('pred-traffic');
    const distanceSlider = document.getElementById('pred-distance');
    const fuelSlider = document.getElementById('pred-fuel');
    const holidaySelect = document.getElementById('pred-holiday');
    const supplierSelect = document.getElementById('pred-supplier');

    if (scenario === 'monsoon') {
        // Find supplier with mid/low range reliability (Global Tech or Horizon)
        selectOptionByText(supplierSelect, ['Global Tech Parts', 'Horizon Agritech']);
        modeSelect.value = 'Truck';
        weatherSelect.value = 'Storm';
        trafficSelect.value = 'High';
        distanceSlider.value = 1200;
        distanceSlider.dispatchEvent(new Event('input'));
        holidaySelect.value = 0;
    } else if (scenario === 'fuel') {
        selectOptionByText(supplierSelect, ['Apex Logistics Inc.', 'Vanguard Materials']);
        modeSelect.value = 'Truck';
        weatherSelect.value = 'Clear';
        trafficSelect.value = 'Medium';
        fuelSlider.value = 5.50;
        fuelSlider.dispatchEvent(new Event('input'));
        holidaySelect.value = 1;
    } else if (scenario === 'strike') {
        // Port strike
        selectOptionByText(supplierSelect, ['Horizon Agritech', 'Global Tech Parts', 'Synergy Industrial Steel']);
        modeSelect.value = 'Sea';
        weatherSelect.value = 'Light Rain';
        trafficSelect.value = 'High';
        distanceSlider.value = 2100;
        distanceSlider.dispatchEvent(new Event('input'));
        holidaySelect.value = 0;
    }

    // Trigger calculation
    setTimeout(() => {
        document.getElementById('form-ai-predictor').dispatchEvent(new Event('submit'));
    }, 400);
}

function selectOptionByText(selectEl, matchTexts) {
    for (let i = 0; i < selectEl.options.length; i++) {
        const optionText = selectEl.options[i].text.toLowerCase();
        const matches = matchTexts.some(txt => optionText.includes(txt.toLowerCase()));
        if (matches) {
            selectEl.selectedIndex = i;
            selectEl.dispatchEvent(new Event('change'));
            break;
        }
    }
}

// Toast notification trigger
function showToast(title, message, isError = false) {
    const toast = document.getElementById('toast-notification');
    const toastIcon = toast.querySelector('.toast-icon');
    
    document.getElementById('toast-title').innerText = title;
    document.getElementById('toast-message').innerText = message;

    if (isError) {
        toast.style.borderColor = 'var(--color-red)';
        toastIcon.className = 'fa-solid fa-circle-xmark toast-icon';
        toastIcon.style.color = 'var(--color-red)';
    } else {
        toast.style.borderColor = 'var(--color-emerald)';
        toastIcon.className = 'fa-solid fa-circle-check toast-icon';
        toastIcon.style.color = 'var(--color-emerald)';
    }

    toast.classList.remove('hidden');
    
    // Auto collapse toast after 4 seconds
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 4500);
}

/* ==========================================================================
   ICON & COLOR GETTERS
   ========================================================================== */
function getTransportIcon(mode) {
    switch (mode) {
        case 'Truck': return 'fa-truck';
        case 'Rail': return 'fa-train-subway';
        case 'Air': return 'fa-plane-departure';
        case 'Sea': return 'fa-ship';
        default: return 'fa-box';
    }
}

function getWeatherIcon(weather) {
    switch (weather) {
        case 'Clear': return 'fa-sun';
        case 'Light Rain': return 'fa-cloud-sun-rain';
        case 'Heavy Rain': return 'fa-cloud-showers-heavy';
        case 'Snow': return 'fa-snowflake';
        case 'Storm': return 'fa-cloud-bolt';
        default: return 'fa-cloud';
    }
}

function getReliabilityColor(score) {
    if (score >= 90) return 'var(--color-emerald)';
    if (score >= 70) return 'var(--color-indigo)';
    return 'var(--color-red)';
}

function getRiskColor(score) {
    if (score > 65) return 'var(--color-red)';
    if (score > 35) return 'var(--color-amber)';
    return 'var(--color-emerald)';
}
