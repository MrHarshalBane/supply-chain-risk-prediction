/* ==========================================================================
   AEGIS SUPPLY CHAIN RISK PREDICTOR - CHARTS INTEGRATION (LIGHT THEME)
   ========================================================================== */

// Global chart references
let delayTrendsChart = null;
let deliverySuccessChart = null;
let supplierPerfChart = null;

// Chart JS default configuration for light theme
const chartDefaults = {
    color: '#475569', // text-secondary (slate-600)
    font: {
        family: "'Inter', sans-serif",
        size: 11
    },
    gridColor: '#f1f5f9', // light subtle grid
    borderColor: '#e2e8f0'
};

function initCharts() {
    // 1. Shipment Delay & Volume Trends (Line Chart)
    const ctxTrends = document.getElementById('chart-delay-trends').getContext('2d');
    delayTrendsChart = new Chart(ctxTrends, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Total Shipments',
                    data: [],
                    borderColor: '#0284c7', // sky-600
                    backgroundColor: 'rgba(2, 132, 199, 0.08)',
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2,
                    pointBackgroundColor: '#0284c7'
                },
                {
                    label: 'Delayed Orders',
                    data: [],
                    borderColor: '#dc2626', // red-600
                    backgroundColor: 'rgba(220, 38, 38, 0.08)',
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2,
                    pointBackgroundColor: '#dc2626'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: chartDefaults.color, font: chartDefaults.font }
                }
            },
            scales: {
                x: {
                    grid: { color: chartDefaults.gridColor },
                    ticks: { color: chartDefaults.color, font: chartDefaults.font }
                },
                y: {
                    grid: { color: chartDefaults.gridColor },
                    ticks: { color: chartDefaults.color, font: chartDefaults.font, stepSize: 1 },
                    beginAtZero: true
                }
            }
        }
    });

    // 2. Delivery Success Ratio (Doughnut Chart)
    const ctxSuccess = document.getElementById('chart-delivery-success').getContext('2d');
    deliverySuccessChart = new Chart(ctxSuccess, {
        type: 'doughnut',
        data: {
            labels: ['On-Time Deliveries', 'Delayed Deliveries'],
            datasets: [{
                data: [0, 0],
                backgroundColor: [
                    'rgba(22, 163, 74, 0.85)', // emerald-600
                    'rgba(220, 38, 38, 0.85)'   // red-600
                ],
                borderColor: '#ffffff',
                borderWidth: 3,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: chartDefaults.color, font: chartDefaults.font }
                }
            },
            cutout: '70%'
        }
    });

    // 3. Supplier Reliability Benchmark (Bar Chart)
    const ctxSupplier = document.getElementById('chart-supplier-perf').getContext('2d');
    supplierPerfChart = new Chart(ctxSupplier, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Reliability Score (%)',
                data: [],
                backgroundColor: 'rgba(79, 70, 229, 0.8)', // indigo-600
                borderColor: '#4f46e5',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: chartDefaults.color, font: chartDefaults.font }
                },
                y: {
                    grid: { color: chartDefaults.gridColor },
                    ticks: { color: chartDefaults.color, font: chartDefaults.font },
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

function updateChartsData(chartsData) {
    if (!chartsData) return;

    // Update Delay Trends
    const trends = chartsData.delay_trends || [];
    const trendLabels = trends.map(t => t.month);
    const totalData = trends.map(t => t.total);
    const delayedData = trends.map(t => t.delayed);
    
    delayTrendsChart.data.labels = trendLabels;
    delayTrendsChart.data.datasets[0].data = totalData;
    delayTrendsChart.data.datasets[1].data = delayedData;
    delayTrendsChart.update();

    // Update Delivery Success Doughnut
    const deliveries = chartsData.delivery_success || [];
    let totalOnTime = 0;
    let totalDelayed = 0;
    
    deliveries.forEach(d => {
        totalOnTime += d.on_time || 0;
        totalDelayed += d.delayed_delivered || 0;
    });

    // If no deliveries recorded, use default mock splits so it is visual
    if (totalOnTime === 0 && totalDelayed === 0) {
        totalOnTime = 85;
        totalDelayed = 15;
    }
    
    deliverySuccessChart.data.datasets[0].data = [totalOnTime, totalDelayed];
    deliverySuccessChart.update();

    // Update Supplier Performance Bar Chart
    const suppliers = chartsData.supplier_perf || [];
    const supplierLabels = suppliers.map(s => s.name);
    const supplierScores = suppliers.map(s => s.reliability_score);
    
    supplierPerfChart.data.labels = supplierLabels;
    supplierPerfChart.data.datasets[0].data = supplierScores;
    
    // Color code bar chart based on scores (High = Emerald, Med = Indigo, Low = Red)
    const backgroundColors = supplierScores.map(score => {
        if (score >= 90) return 'rgba(22, 163, 74, 0.75)'; // emerald
        if (score >= 70) return 'rgba(79, 70, 229, 0.75)'; // indigo
        return 'rgba(220, 38, 38, 0.75)'; // red
    });
    const borderColors = supplierScores.map(score => {
        if (score >= 90) return '#16a34a';
        if (score >= 70) return '#4f46e5';
        return '#dc2626';
    });
    
    supplierPerfChart.data.datasets[0].backgroundColor = backgroundColors;
    supplierPerfChart.data.datasets[0].borderColor = borderColors;
    supplierPerfChart.update();
}
