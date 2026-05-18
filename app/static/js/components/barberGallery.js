import { renderGalleryGrid } from "./galleryGrid.js";
import { renderBarberGalleryCard } from "./barberGalleryCard.js";
/**
 * Initializes and renders a gallery of photos for a specific barber.
 * Fetches photos from the API and displays them in a 2-column grid layout.
 *
 * @param {Object} options - Configuration object
 * @param {HTMLElement} options.mountEl - The DOM element where the gallery will be rendered
 * @param {string|number} options.barberId - The unique identifier of the barber
 */
export async function initBarberGallery({ mountEl, barberId }) {
  try {
     // Fetch photos from the barber API endpoint
    const response = await fetch(`/api/barber/${barberId}/photos`);
    
     // Handle failed API requests (non-2xx status codes)
    if (!response.ok) {
      console.error("Failed to fetch barber photos:", response.status);
      mountEl.innerHTML = "<p>No photos available</p>";
      return;
    }

    const photos = await response.json();

    if (!photos || photos.length === 0) {
      mountEl.innerHTML = "<p>No photos yet</p>";
      return;
    }
  // Render the photos in a responsive grid layout with 2 columns
    renderGalleryGrid({
      mountEl,
      items: photos,
      columns: 2,
      renderItem: renderBarberGalleryCard
    });
  } catch (error) {
     // Handle network errors or unexpected failures
    console.error("Error loading barber gallery:", error);
    mountEl.innerHTML = "<p>Error loading photos</p>";
  }
}
/**
 * Initializes and renders a gallery of photos for a specific barbershop.
 * Fetches photos from the API and displays them in a 2-column grid layout.
 * Similar to initBarberGallery but operates at the barbershop level.
 *
 * @param {Object} options - Configuration object
 * @param {HTMLElement} options.mountEl - The DOM element where the gallery will be rendered
 * @param {string|number} options.barbershopId - The unique identifier of the barbershop
 */
export async function initBarbershopGallery({ mountEl, barbershopId }) {
  try {
    const response = await fetch(`/api/barbershop/${barbershopId}/photos`);
    if (!response.ok) {
      console.error("Failed to fetch barbershop photos:", response.status);
      mountEl.innerHTML = "<p>No photos available</p>";
      return;
    }

    const photos = await response.json();

    if (!photos || photos.length === 0) {
      mountEl.innerHTML = "<p>No photos yet</p>";
      return;
    }

    renderGalleryGrid({
      mountEl,
      items: photos,
      columns: 2,
      renderItem: renderBarberGalleryCard
    });
  } catch (error) {
    console.error("Error loading barbershop gallery:", error);
    mountEl.innerHTML = "<p>Error loading photos</p>";
  }
}
