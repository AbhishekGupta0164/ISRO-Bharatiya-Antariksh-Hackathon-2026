// --- DOM Elements ---
const btnHome = document.getElementById('btn-home');
const btnRoute = document.getElementById('btn-route');
const btnTraffic = document.getElementById('btn-traffic');
const btnNetwork = document.getElementById('btn-network');
const btnAqi = document.getElementById('btn-aqi');
const btnTasks = document.getElementById('btn-tasks');
const viewHome = document.getElementById('view-home');
const viewRoute = document.getElementById('view-route');
const viewTraffic = document.getElementById('view-traffic');
const viewNetwork = document.getElementById('view-network');
const viewAqi = document.getElementById('view-aqi');
const viewTasks = document.getElementById('view-tasks');

// --- Map Initialization ---
let map = L.map('map').setView([26.0, 80.0], 5);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EAP, and the GIS User Community',
    maxZoom: 18
}).addTo(map);

// Apply cinematic dark filter to the map tiles so glowing paths pop
document.getElementById('map').style.background = '#000';
document.querySelector('#map .leaflet-tile-pane').style.filter = 'brightness(0.35) saturate(0.8) contrast(1.4)';

let currentRouteLayer = null;
let currentShortestRouteLayer = null;
let shortestRouteControlMain = null;
let mapSelectionMode = false;
let mapSelectStage = 0; 
let mapSelectMarkers = [];

// Traffic Engine Map
let mapTraffic = L.map('map-traffic').setView([26.0, 80.0], 5);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EAP, and the GIS User Community',
    maxZoom: 18
}).addTo(mapTraffic);

// Apply cinematic dark filter to the map tiles so glowing paths pop
document.getElementById('map-traffic').style.background = '#000';
document.querySelector('#map-traffic .leaflet-tile-pane').style.filter = 'brightness(0.35) saturate(0.8) contrast(1.4)';

let currentTrafficRouteLayer = null;

const CITY_COORDS = {
    "A": [28.6139, 77.2090], // Delhi
    "B": [26.9124, 75.7873], // Jaipur
    "C": [27.1767, 78.0081], // Agra
    "D": [25.3176, 82.9739], // Varanasi
    "E": [26.8467, 80.9462], // Lucknow
    "F": [22.5726, 88.3639], // Kolkata
    "MUM": [19.0760, 72.8777],
    "BLR": [12.9716, 77.5946],
    "CHN": [13.0827, 80.2707],
    "HYD": [17.3850, 78.4867],
    "PNE": [18.5204, 73.8567],
    "AMD": [23.0225, 72.5714]
};

const CITY_NAMES = {
    "A": "Delhi",
    "B": "Jaipur",
    "C": "Agra",
    "D": "Varanasi",
    "E": "Lucknow",
    "F": "Kolkata",
    "MUM": "Mumbai",
    "BLR": "Bengaluru",
    "CHN": "Chennai",
    "HYD": "Hyderabad",
    "PNE": "Pune",
    "AMD": "Ahmedabad"
};

// --- Global State ---
const CREDIT_RESET_AMOUNT = 1000;
let lastResetDate = localStorage.getItem('econav_last_reset_date');
let todayStr = new Date().toDateString();
let globalCredits;
let initialTripCredits = 0; // Baseline before current trip started

if (lastResetDate !== todayStr) {
    globalCredits = CREDIT_RESET_AMOUNT;
    localStorage.setItem('econav_credits', globalCredits);
    localStorage.setItem('econav_last_reset_date', todayStr);
} else {
    globalCredits = parseInt(localStorage.getItem('econav_credits'));
    if (isNaN(globalCredits)) globalCredits = CREDIT_RESET_AMOUNT;
}

const sleep = ms => new Promise(res => setTimeout(res, ms));

async function animateCredits(start, end) {
    const duration = 500;
    const startTime = performance.now();
    const valObj = document.getElementById('global-credits-val');
    if (!valObj) return;
    
    return new Promise(resolve => {
        function step(now) {
            const progress = Math.min((now - startTime) / duration, 1);
            const current = Math.floor(start + (end - start) * progress);
            valObj.textContent = current;
            updateGlobalCreditsUI(current);
            
            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                resolve();
            }
        }
        requestAnimationFrame(step);
    });
}

function updateGlobalCreditsUI(overrideVal = null) {
    const badge = document.getElementById('global-credit-badge');
    const valObj = document.getElementById('global-credits-val');
    if (!badge || !valObj) return;
    
    const val = overrideVal !== null ? overrideVal : globalCredits;
    valObj.textContent = val;
    
    // Scale indicating depletion of today's health credits
    if (val >= 800) {
        // Green
        badge.style.background = 'rgba(16, 185, 129, 0.1)';
        badge.style.color = '#10b981';
    } else if (globalCredits >= 500) {
        // Light Red / Orange
        badge.style.background = 'rgba(249, 115, 22, 0.1)';
        badge.style.color = '#f97316';
    } else if (globalCredits >= 200) {
        // Red
        badge.style.background = 'rgba(239, 68, 68, 0.1)'; 
        badge.style.color = '#ef4444';
    } else {
        // Dark Red
        badge.style.background = 'rgba(153, 27, 27, 0.2)'; 
        badge.style.color = '#dc2626'; // slightly brighter text for contrast against dark background
    }
}
updateGlobalCreditsUI();
initialTripCredits = globalCredits;

// --- Credit Info Tooltip Click Toggle ---
(function() {
    const btn = document.getElementById('credit-info-toggle');
    const tooltip = document.querySelector('.credit-tooltip');
    if (!btn || !tooltip) return;

    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        tooltip.classList.toggle('visible');
        btn.style.color = tooltip.classList.contains('visible') ? '#34d399' : '';
        btn.style.background = tooltip.classList.contains('visible') ? 'rgba(16,185,129,0.2)' : '';
        btn.style.borderColor = tooltip.classList.contains('visible') ? 'rgba(16,185,129,0.5)' : '';
    });

    // Click outside to dismiss
    document.addEventListener('click', (e) => {
        if (!btn.contains(e.target)) {
            tooltip.classList.remove('visible');
            btn.style.color = '';
            btn.style.background = '';
            btn.style.borderColor = '';
        }
    });
})();

// --- Tab Switching ---
function hideAll() {
    [viewHome, viewRoute, viewTraffic, viewNetwork, viewAqi, viewTasks].forEach(v => {
        v.classList.add('hidden');
        v.classList.remove('animate-in');
    });
    [btnHome, btnRoute, btnTraffic, btnNetwork, btnAqi, btnTasks].forEach(b => b.classList.remove('active'));
}

btnHome.addEventListener('click', () => {
    hideAll();
    viewHome.classList.remove('hidden');
    viewHome.classList.add('animate-in');
    btnHome.classList.add('active');
});

btnRoute.addEventListener('click', () => {
    hideAll();
    viewRoute.classList.remove('hidden');
    viewRoute.classList.add('animate-in');
    btnRoute.classList.add('active');
    setTimeout(() => map.invalidateSize(), 100);
});

btnTraffic.addEventListener('click', () => {
    hideAll();
    viewTraffic.classList.remove('hidden');
    viewTraffic.classList.add('animate-in');
    btnTraffic.classList.add('active');
    setTimeout(() => mapTraffic.invalidateSize(), 100);
});

btnNetwork.addEventListener('click', () => {
    hideAll();
    viewNetwork.classList.remove('hidden');
    viewNetwork.classList.add('animate-in');
    btnNetwork.classList.add('active');
    loadNetworkGraph();
});

