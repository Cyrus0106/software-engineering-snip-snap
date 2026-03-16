import { renderUserPromo } from "./userPromo.js";

export function renderPostImageCard(item) {
  const card = document.createElement("div");
  card.className = "postImageCard";

  // Promo at top
  const promoMount = document.createElement("div");
  promoMount.className = "post-card__promo";
  card.appendChild(promoMount);

  renderUserPromo(promoMount, {
    name: item.promo_name,
    role: item.promo_role,
    barbershop_name: item.promo_barbershop_name,
    profile_image_url: item.promo_profile_image_url,
  }, { avatarSize: 36 });

  // Image
  const media = document.createElement("div");
  media.className = "postImageCard__media";

  const img = document.createElement("img");
  img.className = "postImageCard__img";
  img.src = item.image_url;
  img.loading = "lazy";

  media.appendChild(img);
  card.appendChild(media);

  const meta = document.createElement("div");
  meta.className = "postImageCard__meta";

  // rating
  const avg = Number(item.avg_rating);
  const count = Number(item.rating_count || 0);

  const ratingEl = document.createElement("div");
  ratingEl.className = "postImageCard__rating";

  if (count > 0 && Number.isFinite(avg)) {
    // 0..5
    const pct = Math.max(0, Math.min(100, (avg / 5) * 100));
    ratingEl.innerHTML = `
      <span class="stars" aria-label="Rating ${avg.toFixed(1)} out of 5">
        <span class="stars__bg">★★★★★</span>
        <span class="stars__fg" style="width:${pct}%">★★★★★</span>
      </span>
      <span class="rating__text">${avg.toFixed(1)} (${count})</span>
    `;
  } else {
    ratingEl.textContent = "No ratings";
  }

  meta.appendChild(ratingEl);

  // distance (only if viewer loc exists + shop coords exist)
  const viewer = window.__VIEWER_LOC__;
  const shopLat = Number(item.shop_lat);
  const shopLng = Number(item.shop_lng);

  if (viewer && Number.isFinite(viewer.lat) && Number.isFinite(viewer.lng) && Number.isFinite(shopLat) && Number.isFinite(shopLng)) {
    const km = Number(item.distance_km);
    const distEl = document.createElement("div");
    if (Number.isFinite(km)) {
      distEl.textContent = `${km.toFixed(1)} km`;
    }
    distEl.className = "postImageCard__distance";
    distEl.textContent = `${km.toFixed(1)} km`;
    meta.appendChild(distEl);
  }

  card.appendChild(meta);

  console.log(item);

  return card;
}