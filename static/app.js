/* Quick Trip Planner — Map Page Logic */

// --- State ---
let map, markersLayer, pathsLayer, homeMarker;
let selectedAirport = null; // { iata, lat, lon, city, ... }
let allRoutes = [];
let depDay = -1; // Any day
let retDay = -1; // Any day
let searchTimeout = null;
let activeSelectedDest = null;

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

// --- Init ---
function init() {
    lucide.createIcons();

    map = L.map('map', { zoomControl: false }).setView([40, -3], 6);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; CARTO',
    }).addTo(map);

    L.control.zoom({ position: 'topright' }).addTo(map);
    markersLayer = L.layerGroup().addTo(map);
    pathsLayer = L.layerGroup().addTo(map);

    // Day selectors
    document.getElementById('depDaySelector').addEventListener('change', (e) => {
        depDay = parseInt(e.target.value);
        fetchRoutes();
    });
    document.getElementById('retDaySelector').addEventListener('change', (e) => {
        retDay = parseInt(e.target.value);
        fetchRoutes();
    });

    // Close flight panel
    const closeBtn = document.getElementById('closePanelBtn');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeFlightPanel);
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeFlightPanel();
    });

    // Airport search
    const searchInput = document.getElementById('airportSearch');
    const resultsDiv = document.getElementById('airportResults');

    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        const q = searchInput.value.trim();
        if (q.length < 2) {
            resultsDiv.classList.remove('active');
            return;
        }
        searchTimeout = setTimeout(() => searchAirports(q), 200);
    });

    searchInput.addEventListener('focus', () => {
        if (searchInput.value.trim().length >= 2) {
            resultsDiv.classList.add('active');
        }
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.airport-search-wrapper')) {
            resultsDiv.classList.remove('active');
        }
    });
}

// --- API ---
async function searchAirports(query) {
    const res = await fetch(`/api/airports?search=${encodeURIComponent(query)}`);
    const airports = await res.json();
    const resultsDiv = document.getElementById('airportResults');

    if (airports.length === 0) {
        resultsDiv.innerHTML = '<div class="p-4 text-sm text-slate-400 text-center">No airports found</div>';
        resultsDiv.classList.add('active');
        return;
    }

    resultsDiv.innerHTML = airports.map(a => `
        <div class="airport-result-item" data-iata="${a.iata}" data-lat="${a.lat}" data-lon="${a.lon}" data-city="${a.city}">
            <span class="iata">${a.iata}</span>
            <div>
                <div class="city">${a.city}</div>
                <div class="name">${a.name}</div>
            </div>
        </div>
    `).join('');

    resultsDiv.querySelectorAll('.airport-result-item').forEach(item => {
        item.addEventListener('click', () => selectAirport({
            iata: item.dataset.iata,
            lat: parseFloat(item.dataset.lat),
            lon: parseFloat(item.dataset.lon),
            city: item.dataset.city,
        }));
    });

    resultsDiv.classList.add('active');
}

async function fetchRoutes() {
    if (!selectedAirport) return;
    const res = await fetch(`/api/routes/${selectedAirport.iata}?dep_day=${depDay}&ret_day=${retDay}`);
    allRoutes = await res.json();
    renderRoutes();

    if (activeSelectedDest) {
        const updated = allRoutes.find(r => r.dest_iata === activeSelectedDest.dest_iata);
        if (updated) {
            openFlightPanel(updated);
        } else {
            closeFlightPanel();
        }
    }
}

async function selectAirport(airport) {
    selectedAirport = airport;
    closeFlightPanel();

    // Update UI
    const searchInput = document.getElementById('airportSearch');
    searchInput.value = `${airport.city}`;
    document.getElementById('airportResults').classList.remove('active');

    const badge = document.getElementById('selectedIata');
    badge.textContent = airport.iata;
    badge.classList.remove('hidden');

    document.getElementById('hubLabel').textContent = `${airport.iata} HUB`;
    document.getElementById('emptyState').style.display = 'none';

    // Fetch routes from API
    await fetchRoutes();

    // Center map on airport
    map.setView([airport.lat, airport.lon], 6, { animate: true });

    // Set home marker
    if (homeMarker) map.removeLayer(homeMarker);
    homeMarker = L.circleMarker([airport.lat, airport.lon], {
        radius: 10,
        color: 'white',
        fillColor: '#2563eb',
        fillOpacity: 1,
        weight: 3,
    }).addTo(map)
      .bindTooltip(`${airport.city.toUpperCase()} (${airport.iata})`, {
          permanent: true,
          direction: 'bottom',
          offset: [0, 10],
          className: 'custom-tooltip',
      });
}

