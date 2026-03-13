/* Quick Trip Planner — Admin Page Logic */

let countries = [];

async function init() {
    lucide.createIcons();
    await loadCountries();
}

function showToast(message, type = 'warning') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

async function loadCountries() {
    const res = await fetch('/api/admin/countries');
    countries = await res.json();
    renderGrid();
}

function renderGrid() {
    const grid = document.getElementById('countryGrid');
    const activeCount = countries.filter(c => c.enabled).length;
    document.getElementById('activeCount').textContent = `${activeCount} Active`;

    grid.innerHTML = countries.map(c => {
        const locked = !c.available;
        return `
            <div class="country-card ${locked ? 'locked' : ''}">
                <span class="flag">${c.flag}</span>
                <div class="info">
                    <div class="name">${c.name}</div>
                    ${locked
                        ? '<span class="badge soon">Coming Soon</span>'
                        : (c.enabled ? '<span class="badge active">Active</span>' : '')
                    }
                </div>
                <label class="toggle ${locked ? 'disabled' : ''}" title="${locked ? 'Not yet available' : 'Toggle'}">
                    <input type="checkbox" ${c.enabled ? 'checked' : ''} ${locked ? 'disabled' : ''}
                           onchange="toggleCountry('${c.code}', this.checked, ${locked})">
                    <div class="toggle-track"></div>
                    <div class="toggle-thumb"></div>
                </label>
            </div>`;
    }).join('');
}

async function toggleCountry(code, enabled, locked) {
    if (locked) {
        showToast(`${countries.find(c => c.code === code)?.flag || ''} This country is not yet available. Coming soon!`, 'warning');
        // Reset the checkbox visually
        await loadCountries();
        return;
    }

    try {
        const res = await fetch(`/api/admin/countries/${code}?enabled=${enabled}`, { method: 'PUT' });
        if (!res.ok) {
            const data = await res.json();
            showToast(data.detail || 'Failed to update', 'error');
            await loadCountries();
            return;
        }
        showToast(`${countries.find(c => c.code === code)?.flag || ''} ${enabled ? 'Enabled' : 'Disabled'} successfully`, 'success');
        await loadCountries();
    } catch {
        showToast('Network error', 'error');
        await loadCountries();
    }
}

async function refreshData() {
    const btn = document.getElementById('refreshBtn');
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader" class="w-4 h-4 animate-spin"></i> Refreshing...';
    lucide.createIcons();

    try {
        const res = await fetch('/api/data/refresh', { method: 'POST' });
        const data = await res.json();
        showToast(`Data refreshed: ${data.seeded.airports} airports, ${data.seeded.routes} routes`, 'success');
    } catch {
        showToast('Refresh failed', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="refresh-cw" class="w-4 h-4"></i> Refresh Data';
        lucide.createIcons();
    }
}

window.onload = init;