btnAqi.addEventListener('click', () => {
    hideAll();
    viewAqi.classList.remove('hidden');
    viewAqi.classList.add('animate-in');
    btnAqi.classList.add('active');
    if (!window.aqiLoaded) loadAqiData();
});

btnTasks.addEventListener('click', () => {
    hideAll();
    viewTasks.classList.remove('hidden');
    viewTasks.classList.add('animate-in');
    btnTasks.classList.add('active');
    if (!window.tasksLoaded) loadTasksData();
});

// --- Normal Route Optimization Logic ---
const btnSubmit = document.getElementById('submit-route');
const routeLoading = document.getElementById('route-loading');
const routeResults = document.getElementById('route-results');
const routeError = document.getElementById('route-error');

async function geocodeCity(name) {
    // If name is already a coordinate string "lat, lon"
    if (name.includes(',')) {
        const parts = name.split(',').map(s => parseFloat(s.trim()));
        if (!parts.some(isNaN)) return parts;
    }
    
    const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(name)}&limit=1`);
    const data = await res.json();
    if (data.length === 0) throw new Error(`City not found: ${name}`);
    return [parseFloat(data[0].lat), parseFloat(data[0].lon)];
}





function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
              Math.sin(dLon/2) * Math.sin(dLon/2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
}



btnSubmit.addEventListener('click', async () => {
    const startStr = document.getElementById('start-node').value.trim();
    const endStr = document.getElementById('end-node').value.trim();
    const routeType = 'full';
    const multiplier = 1.0; 
    
    // UI Reset
    routeResults.classList.add('hidden');
    routeError.classList.add('hidden');
    routeLoading.classList.remove('hidden');

    try {
        let startKey = Object.keys(CITY_NAMES).find(k => CITY_NAMES[k].toLowerCase() === startStr.toLowerCase());
        let endKey = Object.keys(CITY_NAMES).find(k => CITY_NAMES[k].toLowerCase() === endStr.toLowerCase());

        let data = null;

        if (startKey && endKey) {
            // Both inside our 6-node RL environment
            const response = await fetch('/api/v1/eco-route', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start: startKey, end: endKey, traffic_multiplier: multiplier, route_type: routeType })
            });
            
            if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
            data = await response.json();
            
        } else {
            // One or more arbitrary cities! Do custom geocode routing
            const [startLat, startLng] = await geocodeCity(startStr);
            const [endLat, endLng] = await geocodeCity(endStr);
            
            const straightDist = calculateDistance(startLat, startLng, endLat, endLng);
            const seed = ((startStr.charCodeAt(0) || 0) + (endStr.charCodeAt(0) || 0)) % 100;
            const pseudoAqi = 50 + seed; // 50-150 AQI range
            
            let customCoords = [[startLat, startLng], [endLat, endLng]];
            const makeMockAlt = (type, distMult, pollMult) => {
                let mockDist = straightDist * distMult;
                let mockPoll = mockDist * pseudoAqi * pollMult;
                let coords = [[startLat, startLng]];
                if (type === 'medium') {
                    coords.push([(startLat+endLat)/2 + 1.5, (startLng+endLng)/2 + 1.5]);
                } else if (type === 'full') {
                    coords.push([(startLat+endLat)/2 + 2.5, (startLng+endLng)/2 - 2.5]);
                }
                coords.push([endLat, endLng]);
                
                return {
                    type: type,
                    route: coords.map((c, i) => i === 0 ? startStr : (i === coords.length-1 ? endStr : `Detour ${i}`)),
                    custom_coords: coords,
                    total_distance: mockDist,
                    total_pollution: mockPoll,
                    exposure_credits: {
                        final_credit_change: type === 'full' ? 65 : (type === 'medium' ? 25 : -85),
                        overall_grade: type === 'full' ? "A" : (type === 'medium' ? "B" : "D"),
                        overall_emoji: type === 'full' ? "🌟" : (type === 'medium' ? "🟢" : "🔴"),
                        grade_summary: type === 'full' ? "🎉 You earned 65 credits! (Eco Bonus included)" : (type === 'medium' ? "🎉 You earned 25 credits! (Balanced)" : "⚠️ You lost 85 credits. (Shortest Path Penalty applied)"),
                        segments: [
                            {from: startStr, to: endStr, avg_aqi: pseudoAqi, credit_delta: type === 'full' ? 45 : -55, emoji: type === 'full' ? "🌟" : "🔴"}
                        ]
                    }
                };
            };

            const alts = [
                makeMockAlt('shortest', 1.15, 0.05),
                makeMockAlt('medium', 1.25, 0.04),
                makeMockAlt('full', 1.4, 0.035)
            ];

            data = {
                route: [startStr, endStr],
                custom_coords: customCoords,
                total_distance: straightDist,
                total_pollution: straightDist * pseudoAqi * 0.04,
                alternatives: alts,
                custom_routed_fallback: true,
                exposure_credits: alts[2].exposure_credits // Give eco credits by default for global tracker
            };
        }

        renderRouteResults(data);
        
        // Credits are now animated inside renderSegmentsData when an alternative is clicked/selected
        // We just update the internal state here, but the UI update will be handled by the animation
        const creditsEarned = data.exposure_credits.final_credit_change || 0;
        
        // Record baseline (current globalCredits) before applying these specific results
        initialTripCredits = globalCredits; 
        
        // Update the internal state
        globalCredits += creditsEarned;
        localStorage.setItem('econav_credits', globalCredits);
        
        // Note: updateGlobalCreditsUI() is NOT called here anymore; 
        // it's called at the end of the animation in renderSegmentsData.
        
    } catch (err) {
        routeError.textContent = err.message;
        routeError.classList.remove('hidden');
    } finally {
        routeLoading.classList.add('hidden');
    }
});

// --- Traffic Engine Simulator Logic ---
const simSlider = document.getElementById('traffic-level-sim');
const simTrafficVal = document.getElementById('traffic-val-sim');

simSlider.addEventListener('input', (e) => {
    simTrafficVal.textContent = parseFloat(e.target.value).toFixed(1) + 'x';
});

document.getElementById('submit-traffic').addEventListener('click', async () => {
    const start = document.getElementById('traffic-start').value;
    const end = document.getElementById('traffic-end').value;
    const multiplier = parseFloat(simSlider.value);
    
    const resultsPanel = document.getElementById('traffic-results');
    const errText = document.getElementById('traffic-error');
    errText.classList.add('hidden');
    resultsPanel.classList.add('hidden');
    
    try {
        let startKey = Object.keys(CITY_NAMES).find(k => CITY_NAMES[k].toLowerCase() === start.toLowerCase());
        let endKey = Object.keys(CITY_NAMES).find(k => CITY_NAMES[k].toLowerCase() === end.toLowerCase());

        let data = null;

        if (startKey && endKey) {
            const response = await fetch('/api/v1/eco-route', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start: startKey, end: endKey, traffic_multiplier: multiplier })
            });
            if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
            data = await response.json();
            
        } else {
            // Geographic custom routing
            const [startLat, startLng] = await geocodeCity(start);
            const [endLat, endLng] = await geocodeCity(end);
            
            const straightDist = calculateDistance(startLat, startLng, endLat, endLng);
            const mockDist = Math.floor(straightDist * 1.3);
            
            const seed = ((start.charCodeAt(0) || 0) + (end.charCodeAt(0) || 0)) % 100;
            const pseudoAqi = 50 + seed;
            const mockPollution = mockDist * pseudoAqi * 0.04 * multiplier;
            data = {
                route: [start, end],
                custom_coords: [[startLat, startLng], [endLat, endLng]],
                total_distance: mockDist,
                total_pollution: mockPollution,
                exposure_credits: { 
                    grade_summary: "➡️ No credit change. (1 segment)",
                    segments: [{from: start, to: end, avg_aqi: Math.floor(Math.random()*200), emoji: "🚦"}] 
                }
            };
        }
        
        const routeArr = data.route || [];

        // Populate the traffic stats
        const dist = Math.round(data.total_distance || 0);
        const exp = Math.round(data.total_pollution || 0);
        const baseExp = Math.round(exp / multiplier);
        const speed = Math.max(5, Math.round(60 / multiplier)); // Baseline 60km/h
        const timeHrs = (dist / speed).toFixed(1);

        document.getElementById('traffic-res-dist').innerHTML = `📏 <strong>${dist} km</strong>`;
        document.getElementById('traffic-res-base-exp').innerHTML = `🌱 Base Risk: <strong>${baseExp}</strong>`;
        let expColor = multiplier > 1.2 ? '#f43f5e' : (multiplier < 0.8 ? '#10b981' : '#f59e0b');
        document.getElementById('traffic-res-exp').innerHTML = `🚦 Traffic Risk: <strong style="color:${expColor}">${exp}</strong>`;
        document.getElementById('traffic-res-exp').style.borderColor = expColor;

        document.getElementById('traffic-res-speed').textContent = `Avg Speed: ${speed} km/h`;
        document.getElementById('traffic-res-time').textContent = `${timeHrs} hrs`;
        
        // Setup banners
        let bannerColor = multiplier > 1.2 ? '#ef4444' : (multiplier < 0.8 ? '#10b981' : '#f59e0b');
        document.getElementById('traffic-warning-banner').style.background = bannerColor;
        document.getElementById('traffic-multiplier-badge').textContent = `x${multiplier.toFixed(1)} Flow`;
        document.getElementById('traffic-multiplier-badge').style.color = bannerColor;

        // Traffic Credit Summary
        const trafficSummary = document.getElementById('traffic-credit-summary');
        if (trafficSummary) {
            if (data.exposure_credits && data.exposure_credits.grade_summary) {
                trafficSummary.innerHTML = `
                    <div style="display:flex; align-items:center; gap:0.75rem;">
                        <div style="font-size:1.5rem;">${data.exposure_credits.overall_emoji || '🚥'}</div>
                        <div style="font-weight:600; color:#fff; font-size:0.95rem; line-height:1.4;">${data.exposure_credits.grade_summary}</div>
                    </div>
                `;
                trafficSummary.style.display = 'block';
                trafficSummary.style.background = `${bannerColor}11`;
                trafficSummary.style.borderColor = `${bannerColor}33`;
            } else {
                trafficSummary.style.display = 'none';
            }
        }

        // Render Timeline UI
        const tlContainer = document.getElementById('traffic-segment-timeline');
        tlContainer.innerHTML = '';
        if (data.exposure_credits?.segments) {
            let html = '<div style="display:flex; gap:1rem; padding-top:0.5rem; padding-bottom:0.5rem;">';
            data.exposure_credits.segments.forEach((s, i) => {
                let badgeColor = s.avg_aqi > 150 ? '#ef4444' : (s.avg_aqi > 100 ? '#f59e0b' : '#10b981');
                html += `
                    <div style="flex-shrink:0; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); padding:0.75rem; border-radius:8px; min-width:150px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                        <div style="font-size:0.7rem; color:#94a3b8; margin-bottom:0.25rem;">Step ${i+1}: ${CITY_NAMES[s.from]||s.from}</div>
                        <div style="font-weight:bold; font-size:0.9rem; margin-bottom:0.5rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">👉 ${CITY_NAMES[s.to]||s.to}</div>
                        <div style="font-size:0.75rem; display:flex; justify-content:space-between; align-items:center;">
                            <span>AQI:</span>
                            <span style="background:${badgeColor}22; color:${badgeColor}; padding:0.1rem 0.4rem; border-radius:4px; font-weight:800; font-size:0.8rem;">${s.avg_aqi}</span>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            tlContainer.innerHTML = html;
        }
        
        resultsPanel.classList.remove('hidden');
        resultsPanel.classList.add('animate-in');
        
        setTimeout(() => {
            mapTraffic.invalidateSize();
        }, 100);
        
        // Traffic Map Updates
        if (currentTrafficRouteLayer) mapTraffic.removeLayer(currentTrafficRouteLayer);
        if (window.trafficRouteControl) mapTraffic.removeControl(window.trafficRouteControl);
        
        // Determine Map Path Color and Animation Speed
        let mapLineColor = multiplier > 1.2 ? '#ef4444' : (multiplier < 0.8 ? '#10b981' : '#f59e0b');
        let mapLineClass = multiplier > 1.2 ? 'glowing-route glow-red' : (multiplier < 0.8 ? 'glowing-route glow-green' : 'glowing-route glow-orange');
        
        let animSpeed = 1.5 * multiplier; // 0.5x = 0.75s (fast), 3.0x = 4.5s (slow)
        
        // Dynamically inject animation style for this speed
        let styleEl = document.getElementById('dynamic-traffic-style');
        if (!styleEl) {
            styleEl = document.createElement('style');
            styleEl.id = 'dynamic-traffic-style';
            document.head.appendChild(styleEl);
        }
        styleEl.innerHTML = `
            @keyframes trafficFlowAnim {
                to { stroke-dashoffset: -200; }
            }
            .flow-anim-cars {
                animation: trafficFlowAnim ${Math.max(0.5, animSpeed * 3)}s linear infinite;
            }
        `;

        const coords = data.custom_coords ? data.custom_coords : routeArr.map(n => CITY_COORDS[n]).filter(Boolean);
        if (coords.length > 0) {
            currentTrafficRouteLayer = L.featureGroup().addTo(mapTraffic);
            
            window.trafficRouteControl = L.Routing.control({
                waypoints: coords.map(c => L.latLng(c[0], c[1])),
                routeWhileDragging: false,
                addWaypoints: false,
                fitSelectedRoutes: true,
                showAlternatives: false,
                createMarker: function() { return null; },
                lineOptions: {
                    styles: [
                        { className: mapLineClass, weight: 8, color: mapLineColor, opacity: 0.7 },
                        { className: 'flow-anim-cars', weight: 3, color: '#ffffff', opacity: 1, dashArray: '8, 24' }
                    ]
                }
            }).addTo(mapTraffic);
            
            coords.forEach((coord, i) => {
                const isEndpoint = i === 0 || i === coords.length - 1;
                L.circleMarker(coord, {
                    radius: isEndpoint ? 8 : 5,
                    fillColor: isEndpoint ? "#0ea5e9" : mapLineColor,
                    color: "#fff",
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 1
                }).bindTooltip(CITY_NAMES[routeArr[i]] || routeArr[i], {
                    permanent: true, direction: "top", className: 'city-tooltip', offset: [0, -5]
                }).addTo(currentTrafficRouteLayer);
            });
            setTimeout(() => mapTraffic.invalidateSize(), 50);
        }
        
        // Traffic Chart Rendering
        if (data.exposure_credits && data.exposure_credits.segments && data.exposure_credits.segments.length > 0) {
            document.getElementById('traffic-segment-chart-card').style.display = 'block';
            const tCtx = document.getElementById('trafficSegmentChart').getContext('2d');
            if (window.trafficSegmentChartInstance) window.trafficSegmentChartInstance.destroy();

            const tLabels = data.exposure_credits.segments.map(s => `${CITY_NAMES[s.from] || s.from} → ${CITY_NAMES[s.to] || s.to}`);
            const tAqi = data.exposure_credits.segments.map(s => s.avg_aqi);
            const tBaseAqi = tAqi.map(a => Math.round(a / multiplier));

            Chart.defaults.color = '#a1a1aa';
            window.trafficSegmentChartInstance = new Chart(tCtx, {
                type: 'bar',
                data: {
                    labels: tLabels,
                    datasets: [
                        {
                            label: 'Traffic-Inflated AQI Risk',
                            data: tAqi,
                            backgroundColor: 'rgba(244, 63, 94, 0.8)'
                        },
                        {
                            label: 'Base AQI (No Traffic)',
                            data: tBaseAqi,
                            backgroundColor: 'rgba(16, 185, 129, 0.4)'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        } else {
            const trfChart = document.getElementById('traffic-segment-chart-card');
            if (trfChart) trfChart.style.display = 'none';
        }
        
    } catch (err) {
        errText.textContent = err.message;
        errText.classList.remove('hidden');
    }
});

async function renderSegmentsData(credits, routeArr) {
    const summaryContainer = document.getElementById('credit-summary-container');
    const segContainer = document.getElementById('segment-container');
    if (!segContainer) return;

    // Clear previous
    segContainer.innerHTML = '';
    if (summaryContainer) summaryContainer.style.display = 'none';

    // Get current display value to start animation from
    // Always start from initialTripCredits to ensure clicking alternatives doesn't stack deductions
    let displayVal = initialTripCredits;
    updateGlobalCreditsUI(displayVal);

    if (summaryContainer && credits && credits.grade_summary) {
        summaryContainer.innerHTML = `
            <div style="display:flex; align-items:center; gap:0.75rem;">
                <div style="font-size:1.5rem;">${credits.overall_emoji || '📊'}</div>
                <div style="font-weight:600; color:#fff; font-size:0.95rem; line-height:1.4;">${credits.grade_summary}</div>
            </div>
        `;
        summaryContainer.style.display = 'block';
        
        // Adjust background color based on credits
        if (credits.final_credit_change > 0) {
            summaryContainer.style.background = 'rgba(16, 185, 129, 0.1)';
            summaryContainer.style.borderColor = 'rgba(16, 185, 129, 0.2)';
        } else if (credits.final_credit_change < 0) {
            summaryContainer.style.background = 'rgba(239, 68, 68, 0.1)';
            summaryContainer.style.borderColor = 'rgba(239, 68, 68, 0.2)';
        } else {
            summaryContainer.style.background = 'rgba(148, 163, 184, 0.1)';
            summaryContainer.style.borderColor = 'rgba(148, 163, 184, 0.2)';
        }
    }

    if (credits && credits.segments) {
        // Sequentially render segments and animate credits
        for (const s of credits.segments) {
            const segSign = s.credit_delta > 0 ? '+' : '';
            const row = document.createElement('div');
            row.className = 'animate-in'; // Apply entrance animation
            row.style.display = 'flex';
            row.style.justifyContent = 'space-between';
            row.style.padding = '0.75rem';
            row.style.background = 'rgba(0,0,0,0.2)';
            row.style.borderRadius = '8px';
            row.style.fontSize = '0.9rem';
            row.style.borderLeft = `4px solid ${s.credit_delta >= 0 ? '#10b981' : '#f43f5e'}`;
            
            row.innerHTML = `
                <div style="font-weight:600; color: #e2e8f0;">${CITY_NAMES[s.from] || s.from} → ${CITY_NAMES[s.to] || s.to}</div>
                <div style="color: #94a3b8;">AQI: ${s.avg_aqi}</div>
                <div style="color: ${s.credit_delta >= 0 ? '#10b981' : '#f43f5e'}; font-weight:600;">
                    ${s.emoji} ${segSign}${s.credit_delta}
                </div>
            `;
            segContainer.appendChild(row);
            
            // Animate global credit change for this segment
            const targetVal = displayVal + s.credit_delta;
            await animateCredits(displayVal, targetVal);
            displayVal = targetVal;
            
            await sleep(300); // Small pause between segments
        }
        
        // Final Eco Bonus Animation
        if (credits.eco_bonus > 0) {
            const bonusRow = document.createElement('div');
            bonusRow.className = 'animate-in';
            bonusRow.style = 'display:flex; justify-content:space-between; padding:0.75rem; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.2); border-radius:8px; font-size:0.9rem; font-weight:bold; color:#10b981; margin-top:0.5rem;';
            bonusRow.innerHTML = `
                <div>✨ Eco-conscious Choice Bonus</div>
                <div>+${credits.eco_bonus}</div>
            `;
            segContainer.appendChild(bonusRow);
            
            const finalVal = displayVal + credits.eco_bonus;
            await animateCredits(displayVal, finalVal);
            displayVal = finalVal;
        }
    }

    // Ensure the UI is perfectly synced with global state at the end
    updateGlobalCreditsUI();

    if (credits && credits.segments && credits.segments.length > 0) {
        document.getElementById('route-segment-chart-card').style.display = 'block';
        const ctxRoute = document.getElementById('routeSegmentChart').getContext('2d');
        if (window.routeSegmentChartInstance) window.routeSegmentChartInstance.destroy();

        const rLabels = credits.segments.map(s => `${CITY_NAMES[s.from] || s.from} → ${CITY_NAMES[s.to] || s.to}`);
        const rAqi = credits.segments.map(s => s.avg_aqi);
        const rDist = credits.segments.map(s => s.distance || 0);

        Chart.defaults.color = '#a1a1aa';
        window.routeSegmentChartInstance = new Chart(ctxRoute, {
            type: 'bar',
            data: {
                labels: rLabels,
                datasets: [
                    { label: 'Avg AQI Risk', data: rAqi, backgroundColor: 'rgba(244, 63, 94, 0.7)', yAxisID: 'y' },
                    { type: 'line', label: 'Distance (km)', data: rDist, borderColor: '#0ea5e9', backgroundColor: 'rgba(14, 165, 233, 0.2)', borderWidth: 2, tension: 0.3, yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } }, y1: { position: 'right', grid: { drawOnChartArea: false }, beginAtZero: true }, x: { grid: { display: false } } }
            }
        });
    } else {
        const segChart = document.getElementById('route-segment-chart-card');
        if (segChart) segChart.style.display = 'none';
    }
}

function renderRouteResults(data) {
    const routeArr = data.route || [];
    const shortestArr = data.shortest_route || [];

    // Map Updates - Clear previous
    if (window.routeLayers) {
        window.routeLayers.forEach(l => map.removeLayer(l));
    } else {
        if (typeof currentRouteLayer !== 'undefined' && currentRouteLayer) map.removeLayer(currentRouteLayer);
        if (typeof currentShortestRouteLayer !== 'undefined' && currentShortestRouteLayer) map.removeLayer(currentShortestRouteLayer);
    }
    if (window.routeControls) {
        window.routeControls.forEach(c => map.removeControl(c));
    } else {
        if (typeof window.routeControlMain !== 'undefined' && window.routeControlMain) map.removeControl(window.routeControlMain);
        if (typeof shortestRouteControlMain !== 'undefined' && shortestRouteControlMain) map.removeControl(shortestRouteControlMain);
    }
    window.routeLayers = [];
    window.routeControls = [];
    
    if (data.alternatives && data.alternatives.length > 0) {
        // Sort alternatives: full (eco) always first, so it never gets dropped as a duplicate
        data.alternatives.sort((a, b) => {
            const order = { 'full': 1, 'medium': 2, 'shortest': 3 };
            return (order[a.type] || 4) - (order[b.type] || 4);
        });

        const uniquePaths = new Set();
        data.alternatives.forEach((alt, idx) => {
            const pathStr = JSON.stringify(alt.route);
            if (uniquePaths.has(pathStr)) return;
            uniquePaths.add(pathStr);

            const coords = alt.custom_coords ? alt.custom_coords : alt.route.map(n => CITY_COORDS[n]).filter(Boolean);
            if (coords.length > 0) {
                const layer = L.featureGroup(); // Do NOT addTo map immediately, we only add the first (selected) one
                window.routeLayers.push(layer);

                let color = '#10b981'; // Green for full eco
                let weight = 7;
                let className = 'glowing-route route-path-' + alt.type;
                let opacity = 1;
                let dashArray = '';

                if (alt.type === 'shortest') {
                    color = '#ef4444'; // Red
                    weight = 4;
                    className = 'glowing-route-shortest route-path-' + alt.type;
                    opacity = 0.7;
                    dashArray = '5, 10';
                } else if (alt.type === 'medium') {
                    color = '#f59e0b'; // Orange
                    weight = 5;
                    className = 'glowing-route route-path-' + alt.type;
                    opacity = 0.9;
                }

                const ctrl = L.Routing.control({
                    waypoints: coords.map(c => L.latLng(c[0], c[1])),
                    routeWhileDragging: false,
                    addWaypoints: false,
                    fitSelectedRoutes: alt.type === 'full',
                    showAlternatives: false,
                    createMarker: function() { return null; },
                    lineOptions: {
                        styles: [{ className, weight, color, opacity, dashArray }]
                    }
                }).addTo(map);
                window.routeControls.push(ctrl);

                coords.forEach((coord, i) => {
                    const isEndpoint = i === 0 || i === coords.length - 1;
                    L.circleMarker(coord, {
                        radius: isEndpoint ? 8 : 5,
                        fillColor: isEndpoint ? "#0ea5e9" : color,
                        color: "#fff",
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 1
                    }).bindTooltip(CITY_NAMES[alt.route[i]] || alt.route[i], {
                        permanent: true, 
                        direction: "top", 
                        className: 'city-tooltip',
                        offset: [0, -5]
                    }).addTo(layer);
                });
            }
        });
    } else {
        // Fallback for custom routing
        const ecoCoords = data.custom_coords ? data.custom_coords : routeArr.map(n => CITY_COORDS[n]).filter(Boolean);
        if (ecoCoords.length > 0) {
            const layer = L.featureGroup().addTo(map);
            window.routeLayers.push(layer);
            
            const ctrl = L.Routing.control({
                waypoints: ecoCoords.map(c => L.latLng(c[0], c[1])),
                routeWhileDragging: false,
                addWaypoints: false,
                fitSelectedRoutes: true,
                showAlternatives: false,
                createMarker: function() { return null; },
                lineOptions: {
                    styles: [{ className: 'glowing-route', weight: 7, color: '#10b981', opacity: 1 }]
                }
            }).addTo(map);
            window.routeControls.push(ctrl);
            
            ecoCoords.forEach((coord, i) => {
                const isEndpoint = i === 0 || i === ecoCoords.length - 1;
                L.circleMarker(coord, {
                    radius: isEndpoint ? 8 : 5,
                    fillColor: isEndpoint ? "#0ea5e9" : "#10b981",
                    color: "#fff",
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 1
                }).bindTooltip(CITY_NAMES[routeArr[i]] || routeArr[i], {permanent: i === 0, direction: "top"}).addTo(layer);
            });
        }
        
        if (shortestArr.length > 0 && (JSON.stringify(routeArr) !== JSON.stringify(shortestArr))) {
            const shortCoords = shortestArr.map(n => CITY_COORDS[n]).filter(Boolean);
            if (shortCoords.length > 0) {
                const layer = L.featureGroup().addTo(map);
                window.routeLayers.push(layer);
                
                const ctrl = L.Routing.control({
                    waypoints: shortCoords.map(c => L.latLng(c[0], c[1])),
                    routeWhileDragging: false,
                    addWaypoints: false,
                    fitSelectedRoutes: false,
                    showAlternatives: false,
                    createMarker: function() { return null; },
                    lineOptions: {
                        styles: [{ className: 'glowing-route-shortest', weight: 4, color: '#ef4444', opacity: 0.7, dashArray: '5, 10' }]
                    }
                }).addTo(map);
                window.routeControls.push(ctrl);

                shortCoords.forEach((coord, i) => {
                    const isEndpoint = i === 0 || i === shortCoords.length - 1;
                    if (!isEndpoint) {
                        L.circleMarker(coord, {
                            radius: 3,
                            fillColor: "#ef4444",
                            color: "#fff",
                            weight: 1,
                            opacity: 0.6,
                            fillOpacity: 0.6
                        }).addTo(layer);
                    }
                });
            }
        }
    }

    // Render Alternatives in Sidebar
    const container = document.getElementById('route-alternatives-container');
    if (container) {
        container.innerHTML = '';
        if (data.alternatives && data.alternatives.length > 0) {
            const shortestAlt = data.alternatives.find(a => a.type === 'shortest') || data.alternatives[0];
            const baseDist = shortestAlt.total_distance;
            const basePoll = shortestAlt.total_pollution;
        
            const uniquePathsUI = new Set();
            let currentLayerIdx = 0;
            data.alternatives.forEach((alt, idx) => {
                const pathStr = JSON.stringify(alt.route);
                if (uniquePathsUI.has(pathStr)) return;
                uniquePathsUI.add(pathStr);
                
                const thisLayerIdx = currentLayerIdx;
                currentLayerIdx++;

                const div = document.createElement('div');
                div.className = 'card-inner';
                let bg = 'rgba(16, 185, 129, 0.05)';
                let border = 'rgba(16, 185, 129, 0.2)';
                let textCol = '#10b981';
                let title = '🌿 Eco Route (Low AQI)';

                if (alt.type === 'shortest') {
                    bg = 'rgba(239, 68, 68, 0.05)';
                    border = 'rgba(239, 68, 68, 0.2)';
                    textCol = '#ef4444';
                    title = '🏎 Shortest Path';
                } else if(alt.type === 'medium') {
                    bg = 'rgba(245, 158, 11, 0.05)';
                    border = 'rgba(245, 158, 11, 0.2)';
                    textCol = '#f59e0b';
                    title = '⚖️ Balanced Route';
                }

                let crd = alt.exposure_credits?.final_credit_change || 0;
                let grade = alt.exposure_credits?.overall_grade || '?';
                let emoji = alt.exposure_credits?.overall_emoji || '⚪';

                let diffDist = Math.round(alt.total_distance - baseDist);
                let diffPoll = Math.round(alt.total_pollution - basePoll);
                let distStr = diffDist > 0 ? `+${diffDist} km` : `${diffDist} km`;
                let pollStr = diffPoll > 0 ? `+${diffPoll} Risk` : `${diffPoll} Risk`;
                
                let compHTML = '';
                if (alt.type === 'shortest') {
                    compHTML = `<span style="font-size:0.75rem; background:rgba(255,255,255,0.1); padding:0.1rem 0.4rem; border-radius:4px; color:#94a3b8;">Baseline</span>`;
                } else if (diffPoll < 0) {
                    compHTML = `<span style="font-size:0.75rem; background:rgba(16, 185, 129, 0.15); color:#10b981; padding:0.1rem 0.4rem; border-radius:4px;" title="Compared to Shortest Path">${distStr} | ${pollStr}</span>`;
                } else {
                    compHTML = `<span style="font-size:0.75rem; background:rgba(255, 255, 255, 0.1); color:#cbd5e1; padding:0.1rem 0.4rem; border-radius:4px;">${distStr} | ${pollStr}</span>`;
                }
                
                let badgeHTML = '';
                if (alt.type === 'full') {
                    badgeHTML = `<span style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; font-size: 0.7rem; font-weight: 800; padding: 0.2rem 0.5rem; border-radius: 4px; box-shadow: 0 0 10px rgba(16, 185, 129, 0.5); text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; gap: 0.25rem; margin-left: 0.5rem;">✨ Recommended</span>`;
                }

                div.style = `background: ${bg}; border: 1px solid ${border}; border-radius: 12px; padding: 1rem; cursor: pointer; transition: all 0.2s; position:relative;`;
                div.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:start;">
                        <div>
                            <h4 style="color: ${textCol}; margin:0 0 0.25rem 0; display:flex; align-items:center; font-size: 0.95rem;">
                                <span>${title}</span> 
                                <span style="font-size:0.8rem; margin-left:0.5rem; background:rgba(0,0,0,0.3); padding:0.1rem 0.4rem; border-radius: 4px;">${emoji} Grade ${grade}</span>
                                ${badgeHTML}
                            </h4>
                            <div style="font-size:0.85rem; color:#94a3b8; margin-bottom:0.5rem; display:flex; align-items:center; gap: 0.75rem;">
                                <span>Exposure: <b style="color:#fff">${Math.round(alt.total_pollution)}</b></span>
                                <span>Credits: <span style="color:${crd >= 0 ? '#10b981' : '#ef4444'}; font-weight: bold;">${crd>0?'+':''}${crd}</span></span>
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:0.9rem; font-weight:bold; color: ${textCol}; background:${border}; padding:0.2rem 0.6rem; border-radius:12px; display:inline-block;">
                                ${Math.round(alt.total_distance)} km
                            </div>
                            <div style="margin-top:0.4rem; justify-content:flex-end; display:flex;">
                                ${compHTML}
                            </div>
                        </div>
                    </div>
                    <div style="font-size:0.8rem; padding:0.4rem; background:rgba(0,0,0,0.2); border-radius:6px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#e2e8f0; margin-top:0.5rem;">
                        <span style="opacity:0.6; margin-right:4px;">PATH:</span> ${alt.route.map(n => CITY_NAMES[n] || n).join(' → ')}
                    </div>
                `;

                div.onclick = () => {
                    Array.from(container.children).forEach(c => {
                        c.style.border = '1px solid rgba(255,255,255,0.05)';
                        c.style.boxShadow = 'none';
                    });
                    div.style.border = `2px solid ${textCol}`;
                    div.style.boxShadow = `0 0 15px ${border}`;
                    
                    if (window.routeLayers) {
                        window.routeLayers.forEach((l, idx) => {
                            if (idx === thisLayerIdx) {
                                map.addLayer(l); // Show markers and names for selected
                            } else {
                                map.removeLayer(l); // Hide others
                            }
                        });
                        
                        // Path SVG Opacity logic
                        setTimeout(() => {
                            const pathsDOM = document.querySelectorAll('path.glowing-route, path.glowing-route-shortest, path[class*="route-path-"]');
                            pathsDOM.forEach(el => {
                                if (el.classList.contains('route-path-' + alt.type)) {
                                    el.style.opacity = '1';
                                    if(el.style.strokeOpacity) el.style.strokeOpacity = '1';
                                    if (el.parentNode) el.parentNode.appendChild(el); // Bring to front SVG trick
                                } else {
                                    el.style.opacity = '0.15';
                                    if(el.style.strokeOpacity) el.style.strokeOpacity = '0.15';
                                }
                            });
                        }, 50); // Small delay to let LRM finish drawing if still busy
                    }
                    
                    renderSegmentsData(alt.exposure_credits, alt.route);
                };

                container.appendChild(div);
            });

            // Default selection
            setTimeout(() => {
                const reqType = 'full';
                let pickIdx = data.alternatives.findIndex(a => a.type === reqType);
                if (pickIdx === -1) pickIdx = 0;
                
                // Map the pickIdx to the deduplicated DOM list
                const u = new Set();
                let actualDomIdx = 0;
                for(let i=0; i<=pickIdx; i++){
                    const p = JSON.stringify(data.alternatives[i].route);
                    if(!u.has(p)) { u.add(p); actualDomIdx = u.size - 1; }
                }

                if (container.children[actualDomIdx]) container.children[actualDomIdx].click();
            }, 50);
        } else {
            renderSegmentsData(data.exposure_credits, routeArr);
        }
    } else {
        renderSegmentsData(data.exposure_credits, routeArr);
    }

    const routeResults = document.getElementById('route-results');
    if (routeResults) {
        routeResults.classList.remove('hidden');
        routeResults.classList.add('animate-in');
    }

    // Fix Leaflet grey map loading issue
    setTimeout(() => {
        map.invalidateSize();
    }, 100);
}



// --- AQI Matrix Logic ---
window.aqiLoaded = false;
var aqiChartInstance = null;

async function loadAqiData() {
    const container = document.getElementById('aqi-container');
    const loader = document.getElementById('aqi-loading');
    const chartCard = document.getElementById('aqi-chart-card');
    
    try {
        const res = await fetch('/api/v1/aqi?region=metro');
        if (!res.ok) throw new Error('Network response was not ok');
        const data = await res.json();
        
        container.innerHTML = '';
        const cities = data.cities || [];
        
        cities.sort((a,b) => b.aqi - a.aqi);

        const chartLabels = [];
        const chartData = [];
        const chartColors = [];

        cities.forEach(c => {
            let color = '#4CAF50';
            if (c.aqi > 50) color = '#FFC107';
            if (c.aqi > 100) color = '#FF9800';
            if (c.aqi > 150) color = '#F44336';
            if (c.aqi > 200) color = '#9C27B0';
            if (c.aqi > 300) color = '#7E0023';

            chartLabels.push(c.city_name);
            chartData.push(c.aqi);
            chartColors.push(color);

            const card = document.createElement('div');
            card.className = 'glass city-card';
            card.style.setProperty('--card-color', color);
            
            card.innerHTML = `
                <div class="city-header">
                    <div>
                        <div class="city-name">${c.city_name}</div>
                        <div style="font-size: 11px; color: var(--text-secondary);">${c.category}</div>
                    </div>
                    <div class="city-aqi">${c.aqi}</div>
                </div>
                <div class="pollutants-list">
                    <div>PM2.5: <span style="color:#fff">${c.pollutants.pm25 || '--'}</span></div>
                    <div>PM10: <span style="color:#fff">${c.pollutants.pm10 || '--'}</span></div>
                    <div>CO: <span style="color:#fff">${c.pollutants.co || '--'}</span></div>
                    <div>O₃: <span style="color:#fff">${c.pollutants.o3 || '--'}</span></div>
                </div>
                <div style="margin-top:0.75rem; font-size:11px; text-transform:uppercase; color: ${color}; font-weight:600;">
                    🎯 Dominant: ${c.dominant_pollutant}
                </div>
            `;
            container.appendChild(card);
        });
        
        if (cities.length > 0 && chartCard) {
            chartCard.style.display = 'block';
            const ctxAqi = document.getElementById('aqiChart').getContext('2d');
            if (aqiChartInstance) aqiChartInstance.destroy();
            
            Chart.defaults.color = '#a1a1aa';
            aqiChartInstance = new Chart(ctxAqi, {
                type: 'bar',
                data: {
                    labels: chartLabels,
                    datasets: [{
                        label: 'Real-Time AQI',
                        data: chartData,
                        backgroundColor: chartColors,
                        borderWidth: 0,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                        x: { grid: { display: false } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }
        
        window.aqiLoaded = true;
    } catch (err) {
        console.error(err);
        container.innerHTML = `<p style="color: #ef4444;">Failed to load live AQI data.</p>`;
    } finally {
        loader.classList.add('hidden');
    }
}

// --- Tasks Viewer Logic ---
window.tasksLoaded = false;

let simChartInstance = null;

async function loadTasksData() {
    const taskSelect = document.getElementById('sim-task-select');
    try {
        const res = await fetch('/tasks');
        const data = await res.json();
        const tasks = data.tasks || [];
        
        taskSelect.innerHTML = tasks.map(t => 
            `<option value="${t.id}">${t.name} (${t.difficulty})</option>`
        ).join('');
        
        window.tasksLoaded = true;
    } catch (err) {
        console.error(err);
        taskSelect.innerHTML = `<option>Failed to load tasks</option>`;
    }
}

document.getElementById('btn-run-sim').addEventListener('click', async () => {
    const task_id = document.getElementById('sim-task-select').value;
    const loader = document.getElementById('sim-loading');
    const logBox = document.getElementById('sim-event-log');
    
    loader.classList.remove('hidden');
    logBox.innerHTML = '<span style="color: #10b981;">Starting simulation...</span>';
    
    try {
        const res = await fetch('/api/v1/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: task_id })
        });
        
        if (!res.ok) throw new Error('Simulation failed');
        const data = await res.json();
        
        // Populate logs
        let logHtml = '';
        const labels = [];
        const creditsData = [];
        const aqiData = [];
        
        data.timeline.forEach(step => {
            const cityName = CITY_NAMES[step.city] || step.city;
            logHtml += `<div style="padding: 0.3rem 0; border-bottom: 1px dashed rgba(255,255,255,0.05);"><span style="color:#a855f7;">[Step ${step.step}]</span> Arrived: <strong>${cityName}</strong> <span style="color:#0ea5e9;">(AQI: ${step.aqi})</span> | Credits: <span style="color:#10b981;">${step.credits}</span></div>`;
            labels.push(`Step ${step.step}`);
            creditsData.push(step.credits);
            aqiData.push(step.aqi);
        });
        
        logHtml += `<div style="color: var(--accent-primary); margin-top: 1rem; font-size: 1rem;">🏁 Final Grade: ${data.grade_report.grade} (Score: ${data.grade_report.score.toFixed(3)})</div>`;
        logBox.innerHTML = logHtml;
        
        // Draw Chart
        const ctx = document.getElementById('simChart').getContext('2d');
        if (simChartInstance) simChartInstance.destroy();
        
        Chart.defaults.color = '#a1a1aa';
        simChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Exposure Credits',
                        data: creditsData,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.2)',
                        borderWidth: 2,
                        tension: 0.3,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Local AQI',
                        data: aqiData,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.2)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        tension: 0.1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        title: { display: true, text: 'Credits Remaining' }
                    },
                    y1: {
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: 'AQI' }
                    },
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#fff' } }
                }
            }
        });
        
    } catch (err) {
        logBox.innerHTML = `<span style="color:#ef4444;">Error: ${err.message}</span>`;
    } finally {
        loader.classList.add('hidden');
    }
});

// ============================================================
// ROUTE NETWORK — canvas-based interactive graph
// ============================================================

let networkData = null;         // { nodes, edges }
let networkAnimationId = null;  // rAF handle
let networkDashOffset = 0;      // animated dash offset

const NODE_RADIUS  = 28;
const CANVAS_PAD_X = 60;        // extra padding so labels don't clip
const CANVAS_PAD_Y = 40;

// Scale raw node positions to the actual canvas pixel size
function scaleNodes(nodes, canvas) {
    const rawW = 760, rawH = 530;       // design-time canvas size (extended for southern cities)
    const scaleX = (canvas.width  - CANVAS_PAD_X * 2) / rawW;
    const scaleY = (canvas.height - CANVAS_PAD_Y * 2) / rawH;
    return nodes.map(n => ({
        ...n,
        px: Math.round(n.x * scaleX + CANVAS_PAD_X),
        py: Math.round(n.y * scaleY + CANVAS_PAD_Y),
    }));
}

function nodeById(scaled, id) {
    return scaled.find(n => n.id === id);
}

// Draw a filled, glow-ringed city node
function drawNode(ctx, n) {
    // Elegant Glow halo
    const grad = ctx.createRadialGradient(n.px, n.py, NODE_RADIUS * 0.2, n.px, n.py, NODE_RADIUS * 2.5);
    grad.addColorStop(0, n.color + '88');
    grad.addColorStop(0.5, n.color + '22');
    grad.addColorStop(1, 'transparent');
    ctx.beginPath();
    ctx.arc(n.px, n.py, NODE_RADIUS * 2.5, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // Node body
    ctx.beginPath();
    ctx.arc(n.px, n.py, NODE_RADIUS, 0, Math.PI * 2);
    const bodyGrad = ctx.createLinearGradient(n.px - NODE_RADIUS, n.py - NODE_RADIUS, n.px + NODE_RADIUS, n.py + NODE_RADIUS);
    bodyGrad.addColorStop(0, '#1e293b');
    bodyGrad.addColorStop(1, '#080d1a');
    ctx.fillStyle = bodyGrad;
    ctx.fill();

    // Node outline and inner ring
    ctx.strokeStyle = n.color;
    ctx.lineWidth = 3;
    ctx.stroke();
    
    ctx.beginPath();
    ctx.arc(n.px, n.py, NODE_RADIUS - 4, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255,255,255,0.1)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // City label (name centered inside)
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    if (n.name.length > 8) {
       ctx.font = 'bold 9px Inter, sans-serif';
    } else {
       ctx.font = 'bold 11px Inter, sans-serif';
    }
    ctx.fillText(n.name, n.px, n.py);

    // AQI badge underneath
    ctx.fillStyle = n.color;
    ctx.font = '600 11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(`AQI ${n.aqi}`, n.px, n.py + NODE_RADIUS + 10);
}

// Draw one directed edge (source → target) with animated dash
function drawEdge(ctx, src, tgt, edge, dashOffset) {
    const dx = tgt.px - src.px;
    const dy = tgt.py - src.py;
    const len = Math.sqrt(dx * dx + dy * dy);
    const ux = dx / len, uy = dy / len;

    // Offset start/end so lines don't overlap the node circles
    const startX = src.px + ux * (NODE_RADIUS + 4);
    const startY = src.py + uy * (NODE_RADIUS + 4);
    const endX   = tgt.px - ux * (NODE_RADIUS + 10);
    const endY   = tgt.py - uy * (NODE_RADIUS + 10);

    // Build curved path (slight arc for bidirectional edges)
    const mx = (startX + endX) / 2 + uy * 18;
    const my = (startY + endY) / 2 - ux * 18;

    // Glowing undertone
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.quadraticCurveTo(mx, my, endX, endY);
    ctx.strokeStyle = edge.color + '44'; // Hex + alpha
    ctx.lineWidth = 6;
    ctx.stroke();

    // Actual moving trail
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.quadraticCurveTo(mx, my, endX, endY);
    ctx.strokeStyle = edge.color;
    ctx.lineWidth = 2;
    ctx.setLineDash([8, 12]);
    ctx.lineDashOffset = -dashOffset;
    ctx.stroke();
    ctx.setLineDash([]); // Reset
    
    // Arrowhead at end
    const angle = Math.atan2(endY - my, endX - mx);
    const aLen = 9;
    ctx.beginPath();
    ctx.moveTo(endX, endY);
    ctx.lineTo(endX - aLen * Math.cos(angle - 0.4), endY - aLen * Math.sin(angle - 0.4));
    ctx.lineTo(endX - aLen * Math.cos(angle + 0.4), endY - aLen * Math.sin(angle + 0.4));
    ctx.closePath();
    ctx.fillStyle = edge.color;
    ctx.fill();

    // Mid-label: distance + avg_aqi
    const lx = (startX + endX) / 2 + uy * 20;
    const ly = (startY + endY) / 2 - ux * 20;
    ctx.fillStyle = 'rgba(15,23,42,0.8)';
    ctx.beginPath();
    ctx.roundRect(lx - 28, ly - 11, 56, 17, 4);
    ctx.fill();
    ctx.fillStyle = edge.color;
    ctx.font = 'bold 9.5px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`${edge.distance}km · AQI${edge.avg_aqi}`, lx, ly + 1);
}

function drawNetwork(canvas, nodes, edges, dashOffset) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const scaled = scaleNodes(nodes, canvas);

    // Edges first
    edges.forEach(e => {
        const src = nodeById(scaled, e.source);
        const tgt = nodeById(scaled, e.target);
        if (src && tgt) drawEdge(ctx, src, tgt, e, dashOffset);
    });

    // Nodes on top
    scaled.forEach(n => drawNode(ctx, n));
}

function startNetworkAnimation(canvas) {
    if (networkAnimationId) cancelAnimationFrame(networkAnimationId);
    function frame() {
        if (!networkData) return;
        networkDashOffset = (networkDashOffset + 0.4) % 28;
        drawNetwork(canvas, networkData.nodes, networkData.edges, networkDashOffset);
        networkAnimationId = requestAnimationFrame(frame);
    }
    networkAnimationId = requestAnimationFrame(frame);
}

function populateEdgeTable(edges, nodes) {
    const tbody = document.getElementById('network-edge-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    const nodeMap = Object.fromEntries(nodes.map(n => [n.id, n.name]));
    edges.forEach(e => {
        const aqiLabel = e.avg_aqi <= 50 ? 'Good' :
                         e.avg_aqi <= 100 ? 'Moderate' :
                         e.avg_aqi <= 150 ? 'Unhealthy (Sensitive)' :
                         e.avg_aqi <= 200 ? 'Unhealthy' :
                         e.avg_aqi <= 300 ? 'Very Unhealthy' : 'Hazardous';
        const tr = document.createElement('tr');
        tr.style.cssText = 'border-bottom: 1px solid rgba(255,255,255,0.05);';
        tr.innerHTML = `
            <td style="padding:0.6rem 0.75rem; color:#e2e8f0;">${nodeMap[e.source] || e.source}</td>
            <td style="padding:0.6rem 0.75rem; color:#e2e8f0;">${nodeMap[e.target] || e.target}</td>
            <td style="padding:0.6rem 0.75rem; text-align:right; color:#94a3b8;">${e.distance} km</td>
            <td style="padding:0.6rem 0.75rem; text-align:right; font-weight:bold; color:${e.color};">${e.avg_aqi}</td>
            <td style="padding:0.6rem 0.75rem; text-align:right; color:#94a3b8;">${e.pollution.toFixed(4)}</td>
            <td style="padding:0.6rem 0.75rem; color:${e.color}; font-size:12px;">${aqiLabel}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Hover tooltip
function setupNetworkHover(canvas, nodes) {
    const tooltip = document.getElementById('network-tooltip');
    if (!tooltip) return;
    const scaled = scaleNodes(nodes, canvas);
    canvas.addEventListener('mousemove', (evt) => {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width  / rect.width;
        const scaleY = canvas.height / rect.height;
        const mx = (evt.clientX - rect.left) * scaleX;
        const my = (evt.clientY - rect.top)  * scaleY;

        const hit = scaled.find(n => {
            const dx = mx - n.px, dy = my - n.py;
            return Math.sqrt(dx*dx + dy*dy) <= NODE_RADIUS + 6;
        });

        if (hit) {
            tooltip.style.display = 'block';
            tooltip.style.left = (evt.clientX - rect.left + 14) + 'px';
            tooltip.style.top  = (evt.clientY - rect.top  + 14) + 'px';
            tooltip.innerHTML = `
                <div style="font-weight:700; color:${hit.color}; margin-bottom:4px;">📍 ${hit.name}</div>
                <div style="color:#94a3b8;">AQI: <b style="color:${hit.color}">${hit.aqi}</b> — ${hit.category}</div>
                <div style="color:#94a3b8; margin-top:2px;">Pollution weight: ${hit.pollution_weight}</div>
            `;
        } else {
            tooltip.style.display = 'none';
        }
    });
    canvas.addEventListener('mouseleave', () => { tooltip.style.display = 'none'; });
}

window.networkLoaded = false;

async function loadNetworkGraph(force = false) {
    if (window.networkLoaded && !force) return;
    const loader = document.getElementById('network-loading');
    const canvas = document.getElementById('network-canvas');
    if (!canvas) return;

    if (loader) loader.classList.remove('hidden');
    if (networkAnimationId) { cancelAnimationFrame(networkAnimationId); networkAnimationId = null; }

    try {
        const res  = await fetch('/api/v1/route-network');
        if (!res.ok) throw new Error('Network API error');
        networkData = await res.json();

        // Resize canvas to actual display width maintaining aspect ratio
        const displayW = canvas.clientWidth || 900;
        canvas.width  = displayW > 0 ? displayW : 900;
        canvas.height = Math.round(canvas.width * (630 / 900)); // taller to fit south India cities

        populateEdgeTable(networkData.edges, networkData.nodes);
        setupNetworkHover(canvas, networkData.nodes);
        startNetworkAnimation(canvas);
        window.networkLoaded = true;
    } catch (err) {
        console.error('Route network:', err);
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ef4444';
        ctx.font = '14px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Failed to load route network data.', canvas.width / 2, canvas.height / 2);
    } finally {
        if (loader) loader.classList.add('hidden');
    }
}

// Refresh button
document.getElementById('btn-refresh-network')?.addEventListener('click', () => {
    window.networkLoaded = false;
    loadNetworkGraph(true);
});

// Pause animation when tab is hidden, resume when visible
document.addEventListener('visibilitychange', () => {
    if (document.hidden && networkAnimationId) {
        cancelAnimationFrame(networkAnimationId);
        networkAnimationId = null;
    } else if (!document.hidden && networkData && !viewNetwork.classList.contains('hidden')) {
        const c = document.getElementById('network-canvas');
        if (c) startNetworkAnimation(c);
    }
});