// --- Side Panel ---
function openFlightPanel(route) {
    activeSelectedDest = route;
    const panel = document.getElementById('flightPanel');
    if (!panel) return;

    document.getElementById('panelTitle').textContent = route.dest_city;
    document.getElementById('panelIata').textContent = route.dest_iata;
    document.getElementById('panelSub').textContent = `Connection between ${selectedAirport.city} (${selectedAirport.iata}) and ${route.dest_city} (${route.dest_iata})`;

    const depLabel = depDay === -1 ? 'Any' : DAY_NAMES[depDay];
    const retLabel = retDay === -1 ? 'Any' : DAY_NAMES[retDay];
    document.getElementById('panelFilterStatus').textContent = `Filter: ${depLabel} → ${retLabel}`;

    const outbound = route.outbound_flights || [];
    const returns = route.return_flights || [];
    const totalCount = route.flight_count || (outbound.length + returns.length);
    document.getElementById('panelFlightCount').textContent = `${totalCount} flight option${totalCount === 1 ? '' : 's'}`;

    const listDiv = document.getElementById('panelFlightList');
    let html = '';

    // --- Outbound Flights Section (Blue) ---
    html += `
        <div class="mb-4">
            <div class="flex items-center gap-2 mb-2 pb-1 border-b border-blue-100">
                <i data-lucide="plane-takeoff" class="w-4 h-4 text-blue-600"></i>
                <h3 class="font-bold text-xs uppercase tracking-wider text-blue-700">Outbound Flights (${selectedAirport.iata} → ${route.dest_iata})</h3>
                <span class="ml-auto text-[10px] font-bold bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">${outbound.length}</span>
            </div>`;

    if (outbound.length > 0) {
        html += outbound.map((f, i) => {
            const flightDays = f.days || [];
            const carrier = f.airline || 'Scheduled Flight';
            const num = f.flight_no ? `#${f.flight_no}` : `Flight ${i + 1}`;
            return `
                <div class="bg-white rounded-xl p-3.5 border border-slate-200 shadow-sm mb-2 hover:border-blue-300 transition-all">
                    <div class="flex justify-between items-center mb-1.5">
                        <span class="font-bold text-xs text-slate-800">${carrier} <span class="font-mono text-slate-400 font-normal">${num}</span></span>
                        <span class="text-[10px] font-bold bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">OUTBOUND</span>
                    </div>
                    <div class="flex items-center justify-between text-xs bg-blue-50/50 p-2 rounded border border-blue-100/50 my-2">
                        <span class="text-[10px] font-bold text-blue-600 uppercase">Departure Time</span>
                        <span class="font-mono font-bold text-slate-800">${f.dep_time || '—'}</span>
                    </div>
                    <div class="flex gap-1 justify-between text-[10px]">
                        ${DAY_NAMES.map((day, idx) => {
                            const active = flightDays.includes(idx);
                            return `<span class="px-1.5 py-0.5 rounded font-bold ${active ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-400'}">${day}</span>`;
                        }).join('')}
                    </div>
                </div>`;
        }).join('');
    } else if (route.dep_am || route.dep_pm) {
        html += `
            <div class="bg-white rounded-xl p-3 border border-slate-200 text-xs mb-2">
                <div class="font-bold text-slate-700 mb-1">Departure Schedule Summary</div>
                ${route.dep_am ? `<div class="flex justify-between py-0.5"><span>Morning</span><span class="font-mono font-bold">${route.dep_am}</span></div>` : ''}
                ${route.dep_pm ? `<div class="flex justify-between py-0.5"><span>Afternoon</span><span class="font-mono font-bold">${route.dep_pm}</span></div>` : ''}
            </div>`;
    } else {
        html += `<div class="p-3 text-xs text-slate-400 italic bg-slate-50 rounded-lg text-center mb-2">No outbound flight schedule recorded.</div>`;
    }
    html += `</div>`;

    // --- Return Flights Section (Orange) ---
    html += `
        <div class="mt-4">
            <div class="flex items-center gap-2 mb-2 pb-1 border-b border-orange-100">
                <i data-lucide="plane-landing" class="w-4 h-4 text-orange-600"></i>
                <h3 class="font-bold text-xs uppercase tracking-wider text-orange-700">Return Flights (${route.dest_iata} → ${selectedAirport.iata})</h3>
                <span class="ml-auto text-[10px] font-bold bg-orange-50 text-orange-600 px-2 py-0.5 rounded-full">${returns.length}</span>
            </div>`;

    if (returns.length > 0) {
        html += returns.map((f, i) => {
            const flightDays = f.days || [];
            const carrier = f.airline || 'Scheduled Flight';
            const num = f.flight_no ? `#${f.flight_no}` : `Flight ${i + 1}`;
            return `
                <div class="bg-white rounded-xl p-3.5 border border-slate-200 shadow-sm mb-2 hover:border-orange-300 transition-all">
                    <div class="flex justify-between items-center mb-1.5">
                        <span class="font-bold text-xs text-slate-800">${carrier} <span class="font-mono text-slate-400 font-normal">${num}</span></span>
                        <span class="text-[10px] font-bold bg-orange-50 text-orange-600 px-1.5 py-0.5 rounded">RETURN</span>
                    </div>
                    <div class="flex items-center justify-between text-xs bg-orange-50/50 p-2 rounded border border-orange-100/50 my-2">
                        <span class="text-[10px] font-bold text-orange-600 uppercase">Return Time</span>
                        <span class="font-mono font-bold text-slate-800">${f.dep_time || '—'}</span>
                    </div>
                    <div class="flex gap-1 justify-between text-[10px]">
                        ${DAY_NAMES.map((day, idx) => {
                            const active = flightDays.includes(idx);
                            return `<span class="px-1.5 py-0.5 rounded font-bold ${active ? 'bg-orange-500 text-white' : 'bg-slate-100 text-slate-400'}">${day}</span>`;
                        }).join('')}
                    </div>
                </div>`;
        }).join('');
    } else if (route.ret_am || route.ret_pm) {
        html += `
            <div class="bg-white rounded-xl p-3 border border-orange-200 text-xs mb-2">
                <div class="font-bold text-orange-700 mb-1">Return Schedule Summary</div>
                ${route.ret_am ? `<div class="flex justify-between py-0.5"><span>Morning</span><span class="font-mono font-bold text-orange-600">${route.ret_am}</span></div>` : ''}
                ${route.ret_pm ? `<div class="flex justify-between py-0.5"><span>Afternoon</span><span class="font-mono font-bold text-orange-600">${route.ret_pm}</span></div>` : ''}
            </div>`;
    } else {
        html += `<div class="p-3 text-xs text-slate-400 italic bg-slate-50 rounded-lg text-center mb-2">No return flight schedule recorded for reverse route.</div>`;
    }
    html += `</div>`;

    listDiv.innerHTML = html;
    lucide.createIcons();
    panel.classList.remove('translate-x-full');
}

