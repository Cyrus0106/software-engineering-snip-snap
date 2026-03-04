(function () {
  "use strict";

  // ── Constants ────────────────────────────────────────────────────────────────
  const UK_CENTER = [54.5, -3.5];
  const UK_ZOOM = 6;
  const LOCATION_ZOOM = 14;
  const NOMINATIM_URL = "https://nominatim.openstreetmap.org/search";

  // ── State ────────────────────────────────────────────────────────────────────
  let userLat = null;
  let userLng = null;
  let allShops = [];

  // ── Search bar (always visible, items populated after shops load) ─────────────
  const searchBar = createSearchBarAutocomplete(
    "#map-search-bar",
    function (item) {
      const shop = allShops.find(function (s) {
        return s.barbershop_id === item.id;
      });
      if (shop) map.setView([shop.lat, shop.lng], LOCATION_ZOOM);
    },
    [],
    { placeholder: "Search barbershops..." }
  );

  // ── Map initialisation ───────────────────────────────────────────────────────
  const map = L.map("map", { zoomControl: true }).setView(UK_CENTER, UK_ZOOM);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map);

  // ── DOM refs ─────────────────────────────────────────────────────────────────
  const locationModal = document.getElementById("location-modal");
  const locationInput = document.getElementById("location-input");
  const setLocationBtn = document.getElementById("set-location-btn");
  const useCurrentBtn = document.getElementById("use-current-location-btn");
  const myLocationBtn = document.getElementById("my-location-btn");
  const savePrompt = document.getElementById("save-location-prompt");
  const saveNoBtn = document.getElementById("save-location-no");
  const saveYesBtn = document.getElementById("save-location-yes");
  const locationModalClose = document.getElementById("location-modal-close");

  // ── Location modal ───────────────────────────────────────────────────────────
  function showModal() {
    locationModal.classList.remove("hidden");
    locationInput.value = "";
    locationInput.focus();
  }

  function hideModal() {
    locationModal.classList.add("hidden");
  }

  // Show on page load
  showModal();

  myLocationBtn.addEventListener("click", showModal);
  locationModalClose.addEventListener("click", hideModal);

  // Set location by postcode / address (Nominatim geocoding)
  setLocationBtn.addEventListener("click", geocodeAndZoom);
  locationInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") geocodeAndZoom();
  });

  async function geocodeAndZoom() {
    const query = locationInput.value.trim();
    if (!query) return;

    setLocationBtn.textContent = "Searching…";
    setLocationBtn.disabled = true;

    try {
      const res = await fetch(
        NOMINATIM_URL +
          "?q=" +
          encodeURIComponent(query) +
          "&format=json&limit=1&countrycodes=gb"
      );
      const data = await res.json();

      if (data.length === 0) {
        alert("Location not found. Try a different postcode or address.");
        return;
      }

      userLat = parseFloat(data[0].lat);
      userLng = parseFloat(data[0].lon);
      map.setView([userLat, userLng], LOCATION_ZOOM);
      hideModal();
      showSavePrompt();
    } catch (_) {
      alert("Could not search for location. Check your internet connection.");
    } finally {
      setLocationBtn.textContent = "Set Location";
      setLocationBtn.disabled = false;
    }
  }

  // Use browser geolocation
  useCurrentBtn.addEventListener("click", function () {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }

    useCurrentBtn.textContent = "Locating…";
    useCurrentBtn.disabled = true;

    navigator.geolocation.getCurrentPosition(
      function (pos) {
        userLat = pos.coords.latitude;
        userLng = pos.coords.longitude;
        map.setView([userLat, userLng], LOCATION_ZOOM);
        hideModal();
        showSavePrompt();
        useCurrentBtn.textContent = "Use Current Location";
        useCurrentBtn.disabled = false;
      },
      function () {
        alert("Could not get your location. Please check your browser permissions.");
        useCurrentBtn.textContent = "Use Current Location";
        useCurrentBtn.disabled = false;
      }
    );
  });

  // ── Save location prompt ─────────────────────────────────────────────────────
  function showSavePrompt() {
    savePrompt.classList.remove("hidden");
  }

  function hideSavePrompt() {
    savePrompt.classList.add("hidden");
  }

  saveNoBtn.addEventListener("click", hideSavePrompt);

  saveYesBtn.addEventListener("click", function () {
    // TODO: POST to /api/user/location once auth is implemented
    hideSavePrompt();
  });

  // ── Helpers ──────────────────────────────────────────────────────────────────
  function renderStars(rating) {
    const full = Math.round(rating);
    return "★".repeat(full) + "☆".repeat(5 - full);
  }

  function haversineKm(lat1, lng1, lat2, lng2) {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLng = ((lng2 - lng1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLng / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function formatDistance(km) {
    return km < 1 ? Math.round(km * 1000) + "m" : km.toFixed(1) + "km";
  }

  // ── Barbershop markers ───────────────────────────────────────────────────────
  function buildPopupHtml(shop) {
    const barber = shop.barbers[0] || null;

    const distHtml =
      userLat !== null
        ? '<span class="shop-popup-distance">● ' +
          formatDistance(haversineKm(userLat, userLng, shop.lat, shop.lng)) +
          "</span>"
        : "";

    const photoHtml = barber
      ? barber.profile_image_url
        ? '<img src="' +
          barber.profile_image_url +
          '" alt="' +
          barber.username +
          '" class="shop-popup-photo" />'
        : '<div class="shop-popup-photo-placeholder"></div>'
      : "";

    const barberHtml = barber
      ? '<div class="shop-popup-barber">' +
        photoHtml +
        '<div>' +
        '<div class="shop-popup-barber-name">' +
        barber.username +
        "</div>" +
        '<div class="shop-popup-stars">' +
        renderStars(barber.average_rating) +
        "</div>" +
        "</div>" +
        "</div>"
      : "";

    return (
      '<div class="shop-popup">' +
      '<div class="shop-popup-name">' +
      shop.name +
      "</div>" +
      distHtml +
      barberHtml +
      '<a class="shop-popup-btn" href="/shop/' +
      shop.barbershop_id +
      '">View Shop</a>' +
      "</div>"
    );
  }

  function addMarkers(shops) {
    shops.forEach(function (shop) {
      const marker = L.marker([shop.lat, shop.lng]).addTo(map);
      marker.on("click", function () {
        marker.bindPopup(buildPopupHtml(shop), { maxWidth: 220 }).openPopup();
      });
    });
  }

  // ── Bootstrap ────────────────────────────────────────────────────────────────
  fetch("/api/barbershops")
    .then(function (res) {
      return res.json();
    })
    .then(function (shops) {
      allShops = shops;
      addMarkers(shops);

      // Populate the search bar with the loaded shops
      const shopItems = shops.map(function (s) {
        return { id: s.barbershop_id, type: "barbershop", label: s.name };
      });
      searchBar.setItems(shopItems);
    })
    .catch(function () {
      console.error("Could not load barbershops from /api/barbershops");
    });
})();
