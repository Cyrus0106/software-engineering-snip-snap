import { renderUserPromo } from "../components/userPromo.js";

const pageEl = document.querySelector(".barbershop-page");
const shopNameEl = document.getElementById("barbershopName");
const shopMetaEl = document.getElementById("barbershopMeta");
const barberListEl = document.getElementById("barberList");

function renderNoBarbers() {
  if (!barberListEl) return;
  barberListEl.innerHTML = '<p class="barbershop-page__empty">No barbers listed yet.</p>';
}

function renderBarberItem(shopName, barber) {
  const wrapper = document.createElement("article");
  wrapper.className = "barbershop-page__barber";

  const promoMount = document.createElement("div");
  promoMount.className = "barbershop-page__promo";

  renderUserPromo(promoMount, {
    name: barber.username || "Unknown",
    role: "barber",
    barbershop_name: shopName || "",
    profile_image_url: barber.profile_image_url || null,
  });

  const profileLink = document.createElement("a");
  profileLink.className = "barbershop-page__barber-link";
  profileLink.href = `/barber?barber_id=${encodeURIComponent(String(barber.barber_id))}`;
  profileLink.textContent = "View profile";

  wrapper.appendChild(promoMount);
  wrapper.appendChild(profileLink);
  return wrapper;
}

async function initBarbershopPage() {
  if (!pageEl || !barberListEl || !shopNameEl) return;

  const shopId = Number(pageEl.getAttribute("data-barbershop-id"));
  if (!shopId) {
    shopNameEl.textContent = "Barbershop not found";
    renderNoBarbers();
    return;
  }

  try {
    const res = await fetch(`/api/barbershops/${shopId}`, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error(`Failed: ${res.status}`);

    const shop = await res.json();
    const shopName = shop.name || "Unnamed barbershop";
    const barbers = Array.isArray(shop.barbers) ? shop.barbers : [];

    shopNameEl.textContent = shopName;
    shopMetaEl.textContent = [shop.postcode, shop.phone].filter(Boolean).join(" • ");

    barberListEl.textContent = "";
    if (!barbers.length) {
      renderNoBarbers();
      return;
    }

    barbers.forEach((barber) => {
      barberListEl.appendChild(renderBarberItem(shopName, barber));
    });
  } catch (_err) {
    shopNameEl.textContent = "Could not load barbershop";
    renderNoBarbers();
  }
}

initBarbershopPage();