function closeFlightPanel() {
    activeSelectedDest = null;
    const panel = document.getElementById('flightPanel');
    if (panel) {
        panel.classList.add('translate-x-full');
    }
}

// --- Rendering ---
function getCurvedPath(from, to) {
    const mid = [
        (from[0] + to[0]) / 2 + (to[1] - from[1]) * 0.08,
        (from[1] + to[1]) / 2 + (from[0] - to[0]) * 0.08,
    ];
    return [from, mid, to];
}

function renderRoutes() {
    markersLayer.clearLayers();
    pathsLayer.clearLayers();

    if (!selectedAirport) return;

    const homeCoords = [selectedAirport.lat, selectedAirport.lon];

    allRoutes.forEach((route) => {
        const destCoords = [route.dest_lat, route.dest_lon];
        const hasSchedule = route.has_schedule;
        const flightCount = route.flight_count || 0;

        const marker = L.circleMarker(destCoords, {
            radius: 7,
            color: 'white',
            fillColor: hasSchedule ? '#2563eb' : '#94a3b8',
            fillOpacity: 1,
            weight: 2,
        }).addTo(markersLayer);

        const countText = flightCount > 0
            ? `<span class="text-blue-600 font-bold">${flightCount} flight${flightCount === 1 ? '' : 's'} available</span>`
            : '<span class="text-slate-400 italic">Schedule not available</span>';

        const tooltipHtml = `
            <div class="font-sans text-center">
                <div class="font-bold text-sm text-slate-900">${route.dest_city} <span class="text-xs font-mono text-slate-400">(${route.dest_iata})</span></div>
                <div class="text-xs mt-1">${countText}</div>
                <div class="text-[10px] text-blue-500 font-medium mt-1 uppercase tracking-wider">Click for flight details</div>
            </div>`;

        marker.bindTooltip(tooltipHtml, {
            className: 'detail-tooltip',
            direction: 'top',
            offset: [0, -10],
            sticky: false,
            opacity: 1,
        });

        marker.on('click', () => {
            openFlightPanel(route);
        });

        // Departure line (blue)
        L.polyline([homeCoords, destCoords], {
            color: '#2563eb',
            weight: 2,
            opacity: hasSchedule ? 0.6 : 0.25,
            dashArray: (hasSchedule && route.has_am) ? null : '8, 8',
        }).addTo(pathsLayer);

        // Return line (orange, curved)
        const curved = getCurvedPath(destCoords, homeCoords);
        L.polyline(curved, {
            color: '#f97316',
            weight: 2,
            opacity: hasSchedule ? 0.6 : 0.25,
            dashArray: (hasSchedule && route.has_am) ? null : '5, 10',
            smoothFactor: 2,
        }).addTo(pathsLayer);
    });

    // Update counters
    document.getElementById('routeCount').innerText = `${allRoutes.length} Cities`;
    const depLabel = depDay === -1 ? 'Any' : DAY_NAMES[depDay];
    const retLabel = retDay === -1 ? 'Any' : DAY_NAMES[retDay];
    document.getElementById('statusText').innerText = `${depLabel} → ${retLabel} | ${allRoutes.length} ROUTES`;
}

window.onload = init;
