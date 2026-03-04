// Global bootstrap for shared page setup
// Components are imported and used by features/pages, not auto-initialized here

if (document.readyState === "loading") {
	document.addEventListener("DOMContentLoaded", () => {
		// Reserved for future global initialization
	}, { once: true });
}
