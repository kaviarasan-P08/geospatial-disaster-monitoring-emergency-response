let map;
let marker = null;

// Initialize map
export function initMap() {
  map = L.map('map').setView([20.5937, 78.9629], 5);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  map.on('click', function (e) {
    if (document.getElementById('type').disabled) {
      alert('You cannot select a location because your star rating is zero.');
      return;
    }
    const { lat, lng } = e.latlng;
    document.getElementById('latitude').value = lat.toFixed(5);
    document.getElementById('longitude').value = lng.toFixed(5);

    if (marker) map.removeLayer(marker);
    marker = L.marker([lat, lng]).addTo(map);
  });

  loadReports();
  loadNasaEvents();
  loadEarthquakes();
}

// Load user-submitted reports
async function loadReports() {
  const res = await fetch('/user-reports');
  const reports = await res.json();
  const container = document.getElementById('reports');
  container.innerHTML = '';

  reports.forEach(r => {
    if (!r.lat || !r.lon) return;
    const lat = parseFloat(r.lat);
    const lng = parseFloat(r.lon);
    if (isNaN(lat) || isNaN(lng)) return;

    const div = document.createElement('div');
    div.className = 'report-entry';
    div.innerHTML = `<strong>${r.type}</strong> at [${lat.toFixed(5)}, ${lng.toFixed(5)}]<br>${r.description}<br><small>Reported by: ${r.username || 'Unknown'}</small>`;
    container.appendChild(div);

    L.circleMarker([lat, lng], {
      color: 'red',
      radius: 8,
      fillOpacity: 0.6
    }).addTo(map).bindPopup(`<b>${r.type}</b><br>${r.description}<br><small>Reported by: ${r.username || 'Unknown'}</small>`);
  });
}

// NASA Events
async function loadNasaEvents() {
  try {
    const res = await fetch('/nasa-data');
    const data = await res.json();
    if (!data || !data.events) return;

    data.events.forEach(event => {
      const coords = event.geometry?.[0]?.coordinates;
      if (coords && coords.length === 2) {
        const [lng, lat] = coords;
        L.marker([lat, lng], { title: event.title })
          .addTo(map)
          .bindPopup(`<b>NASA: ${event.title}</b><br>Status: ${event.closed || 'Ongoing'}`);
      }
    });
  } catch (error) {
    console.error('Failed to load NASA data:', error);
  }
}

// USGS Earthquakes
async function loadEarthquakes() {
  try {
    const res = await fetch('/earthquake-data');
    const data = await res.json();
    if (!data?.features) return;

    data.features.forEach(quake => {
      const coords = quake.geometry?.coordinates;
      if (coords && coords.length >= 2) {
        const [lng, lat] = coords;
        const mag = quake.properties.mag;
        const place = quake.properties.place;

        L.circle([lat, lng], {
          color: 'orange',
          radius: mag * 5000,
          fillOpacity: 0.3
        }).addTo(map).bindPopup(`<b>USGS Earthquake</b><br>${place}<br>Magnitude: ${mag}`);
      }
    });
  } catch (error) {
    console.error('Failed to load USGS data:', error);
  }
}

// Report submission
document.addEventListener('DOMContentLoaded', () => {
  initMap();

  const form = document.getElementById('report-form');
  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (document.getElementById('type').disabled) return;

    const report = {
      type: document.getElementById('type').value,
      description: document.getElementById('description').value,
      lat: document.getElementById('latitude').value,
      lon: document.getElementById('longitude').value
    };

    const res = await fetch('/submit-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(report)
    });

    if (res.ok) {
      alert('Report submitted successfully!');
      form.reset();
      if (marker) map.removeLayer(marker);
      loadReports();
    } else {
      alert('Failed to submit report.');
    }
  });
});
