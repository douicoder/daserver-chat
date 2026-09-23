/* attachments.js — Attachment display helpers (supplements chat.js) */

(function () {
    "use strict";

    var ALLOWED_TYPES = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain", "application/zip"
    ];

    var ALLOWED_EXTENSIONS = [
        "jpg", "jpeg", "png", "gif", "webp", "pdf", "txt", "zip"
    ];

    function validateFile(file) {
        if (!file) return { valid: false, error: "No file selected." };

        var ext = file.name.split(".").pop().toLowerCase();
        if (ALLOWED_EXTENSIONS.indexOf(ext) === -1) {
            return {
                valid: false,
                error: "Unsupported file type. Allowed: " + ALLOWED_EXTENSIONS.join(", ")
            };
        }

        var maxSize = 25 * 1024 * 1024;
        if (file.size > maxSize) {
            return { valid: false, error: "File is too large. Maximum size is 25 MB." };
        }

        return { valid: true };
    }

    function isImageFile(file) {
        if (!file) return false;
        return file.type && file.type.indexOf("image/") === 0;
    }

    function getIconClass(mimeType) {
        if (!mimeType) return "file-icon";
        if (mimeType.indexOf("image/") === 0) return "file-icon image";
        if (mimeType === "application/pdf") return "file-icon pdf";
        if (mimeType === "text/plain") return "file-icon text";
        if (mimeType === "application/zip") return "file-icon zip";
        return "file-icon";
    }

    window.AppAttachments = {
        validateFile: validateFile,
        isImageFile: isImageFile,
        getIconClass: getIconClass,
        ALLOWED_EXTENSIONS: ALLOWED_EXTENSIONS
    };
})();
