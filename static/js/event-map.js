(function () {
  "use strict";

  const mapEl = document.getElementById("event-map");
  if (!mapEl || typeof L === "undefined") return;

  const address = mapEl.dataset.address;
  if (!address) return;

  // Default view (Sydney) before geocoding completes
  const map = L.map("event-map").setView([-33.8688, 151.2093], 13);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap contributors",
  }).addTo(map);

  // Build an explicit icon
  const huddleIcon = L.icon({
    iconUrl: "/static/images/marker-icon.png",
    iconRetinaUrl: "/static/images/marker-icon-2x.png",
    shadowUrl: "/static/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  const statusEl = document.getElementById("map-status");

  function setStatus(msg) {
    if (statusEl) statusEl.textContent = msg;
  }

  async function geocode(query) {
    const url =
      "https://nominatim.openstreetmap.org/search?q=" +
      encodeURIComponent(query) +
      "&format=json&limit=1";
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error("Geocoding request failed");
    const data = await res.json();
    return data && data.length > 0 ? data[0] : null;
  }

  async function geocodeAndPin(query) {
    setStatus("Locating...");
    try {
      let result = await geocode(query);

      if (!result) {
        result = await geocode(query + ", Australia");
      }

      if (!result) {
        setStatus(
          "Could not find this location on the map. Try editing it to include a suburb or full address.",
        );
        return;
      }

      const lat = parseFloat(result.lat);
      const lon = parseFloat(result.lon);
      const displayName = result.display_name || query;

      map.setView([lat, lon], 15);
      L.marker([lat, lon], { icon: huddleIcon })
        .addTo(map)
        .bindPopup(displayName)
        .openPopup();
      setStatus("");
    } catch (err) {
      setStatus("Map could not load this location.");
    }
  }

  geocodeAndPin(address);
})();
