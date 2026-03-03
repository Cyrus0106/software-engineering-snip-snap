document.addEventListener("DOMContentLoaded", function () {

    const mount = document.getElementById("photoUploadMount");

    createPhotoUploadComponent(mount, {
        maxPhotos: 3,
        onChange: function(files) {
            console.log("Selected files:", files);
        }
    });

});