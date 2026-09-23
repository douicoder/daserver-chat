/* auth.js — Client-side auth helpers */

(function () {
    "use strict";

    window.AppAuth = {
        getToken: function () {
            return window.__ACCESS_TOKEN__ || "";
        },

        getUser: function () {
            return window.__CURRENT_USER__ || null;
        },

        isAdmin: function () {
            var u = this.getUser();
            return u && u.is_admin === true;
        },

        getBackendUrl: function () {
            return window.__BACKEND_URL__ || "http://localhost:5000";
        },

        /* Parse the standard backend error format: { error: { code, message } } */
        parseError: function (body) {
            if (body && body.error && body.error.message) {
                return body.error.message;
            }
            return "An unexpected error occurred.";
        },

        /* Detect 401 from a fetch Response and redirect to login */
        handle401: function (status) {
            if (status === 401) {
                window.__ACCESS_TOKEN__ = "";
                window.__CURRENT_USER__ = null;
                window.location.href = "/login";
                return true;
            }
            return false;
        }
    };
})();
