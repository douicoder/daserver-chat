/* admin.js — Admin panel logic */

(function () {
    "use strict";

    var token = window.__ACCESS_TOKEN__ || "";
    var backendUrl = window.__BACKEND_URL__ || "http://localhost:5000";
    var currentAdminUser = window.__CURRENT_USER__ || {};

    var $ = function (id) { return document.getElementById(id); };

    var adminLoadingEl = $("adminLoading");
    var adminErrorEl = $("adminError");
    var adminTableEl = $("adminTable");
    var adminTableBodyEl = $("adminTableBody");
    var changePasswordModalEl = $("changePasswordModal");
    var changePasswordUsernameEl = $("changePasswordUsername");
    var newPasswordInputEl = $("newPasswordInput");
    var changePasswordErrorEl = $("changePasswordError");
    var changePasswordSubmitEl = $("changePasswordSubmit");

    var selectedUserId = null;

    function api(path, opts) {
        opts = opts || {};
        var headers = opts.headers || {};
        headers["Content-Type"] = "application/json";
        if (token) headers["Authorization"] = "Bearer " + token;
        return fetch(backendUrl + path, {
            method: opts.method || "GET",
            headers: headers,
            body: opts.body ? JSON.stringify(opts.body) : undefined
        }).then(function (r) {
            if (r.status === 401) {
                window.location.href = "/login";
                return Promise.reject(new Error("Unauthorized"));
            }
            if (r.status === 403) {
                window.location.href = "/chat";
                return Promise.reject(new Error("Forbidden"));
            }
            return r.json().then(function (data) {
                return { status: r.status, data: data };
            });
        });
    }

    function escapeHtml(str) {
        if (!str) return "";
        var d = document.createElement("div");
        d.appendChild(document.createTextNode(str));
        return d.innerHTML;
    }

    function formatDate(isoStr) {
        if (!isoStr) return "—";
        var d = new Date(isoStr);
        return d.toLocaleDateString();
    }

    function showError(msg) {
        adminErrorEl.textContent = msg;
        adminErrorEl.classList.remove("hidden");
    }

    function hideError() {
        adminErrorEl.classList.add("hidden");
    }

    /* ── Load users ────────────────────────────────────────────── */
    function loadUsers() {
        adminLoadingEl.classList.remove("hidden");
        adminTableEl.classList.add("hidden");
        hideError();

        api("/api/admin/users").then(function (res) {
            adminLoadingEl.classList.add("hidden");

            if (res.status !== 200 || !Array.isArray(res.data)) {
                showError("Failed to load users.");
                return;
            }

            renderUsers(res.data);
            adminTableEl.classList.remove("hidden");
        }).catch(function () {
            adminLoadingEl.classList.add("hidden");
            showError("Unable to connect to server.");
        });
    }

    function renderUsers(users) {
        var html = "";
        for (var i = 0; i < users.length; i++) {
            var u = users[i];
            html += "<tr>";
            html += "<td>" + escapeHtml(u.username) + "</td>";
            html += '<td><span class="admin-badge' + (u.is_admin ? " yes" : "") + '">' + (u.is_admin ? "Yes" : "No") + '</span></td>';
            html += "<td>" + formatDate(u.created_at) + "</td>";
            html += "<td>";
            html += '<button class="admin-action-btn" data-uid="' + u.id + '" data-uname="' + escapeHtml(u.username) + '">Change password</button>';
            html += "</td>";
            html += "</tr>";
        }
        adminTableBodyEl.innerHTML = html;

        var btns = adminTableBodyEl.querySelectorAll(".admin-action-btn");
        for (var j = 0; j < btns.length; j++) {
            btns[j].addEventListener("click", function () {
                selectedUserId = this.getAttribute("data-uid");
                var uname = this.getAttribute("data-uname");
                openChangePasswordModal(uname);
            });
        }
    }

    /* ── Change password modal ─────────────────────────────────── */
    function openChangePasswordModal(username) {
        changePasswordUsernameEl.textContent = username;
        newPasswordInputEl.value = "";
        changePasswordErrorEl.classList.add("hidden");
        changePasswordSubmitEl.disabled = false;
        changePasswordSubmitEl.textContent = "Update Password";
        changePasswordModalEl.classList.remove("hidden");
        newPasswordInputEl.focus();
    }

    function closeChangePasswordModal() {
        changePasswordModalEl.classList.add("hidden");
    }

    function onChangePassword() {
        var newPass = newPasswordInputEl.value;
        if (!newPass || newPass.length < 6) {
            changePasswordErrorEl.textContent = "Password must be at least 6 characters.";
            changePasswordErrorEl.classList.remove("hidden");
            return;
        }

        changePasswordSubmitEl.disabled = true;
        changePasswordSubmitEl.textContent = "Updating...";
        changePasswordErrorEl.classList.add("hidden");

        api("/api/admin/users/" + selectedUserId + "/password", {
            method: "POST",
            body: { new_password: newPass }
        }).then(function (res) {
            if (res.status === 200) {
                closeChangePasswordModal();
            } else {
                var msg = "Failed to change password.";
                if (res.data && res.data.error && res.data.error.message) {
                    msg = res.data.error.message;
                }
                changePasswordErrorEl.textContent = msg;
                changePasswordErrorEl.classList.remove("hidden");
                changePasswordSubmitEl.disabled = false;
                changePasswordSubmitEl.textContent = "Update Password";
            }
        }).catch(function () {
            changePasswordErrorEl.textContent = "Unable to connect to server.";
            changePasswordErrorEl.classList.remove("hidden");
            changePasswordSubmitEl.disabled = false;
            changePasswordSubmitEl.textContent = "Update Password";
        });
    }

    /* ── Init ──────────────────────────────────────────────────── */
    function init() {
        loadUsers();

        $("changePasswordModalClose").addEventListener("click", closeChangePasswordModal);
        changePasswordModalEl.addEventListener("click", function (e) {
            if (e.target === changePasswordModalEl) closeChangePasswordModal();
        });
        changePasswordSubmitEl.addEventListener("click", onChangePassword);
        newPasswordInputEl.addEventListener("keydown", function (e) {
            if (e.key === "Enter") onChangePassword();
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
