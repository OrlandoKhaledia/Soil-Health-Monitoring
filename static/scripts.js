let map;
let drawnItems = new L.FeatureGroup();
let currentFeature = null;
let ndviSeries = [];
let currentParcelId = null;

// Initialize Map
function initMap() {
  map = L.map("map").setView([-1.95, 30.06], 8);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
  }).addTo(map);
  map.addLayer(drawnItems);

  const drawControl = new L.Control.Draw({
    draw: { polyline: false, circle: false, rectangle: false, marker: false, circlemarker: false },
    edit: { featureGroup: drawnItems },
  });
  map.addControl(drawControl);

  map.on(L.Draw.Event.CREATED, (e) => {
    drawnItems.clearLayers();
    drawnItems.addLayer(e.layer);
    currentFeature = e.layer.toGeoJSON();
  });
}
initMap();

// Helper Fetch
async function safeFetch(url, options = {}) {
  try {
    const res = await fetch(url, options);
    return await res.json();
  } catch (err) {
    console.error("Fetch error:", err);
    return { error: err.message };
  }
}

// --- AUTH ---
async function handleLogin(email, password) {
  const data = await safeFetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return data;
}

document.getElementById("loginBtn").onclick = async () => {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const data = await handleLogin(email, password);

  if (data.error) {
    document.getElementById("status").innerText = data.error;
    return;
  }

  document.getElementById("status").innerText = data.message;
  document.getElementById("auth").style.display = "none";

  const mapC = document.getElementById("map-container");
  mapC.style.display = "flex";
  mapC.classList.add("active");

  window.currentUser = { user_id: data.user_id, access_token: data.access_token };

  // Ensure map redraw works after becoming visible
  setTimeout(() => {
    map.invalidateSize();
    map.setView([-1.95, 30.06], 8);
  }, 200);
};

document.getElementById("signupBtn").onclick = async () => {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const data = await safeFetch("/api/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (data.error) {
    document.getElementById("status").innerText = data.error;
    return;
  }

  document.getElementById("status").innerText = data.message;
  document.getElementById("auth").style.display = "none";

  const mapC = document.getElementById("map-container");
  mapC.style.display = "flex";
  mapC.classList.add("active");

  window.currentUser = { user_id: data.user_id };

  setTimeout(() => {
    map.invalidateSize();
    map.setView([-1.95, 30.06], 8);
  }, 200);
};

// --- Compute NDVI ---
document.getElementById("computeBtn").onclick = async () => {
  if (!currentFeature) return alert("Draw a parcel first!");
  document.getElementById("result").innerText = "Computing...";
  const res = await safeFetch("/api/compute_ndvi", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feature: currentFeature, user_id: window.currentUser.user_id }),
  });

  if (res.error) return (document.getElementById("result").innerText = res.error);
  ndviSeries = res.series;
  currentParcelId = res.parcel_id;
  document.getElementById("result").innerText =
    `Degradation Score: ${res.degradation_score}\nAI Insight: ${res.ai_insight}\n${res.message}`;
};

// --- Charts ---
document.getElementById("chartBtn").onclick = () => {
  if (!ndviSeries.length) return alert("Compute NDVI first!");
  const modal = document.getElementById("chartModal");
  modal.style.display = "block";

  const ctx = document.getElementById("trendChart").getContext("2d");
  if (window.trendChart instanceof Chart) window.trendChart.destroy();
  window.trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: ndviSeries.map((d) => d.date),
      datasets: [
        {
          label: "NDVI Trend",
          data: ndviSeries.map((d) => d.ndvi),
          borderWidth: 2,
          borderColor: "#2a7a2e",
          fill: false,
          tension: 0.2,
        },
      ],
    },
  });
};

document.getElementById("closeChart").onclick = () => {
  document.getElementById("chartModal").style.display = "none";
};

// --- Report ---
document.getElementById("reportBtn").onclick = () => {
  if (!currentParcelId) return alert("Compute first!");
  window.open(`/api/download_report/${currentParcelId}`, "_blank");
};

// --- Logout ---
document.getElementById("logoutBtn").onclick = () => {
  // Hide dashboard/map container
  const mapContainer = document.getElementById("map-container");
  mapContainer.classList.remove("active");
  mapContainer.style.display = "none";

  // Show auth panel
  const authDiv = document.getElementById("auth");
  authDiv.style.display = "block";

  // Clear login inputs
  document.getElementById("email").value = "";
  document.getElementById("password").value = "";

  // Update status
  document.getElementById("status").innerText = "Logged out successfully.";

  // Clear session data
  window.currentUser = null;
  ndviSeries = [];
  currentParcelId = null;
  currentFeature = null;

  // Clear drawn layers
  drawnItems.clearLayers();

  // Reset map after small delay to ensure Leaflet redraw works
  if (map) setTimeout(() => {
    map.invalidateSize();
    map.setView([-1.95, 30.06], 8);
  }, 200);
};
