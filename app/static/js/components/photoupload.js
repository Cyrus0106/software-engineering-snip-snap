function createPhotoUploadComponent(mountElement, config = {}) {

    const maxPhotos = config.maxPhotos || 2;
    const onChange = config.onChange || function() {};

    let selectedFiles = [];

    // Create structure inside mount
    mountElement.innerHTML = `
        <div class="photo-upload">
            <button class="photo-upload-btn">Upload photo</button>

            <div class="photo-upload-popup hidden">
                <input type="file" class="photo-upload-input" accept="image/*" ${maxPhotos > 1 ? "multiple" : ""}>
                <div class="photo-upload-preview"></div>
                <div class="photo-upload-limit-message"></div>
            </div>
        </div>
    `;

    const button = mountElement.querySelector(".photo-upload-btn");
    const popup = mountElement.querySelector(".photo-upload-popup");
    const input = mountElement.querySelector(".photo-upload-input");
    const preview = mountElement.querySelector(".photo-upload-preview");
    const limitMessage = mountElement.querySelector(".photo-upload-limit-message");

    button.addEventListener("click", () => {
        button.style.display = "none";
        popup.classList.remove("hidden");
    });

    input.addEventListener("change", (event) => {
        let files = Array.from(event.target.files);

        if (selectedFiles.length + files.length > maxPhotos) {
            files = files.slice(0, maxPhotos - selectedFiles.length);
        }

        selectedFiles = selectedFiles.concat(files);

        renderPreview();
        onChange(selectedFiles);

        if (selectedFiles.length >= maxPhotos) {
            input.disabled = true;
            limitMessage.textContent = "Maximum number of photos reached.";
        }
    });

    function renderPreview() {
    preview.innerHTML = "";

    selectedFiles.forEach((file, index) => {

        const reader = new FileReader();

        reader.onload = function (e) {

            const wrapper = document.createElement("div");
            wrapper.className = "preview-wrapper";

            const img = document.createElement("img");
            img.src = e.target.result;
            img.className = "preview-image";

            const removeBtn = document.createElement("button");
            removeBtn.className = "remove-btn";
            removeBtn.innerHTML = "×";

            removeBtn.addEventListener("click", function () {
                selectedFiles.splice(index, 1);
                input.disabled = false;
                limitMessage.textContent = "";
                renderPreview();
                onChange(selectedFiles);
            });

            wrapper.appendChild(img);
            wrapper.appendChild(removeBtn);
            preview.appendChild(wrapper);
        };

        reader.readAsDataURL(file);
    });
}