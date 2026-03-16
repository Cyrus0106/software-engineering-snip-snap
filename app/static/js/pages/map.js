const mapPinsMount = document.getElementById("mapPinsMount");

function renderEmpty(message) {
  if (!mapPinsMount) return;
  mapPinsMount.innerHTML = `<p class="map-pins__empty">${message}</p>`;
}

function toPin(shop) {
  const shopId = Number(shop.barbershop_id);
  const barberCount = Array.isArray(shop.barbers) ? shop.barbers.length : 0;
  const href = Number.isFinite(shopId) && shopId > 0 ? `/barbershop/${shopId}` : "/map";

  const link = document.createElement("a");
  link.className = "map-pin";
  link.href = href;
  link.setAttribute("aria-label", `Open ${shop.name}`);

  link.innerHTML = `
    <span class="map-pin__dot" aria-hidden="true"></span>
    <span class="map-pin__content">
      <span class="map-pin__name">${shop.name || "Unnamed barbershop"}</span>
      <span class="map-pin__meta">${barberCount} barber${barberCount === 1 ? "" : "s"}</span>
    </span>
  `;

  return link;
}

async function initMapPins() {
  if (!mapPinsMount) return;

  try {
    const res = await fetch("/api/barbershops", { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error(`Failed to load barbershops: ${res.status}`);

    const payload = await res.json();
    const shops = Array.isArray(payload.items) ? payload.items : [];

    if (!shops.length) {
      renderEmpty("No barbershops found.");
      return;
    }

    mapPinsMount.textContent = "";
    shops.forEach((shop) => mapPinsMount.appendChild(toPin(shop)));
  } catch (_err) {
    renderEmpty("Could not load map pins right now.");
  }
}

initMapPins();
