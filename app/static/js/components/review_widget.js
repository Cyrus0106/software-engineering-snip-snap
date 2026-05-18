/**
 * ReviewWidget - A reusable component for displaying and managing reviews for a barber.
 * Handles loading reviews from the API, displaying them with star ratings, and submitting new reviews.
 * Supports nested replies where staff can respond to customer reviews.
 */
export class ReviewWidget {
     /**
     * Constructor initializes the review widget with DOM container and barber ID.
     *
     * @param {string} containerId - The ID of the HTML element where the widget will be mounted
     * @param {string|number} barberId - The ID of the barber whose reviews to display
     */
    constructor(containerId, barberId) {
        this.container = document.getElementById(containerId);
        this.barberId = barberId;
        this.reviews = [];
        this.selectedRating = 0;
        this.renderBase();
        this.loadReviews();
    }

    async loadReviews() {
        if (!this.barberId) {
            this.reviews = [];
            this.renderReviews();
            return;
        }
        try {
            const res = await fetch(`/api/reviews/${this.barberId}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            this.reviews = Array.isArray(data) ? data : [];
        } catch (e) {
            this.reviews = [];
            console.error("Failed to load reviews:", e);
        }
        this.renderReviews();
    }

    renderBase() {
        this.container.innerHTML = `
            <div class="widget-container">
                <div class="widget-header">
                    <span>Reviews</span>
                    <div class="add-review-btn" id="openModal">＋</div>
                </div>
                <div class="review-list" id="reviewList"><p class="review-loading">Loading reviews…</p></div>
            </div>
            <div class="modal-overlay" id="modal" style="display:none">
                <div class="modal-content">
                    <div class="modal-title">Leave a review</div>
                    <div class="star-input" id="starInput">
                        <span data-v="1">★</span><span data-v="2">★</span><span data-v="3">★</span><span data-v="4">★</span><span data-v="5">★</span>
                    </div>
                    <textarea id="reviewText" placeholder="Describe your experience..."></textarea>
                    <p class="modal-error" id="modalError" style="display:none;color:red;font-size:13px;"></p>
                    <div class="modal-btns">
                        <button class="btn-upload" id="submitReview">Submit</button>
                        <button class="btn-cancel" id="closeModal">Cancel</button>
                    </div>
                </div>
            </div>
        `;
        this.setupEventListeners();
    }

    setupEventListeners() {
        const modal = this.container.querySelector("#modal");
        const errorEl = this.container.querySelector("#modalError");

        this.container.querySelector("#openModal").onclick = () => {
            errorEl.style.display = "none";
            modal.style.display = "flex";
        };
        this.container.querySelector("#closeModal").onclick = () => {
            modal.style.display = "none";
            this.resetModal();
        };

        const stars = this.container.querySelectorAll("#starInput span");
        stars.forEach(s => {
            s.onclick = () => {
                this.selectedRating = parseInt(s.dataset.v);
                stars.forEach(st => st.classList.toggle("active", parseInt(st.dataset.v) <= this.selectedRating));
            };
        });

        this.container.querySelector("#submitReview").onclick = async () => {
            const text = this.container.querySelector("#reviewText").value.trim();
            errorEl.style.display = "none";

            if (!text || this.selectedRating === 0) {
                errorEl.textContent = "Please select a star rating and write a comment.";
                errorEl.style.display = "block";
                return;
            }

            try {
                const res = await fetch("/api/reviews/submit", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ barber_id: this.barberId, rating: this.selectedRating, comment: text }),
                });
                const data = await res.json();
                if (!res.ok || !data.ok) throw new Error(data.error || "Submission failed");
                modal.style.display = "none";
                this.resetModal();
                await this.loadReviews();
            } catch (e) {
                errorEl.textContent = e.message.includes("login") || e.message.includes("401")
                    ? "You must be logged in to leave a review."
                    : e.message || "Could not submit review.";
                errorEl.style.display = "block";
            }
        };
    }

    resetModal() {
        this.selectedRating = 0;
        this.container.querySelector("#reviewText").value = "";
        this.container.querySelectorAll("#starInput span").forEach(s => s.classList.remove("active"));
    }

    renderReviews() {
        const list = this.container.querySelector("#reviewList");

        if (this.reviews.length === 0) {
            list.innerHTML = "<p>No reviews yet. Be the first!</p>";
            return;
        }

        // Group replies under their parent reviews
        const topLevel = this.reviews.filter(r => !r.parent_review_id);
        const repliesMap = {};
        this.reviews.filter(r => r.parent_review_id).forEach(r => {
            if (!repliesMap[r.parent_review_id]) repliesMap[r.parent_review_id] = [];
            repliesMap[r.parent_review_id].push(r);
        });

        list.innerHTML = topLevel.map(rev => {
            const replies = repliesMap[rev.review_id] || [];
            const starsHtml = rev.rating
                ? `<div class="review-stars">${"★".repeat(rev.rating)}${"☆".repeat(5 - rev.rating)}</div>`
                : "";
            const repliesHtml = replies.map(rep => `
                <div class="reply-item">
                    <span class="review-name">${this._esc(rep.username)}</span>
                    <div class="review-text">${this._esc(rep.text)}</div>
                </div>
            `).join("");

            return `
                <div class="review-card">
                    <div class="review-name">${this._esc(rev.username)}</div>
                    ${starsHtml}
                    <div class="review-text">${this._esc(rev.text)}</div>
                    ${repliesHtml ? `<div class="replies-list">${repliesHtml}</div>` : ""}
                </div>
            `;
        }).join("");
    }

    _esc(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }
}

if (typeof window !== "undefined") {
    window.ReviewWidget = ReviewWidget;
}
