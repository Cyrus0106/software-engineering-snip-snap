document.addEventListener("DOMContentLoaded", function () {
    const mount = document.getElementById("photoUploadSingle");

    createPhotoUploadComponent(mount, function(files) {
        console.log("Selected files:", files);
    });
});