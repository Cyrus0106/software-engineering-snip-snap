// userPromo.js

export function mountUserPromo(containerEl, userId, options) {
    const defaultAvatar = `<svg width='40' height='40' xmlns='http://www.w3.org/2000/svg'><circle cx='20' cy='20' r='20' fill='gray'/></svg>`;
    const loadingSkeleton = document.createElement('div');
    loadingSkeleton.textContent = 'Loading...';
    containerEl.appendChild(loadingSkeleton);

    fetch(`/api/users/${userId}/promo`, { headers: { 'Accept': 'application/json' } })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Clear loading state
            containerEl.removeChild(loadingSkeleton);

            const promoRow = document.createElement('div');
            const avatar = document.createElement('img');
            avatar.src = data.profile_image_url || defaultAvatar;
            avatar.alt = 'User Avatar';
            avatar.style.width = '40px';
            avatar.style.height = '40px';
            avatar.style.borderRadius = '50%';

            const name = document.createElement('strong');
            name.textContent = data.name;

            promoRow.appendChild(avatar);
            promoRow.appendChild(name);

            if (data.role === 'barber' && data.barbershop_name) {
                const barbershopName = document.createElement('div');
                barbershopName.textContent = data.barbershop_name;
                promoRow.appendChild(barbershopName);
            }

            containerEl.appendChild(promoRow);
        })
        .catch(() => {
            // Clear loading state
            containerEl.removeChild(loadingSkeleton);
            const errorRow = document.createElement('div');
            const errorAvatar = document.createElement('img');
            errorAvatar.src = defaultAvatar;
            errorAvatar.alt = 'Default Avatar';
            errorAvatar.style.width = '40px';
            errorAvatar.style.height = '40px';
            errorAvatar.style.borderRadius = '50%';

            const errorName = document.createElement('div');
            errorName.textContent = 'Unknown';

            errorRow.appendChild(errorAvatar);
            errorRow.appendChild(errorName);
            containerEl.appendChild(errorRow);
        });
}

export function initUserPromos(root = document) {
    const promoElements = root.querySelectorAll('.js-user-promo[data-user-id]');
    promoElements.forEach(el => {
        const userId = el.getAttribute('data-user-id');
        mountUserPromo(el, userId);
    });
}