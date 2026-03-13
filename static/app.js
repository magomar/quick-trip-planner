/* Quick Trip Planner — Map Page Logic */

// --- State ---
let map, markersLayer, pathsLayer, homeMarker;
let selectedAirport = null; // { iata, lat, lon, city, ... }
let allRoutes = [];
let depDay = -1; // Any day
let retDay = -1; // Any day
let searchTimeout = null;

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
        renderRoutes();
    });
    document.getElementById('retDaySelector').addEventListener('change', (e) => {
        retDay = parseInt(e.target.value);
        renderRoutes();
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

async function selectAirport(airport) {
    selectedAirport = airport;

    // Update UI
    const searchInput = document.getElementById('airportSearch');
    searchInput.value = `${airport.city}`;
    document.getElementById('airportResults').classList.remove('active');

    const badge = document.getElementById('selectedIata');
    badge.textContent = airport.iata;
    badge.classList.remove('hidden');

    document.getElementById('hubLabel').textContent = `${airport.iata} HUB`;
    document.getElementById('emptyState').style.display = 'none';

    // Fetch routes
    const res = await fetch(`/api/routes/${airport.iata}`);
    allRoutes = await res.json();

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

    renderRoutes();
}

// --- Rendering ---
function getCurvedPath(from, to) {
    const mid = [
        (from[0] + to[0]) / 2 + (to[1] - from[1]) * 0.08,
        (from[1] + to[1]) / 2 + (from[0] - to[0]) * 0.08,
    ];
    return [from, mid, to];
}

function formatTimeLine(label, amTime, pmTime, colorClass) {
    if (!amTime && !pmTime) return '';
    let html = `<div class="flex flex-col gap-1 mt-2">
        <span class="text-[10px] font-bold uppercase ${colorClass}">${label}</span>`;
    if (amTime) html += `<div class="flex justify-between items-center text-xs gap-4"><span>Morning</span><span class="font-mono bg-slate-100 px-1.5 rounded">${amTime}</span></div>`;
    if (pmTime) html += `<div class="flex justify-between items-center text-xs gap-4"><span>Afternoon</span><span class="font-mono bg-slate-100 px-1.5 rounded">${pmTime}</span></div>`;
    html += `</div>`;
    return html;
}

function renderRoutes() {
    markersLayer.clearLayers();
    pathsLayer.clearLayers();

    if (!selectedAirport) return;

    const filtered = allRoutes.filter(r => {
        const days = r.days || [];
        const hasSchedule = days.length > 0;

        // If both selectors are "Any day", show all routes
        if (depDay === -1 && retDay === -1) return true;

        // Routes without schedule data are hidden when a specific day is selected
        if (!hasSchedule) return false;

        // Check departure day match
        if (depDay !== -1 && !days.includes(depDay)) return false;

        // Check return day match
        if (retDay !== -1 && !days.includes(retDay)) return false;

        return true;
    });

    const homeCoords = [selectedAirport.lat, selectedAirport.lon];

    filtered.forEach(route => {
        const destCoords = [route.dest_lat, route.dest_lon];
        const hasSchedule = (route.days || []).length > 0;

        // Destination marker
        const marker = L.circleMarker(destCoords, {
            radius: 6,
            color: 'white',
            fillColor: hasSchedule ? '#475569' : '#94a3b8',
            fillOpacity: 1,
            weight: 1.5,
        }).addTo(markersLayer);

        const depTimesHtml = formatTimeLine('Departure', route.dep_am, route.dep_pm, 'text-blue-600');
        const retTimesHtml = formatTimeLine('Return', route.ret_am, route.ret_pm, 'text-orange-600');
        const scheduleHtml = (depTimesHtml || retTimesHtml)
            ? `${depTimesHtml}${retTimesHtml}`
            : '<div class="text-[10px] text-slate-400 mt-2 italic">Schedule not yet available</div>';

        const tooltipHtml = `
            <div class="min-w-[200px] font-sans">
                <div class="flex justify-between items-start border-b pb-2 mb-2">
                    <div>
                        <h3 class="font-bold text-sm text-slate-900 leading-none">${route.dest_city}</h3>
                        <span class="text-[10px] text-slate-400 font-mono">${route.dest_iata}</span>
                    </div>
                    <span class="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded font-bold">DIRECT</span>
                </div>
                ${scheduleHtml}
            </div>`;

        marker.bindTooltip(tooltipHtml, {
            className: 'detail-tooltip',
            direction: 'top',
            offset: [0, -10],
            sticky: false,
            opacity: 1,
        });

        // Departure line (blue)
        L.polyline([homeCoords, destCoords], {
            color: '#2563eb',
            weight: 2,
            opacity: hasSchedule ? 0.55 : 0.25,
            dashArray: (hasSchedule && route.has_am) ? null : '8, 8',
        }).addTo(pathsLayer);

        // Return line (orange, curved)
        const curved = getCurvedPath(destCoords, homeCoords);
        L.polyline(curved, {
            color: '#f97316',
            weight: 2,
            opacity: hasSchedule ? 0.55 : 0.25,
            dashArray: (hasSchedule && route.has_am) ? null : '5, 10',
            smoothFactor: 2,
        }).addTo(pathsLayer);
    });

    // Update counters
    document.getElementById('routeCount').innerText = `${filtered.length} Cities`;
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const depLabel = depDay === -1 ? 'Any' : dayNames[depDay];
    const retLabel = retDay === -1 ? 'Any' : dayNames[retDay];
    document.getElementById('statusText').innerText = `${depLabel} → ${retLabel} | ${filtered.length} ROUTES`;
}

window.onload = init;
