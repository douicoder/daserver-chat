/* chat.js — Main chat application logic */

(function () {
    "use strict";

    var token = window.__ACCESS_TOKEN__ || "";
    var currentUser = window.__CURRENT_USER__ || {};
    var backendUrl = window.__BACKEND_URL__ || "http://localhost:5000";

    /* ── State ─────────────────────────────────────────────────── */
    var conversations = [];
    var activeConversationId = null;
    var messages = {};
    var currentPage = {};
    var totalPages = {};
    var loadingMessages = false;
    var selectedGroupMembers = [];
    var pendingAttachmentId = null;
    var pendingAttachmentName = null;

    /* ── DOM refs ──────────────────────────────────────────────── */
    var $ = function (id) { return document.getElementById(id); };

    var conversationListEl = $("conversationList");
    var emptyStateEl = $("emptyState");
    var chatViewEl = $("chatView");
    var chatHeaderNameEl = $("chatHeaderName");
    var chatHeaderEl = $("chatHeader");
    var messagesListEl = $("messagesList");
    var messagesContainerEl = $("messagesContainer");
    var messageInputEl = $("messageInput");
    var sendBtnEl = $("sendBtn");
    var attachBtnEl = $("attachBtn");
    var fileInputEl = $("fileInput");
    var attachmentPreviewEl = $("attachmentPreview");
    var attachmentPreviewNameEl = $("attachmentPreviewName");
    var removeAttachmentEl = $("removeAttachment");
    var backBtnEl = $("backBtn");
    var groupInfoBtnEl = $("groupInfoBtn");
    var loadMoreIndicatorEl = $("loadMoreIndicator");

    /* Modals */
    var newChatModalEl = $("newChatModal");
    var userSearchModalEl = $("userSearchModal");
    var createGroupModalEl = $("createGroupModal");
    var groupInfoModalEl = $("groupInfoModal");
    var renameGroupModalEl = $("renameGroupModal");
    var addMemberModalEl = $("addMemberModal");

    /* ── Helpers ───────────────────────────────────────────────── */
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
            return r.json().then(function (data) {
                return { status: r.status, data: data };
            });
        });
    }

    function apiUpload(file) {
        var form = new FormData();
        form.append("file", file);
        var headers = {};
        if (token) headers["Authorization"] = "Bearer " + token;
        return fetch(backendUrl + "/api/attachments", {
            method: "POST",
            headers: headers,
            body: form
        }).then(function (r) {
            if (r.status === 401) {
                window.location.href = "/login";
                return Promise.reject(new Error("Unauthorized"));
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

    function formatTime(isoStr) {
        if (!isoStr) return "";
        var d = new Date(isoStr);
        var h = d.getHours();
        var m = d.getMinutes();
        return (h < 10 ? "0" : "") + h + ":" + (m < 10 ? "0" : "") + m;
    }

    function formatDate(isoStr) {
        if (!isoStr) return "";
        var d = new Date(isoStr);
        var now = new Date();
        var diff = now - d;
        if (diff < 86400000 && d.getDate() === now.getDate()) return "Today";
        var yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        if (d.getDate() === yesterday.getDate() && d.getMonth() === yesterday.getMonth() && d.getFullYear() === yesterday.getFullYear()) return "Yesterday";
        return d.toLocaleDateString();
    }

    function formatFileSize(bytes) {
        if (!bytes) return "0 B";
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / 1048576).toFixed(1) + " MB";
    }

    function getOtherUserName(conv) {
        if (conv.type !== "DIRECT" || !conv.members) return conv.name || "Unknown";
        for (var i = 0; i < conv.members.length; i++) {
            if (conv.members[i].id !== currentUser.id) {
                return conv.members[i].username;
            }
        }
        return "Unknown";
    }

    function getConversationDisplayName(conv) {
        if (conv.type === "DIRECT") return getOtherUserName(conv);
        return conv.name || "Unnamed Group";
    }

    function isGroupOwner(conv) {
        return conv.type === "GROUP" && conv.owner_id === currentUser.id;
    }

    function showModal(el) {
        el.classList.remove("hidden");
    }

    function hideModal(el) {
        el.classList.add("hidden");
    }

    /* ── Conversations ─────────────────────────────────────────── */
    function loadConversations() {
        conversationListEl.innerHTML = '<div class="loading-text">Loading conversations...</div>';
        api("/api/conversations").then(function (res) {
            if (res.status === 200 && Array.isArray(res.data)) {
                conversations = res.data;
                renderConversationList();
                if (window.ChatSocket) window.ChatSocket.connect();
            } else {
                conversationListEl.innerHTML = '<div class="empty-conversations">Failed to load conversations.</div>';
            }
        }).catch(function () {
            conversationListEl.innerHTML = '<div class="empty-conversations">Unable to connect to server.</div>';
        });
    }

    function renderConversationList() {
        if (conversations.length === 0) {
            conversationListEl.innerHTML = '<div class="empty-conversations"><div class="empty-conversations-icon">💬</div><div>No conversations yet.<br>Start a new chat!</div></div>';
            return;
        }
        var html = "";
        for (var i = 0; i < conversations.length; i++) {
            var conv = conversations[i];
            var name = getConversationDisplayName(conv);
            var isActive = conv.id === activeConversationId;
            var cls = "conversation-item" + (isActive ? " active" : "");
            var hasUnread = conv.__unread ? true : false;
            var unread = hasUnread ? " conversation-unread" : "";
            var initial = (name || "?").charAt(0).toUpperCase();
            var avatarCls = "conv-avatar" + (conv.type === "GROUP" ? " group" : "");
            html += '<div class="' + cls + unread + '" data-id="' + conv.id + '" role="button" tabindex="0">';
            html += '<div class="' + avatarCls + '">' + escapeHtml(initial) + '</div>';
            html += '<div class="conversation-meta">';
            html += '<div class="conversation-top-row"><span class="conversation-name">' + escapeHtml(name) + '</span>';
            if (hasUnread) html += '<span class="unread-dot" aria-label="Unread"></span>';
            html += '</div>';
            var preview = getConversationPreview(conv);
            if (preview) {
                html += '<div class="conversation-preview">' + escapeHtml(preview) + '</div>';
            }
            html += '</div>';
            html += '</div>';
        }
        conversationListEl.innerHTML = html;

        var items = conversationListEl.querySelectorAll(".conversation-item");
        for (var j = 0; j < items.length; j++) {
            items[j].addEventListener("click", onConversationClick);
            items[j].addEventListener("keydown", function (e) {
                if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onConversationClick(e); }
            });
        }
    }

    function getConversationPreview(conv) {
        if (!conv.__lastMessage) return "";
        var msg = conv.__lastMessage;
        var sender = msg.sender_username === currentUser.username ? "You" : msg.sender_username;
        var text = msg.content || (msg.attachment ? "[attachment]" : "");
        if (text.length > 40) text = text.substring(0, 40) + "…";
        return sender + ": " + text;
    }

    function onConversationClick(e) {
        var el = e.currentTarget;
        var id = el.getAttribute("data-id");
        openConversation(id);
    }

    function openConversation(id) {
        activeConversationId = id;
        var conv = getConversationById(id);
        if (!conv) return;

        conv.__unread = false;
        emptyStateEl.classList.add("hidden");
        chatViewEl.classList.remove("hidden");
        chatHeaderNameEl.textContent = getConversationDisplayName(conv);
        var sub = $("chatHeaderSub");
        if (sub) {
            if (conv.type === "GROUP") {
                var n = (conv.members || []).length;
                sub.textContent = n + (n === 1 ? " member" : " members");
            } else {
                sub.textContent = "Direct message";
            }
        }
        var avatarEl = $("chatHeaderAvatar");
        if (avatarEl) {
            var nm = getConversationDisplayName(conv) || "?";
            avatarEl.textContent = nm.charAt(0).toUpperCase();
        }
        groupInfoBtnEl.style.display = conv.type === "GROUP" ? "" : "none";
        messagesListEl.innerHTML = '<div class="messages-loading">Loading messages...</div>';
        currentPage[id] = 0;
        totalPages[id] = 1;
        messages[id] = messages[id] || [];

        if (window.innerWidth <= 768) {
            $("sidebar").classList.add("hidden-mobile");
        }

        // Join the socket room immediately so real-time echoes arrive,
        // especially for conversations created moments ago.
        try {
            if (window.ChatSocket) window.ChatSocket.joinConversation(id);
        } catch (e) { /* ignore */ }

        renderConversationList();
        loadMessages(id, 1);
    }

    function getConversationById(id) {
        for (var i = 0; i < conversations.length; i++) {
            if (conversations[i].id === id) return conversations[i];
        }
        return null;
    }

    function updateConversationListPreview(convId, msg) {
        for (var i = 0; i < conversations.length; i++) {
            if (conversations[i].id === convId) {
                conversations[i].__lastMessage = msg;
                break;
            }
        }
        renderConversationList();
    }

    /* ── Messages ──────────────────────────────────────────────── */
    function loadMessages(convId, page) {
        if (loadingMessages) return;
        loadingMessages = true;
        loadMoreIndicatorEl.classList.remove("hidden");

        api("/api/conversations/" + convId + "/messages?page=" + page + "&limit=50").then(function (res) {
            loadingMessages = false;
            loadMoreIndicatorEl.classList.add("hidden");

            if (res.status !== 200 || !res.data) return;

            var data = res.data;
            var msgs = data.messages || [];
            var pag = data.pagination || {};
            totalPages[convId] = pag.total_pages || 1;
            currentPage[convId] = page;

            if (convId !== activeConversationId) return;

            if (!messages[convId]) messages[convId] = [];
            var existingIds = {};
            for (var i = 0; i < messages[convId].length; i++) {
                existingIds[messages[convId][i].id] = true;
            }
            for (var j = 0; j < msgs.length; j++) {
                if (!existingIds[msgs[j].id]) {
                    messages[convId].push(msgs[j]);
                }
            }

            sortMessages(convId);
            renderMessages(convId, page === 1);

            if (page > 1) {
                loadMoreIndicatorEl.classList.remove("hidden");
                setTimeout(function () {
                    loadMoreIndicatorEl.classList.add("hidden");
                }, 300);
            }
        }).catch(function () {
            loadingMessages = false;
            loadMoreIndicatorEl.classList.add("hidden");
        });
    }

    function sortMessages(convId) {
        messages[convId].sort(function (a, b) {
            return new Date(a.created_at) - new Date(b.created_at);
        });
    }

    function renderMessages(convId, scrollToBottom) {
        if (convId !== activeConversationId) return;
        var msgs = messages[convId] || [];
        if (msgs.length === 0) {
            messagesListEl.innerHTML = '<div class="messages-empty"><div class="messages-empty-icon">👋</div><div>No messages yet.<br>Say hello!</div></div>';
            return;
        }
        var html = "";

        var prevSender = null;
        var prevDate = null;

        for (var i = 0; i < msgs.length; i++) {
            var msg = msgs[i];
            var msgDate = formatDate(msg.created_at);
            var isSelf = msg.sender_id === currentUser.id;

            if (msgDate !== prevDate) {
                html += '<div class="message-date-divider"><span>' + escapeHtml(msgDate) + '</span></div>';
                prevSender = null;
                prevDate = msgDate;
            }

            var showSender = msg.sender_id !== prevSender;
            var rowCls = "message-row" + (isSelf ? " self" : " other") + (showSender ? " show-sender" : " grouped");
            html += '<div class="' + rowCls + '">';
            if (!isSelf) {
                var initial = (msg.sender_username || "?").charAt(0).toUpperCase();
                if (showSender) {
                    html += '<div class="msg-avatar">' + escapeHtml(initial) + '</div>';
                } else {
                    html += '<div class="msg-avatar msg-avatar-spacer"></div>';
                }
            }
            html += '<div class="message-group" data-id="' + msg.id + '">';
            if (showSender) {
                html += '<div class="message-header">';
                if (!isSelf) {
                    html += '<span class="message-sender">' + escapeHtml(msg.sender_username) + '</span>';
                }
                html += '<span class="message-time">' + formatTime(msg.created_at) + '</span>';
                html += '</div>';
            }

            if (msg.content) {
                html += '<div class="message-bubble' + (isSelf ? ' self' : '') + '">' + escapeHtml(msg.content) + '</div>';
            } else if (!msg.attachment) {
                html += '<div class="message-bubble' + (isSelf ? ' self' : '') + ' message-empty-content"></div>';
            }

            if (msg.attachment) {
                html += renderAttachmentHtml(msg.attachment);
            }

            html += '</div>';
            html += '</div>';
            prevSender = msg.sender_id;
        }

        messagesListEl.innerHTML = html;

        if (scrollToBottom) {
            requestAnimationFrame(function () {
                messagesContainerEl.scrollTop = messagesContainerEl.scrollHeight;
            });
        }
    }

    function renderAttachmentHtml(att) {
        var isImage = att.mime_type && att.mime_type.indexOf("image/") === 0;
        var fileUrl = "/attachments/" + att.id;
        var html = '<div class="message-attachment">';
        if (isImage) {
            html += '<a href="' + fileUrl + '" target="_blank" rel="noopener"><img src="' + fileUrl + '" alt="' + escapeHtml(att.original_filename) + '" loading="lazy"></a>';
        }
        var linkUrl = isImage ? fileUrl : (fileUrl + "?download=1");
        var dlAttr = isImage ? "" : " download";
        html += '<a href="' + linkUrl + '" target="_blank" rel="noopener"' + dlAttr + '>' + escapeHtml(att.original_filename) + '</a>';
        html += '<span class="attachment-meta">' + escapeHtml(att.mime_type || "file") + ' · ' + formatFileSize(att.size) + '</span>';
        html += '</div>';
        return html;
    }

    function appendMessage(msg) {
        if (!activeConversationId) return;
        if (!messages[activeConversationId]) messages[activeConversationId] = [];

        var existingIds = {};
        for (var i = 0; i < messages[activeConversationId].length; i++) {
            existingIds[messages[activeConversationId][i].id] = true;
        }
        if (existingIds[msg.id]) return;

        messages[activeConversationId].push(msg);
        sortMessages(activeConversationId);
        renderMessages(activeConversationId, true);
    }

    function onMessagesScroll() {
        if (loadingMessages) return;
        if (!activeConversationId) return;
        var page = currentPage[activeConversationId] || 1;
        var total = totalPages[activeConversationId] || 1;
        if (page >= total) return;
        if (messagesContainerEl.scrollTop < 200) {
            var oldHeight = messagesContainerEl.scrollHeight;
            loadMessages(activeConversationId, page + 1);
            requestAnimationFrame(function () {
                messagesContainerEl.scrollTop = messagesContainerEl.scrollHeight - oldHeight;
            });
        }
    }

    /* ── Send message ──────────────────────────────────────────── */
    function sendMessage(content, attachmentId) {
        if (!activeConversationId) return;
        var convId = activeConversationId;
        sendBtnEl.disabled = true;

        var payload = { conversation_id: convId };
        if (content) payload.content = content;
        if (attachmentId) payload.attachment_id = attachmentId;

        // Capture message count so we can detect a missing socket echo.
        var beforeCount = (messages[convId] || []).length;

        if (window.ChatSocket && window.ChatSocket.isConnected()) {
            var emitted = window.ChatSocket.sendMessage(payload.content || null, payload.attachment_id || null);
            messageInputEl.value = "";
            autoResizeInput();
            clearAttachment();
            sendBtnEl.disabled = false;
            if (emitted !== false) {
                // Safety net: if the real-time echo does not arrive within
                // 2.5s (e.g. room join race on a brand-new conversation),
                // fall back to a REST fetch so the message appears without
                // requiring a manual refresh.
                setTimeout(function () {
                    if (convId !== activeConversationId) return;
                    var after = (messages[convId] || []).length;
                    if (after <= beforeCount) {
                        loadMessages(convId, 1);
                    }
                }, 2500);
                return;
            }
        }
        api("/api/conversations/" + convId + "/messages", {
                method: "POST",
                body: { content: content || "", attachment_id: attachmentId || null }
            }).then(function (res) {
                if (res.status === 201 && res.data) {
                    appendMessage(res.data);
                    updateConversationListPreview(convId, res.data);
                } else {
                    var errMsg = AppAuth.parseError(res.data);
                    alert(errMsg);
                }
                messageInputEl.value = "";
                autoResizeInput();
                clearAttachment();
                sendBtnEl.disabled = false;
            }).catch(function () {
                sendBtnEl.disabled = false;
            });
    }

    function onSendClick() {
        var content = messageInputEl.value.trim();
        if (!content && !pendingAttachmentId) return;
        sendMessage(content, pendingAttachmentId);
    }

    function onInputKeyDown(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSendClick();
        }
    }

    function autoResizeInput() {
        messageInputEl.style.height = "auto";
        messageInputEl.style.height = Math.min(messageInputEl.scrollHeight, 120) + "px";
        sendBtnEl.disabled = !messageInputEl.value.trim() && !pendingAttachmentId;
    }

    /* ── Attachments ───────────────────────────────────────────── */
    function onAttachClick() {
        fileInputEl.click();
    }

    function onFileSelected(e) {
        var file = e.target.files[0];
        if (!file) return;
        attachmentPreviewEl.classList.remove("hidden");
        attachmentPreviewNameEl.textContent = file.name + " (" + formatFileSize(file.size) + ")";
        sendBtnEl.disabled = true;

        apiUpload(file).then(function (res) {
            if (res.status === 201 && res.data && res.data.id) {
                pendingAttachmentId = res.data.id;
                pendingAttachmentName = res.data.original_filename;
                sendBtnEl.disabled = !messageInputEl.value.trim() && !pendingAttachmentId;
            } else {
                alert(AppAuth.parseError(res.data));
                clearAttachment();
            }
        }).catch(function () {
            alert("Upload failed.");
            clearAttachment();
        });

        fileInputEl.value = "";
    }

    function clearAttachment() {
        pendingAttachmentId = null;
        pendingAttachmentName = null;
        attachmentPreviewEl.classList.add("hidden");
        attachmentPreviewNameEl.textContent = "";
        sendBtnEl.disabled = !messageInputEl.value.trim();
    }

    /* ── New Chat Modal ────────────────────────────────────────── */
    function onNewChatClick() {
        showModal(newChatModalEl);
    }

    function onNewDirectClick() {
        hideModal(newChatModalEl);
        $("userSearchInput").value = "";
        $("userSearchResults").innerHTML = "";
        showModal(userSearchModalEl);
        $("userSearchInput").focus();
    }

    function onNewGroupClick() {
        hideModal(newChatModalEl);
        $("groupNameInput").value = "";
        $("groupMemberSearchInput").value = "";
        $("groupMemberResults").innerHTML = "";
        $("selectedMembers").innerHTML = "";
        selectedGroupMembers = [];
        $("createGroupSubmit").disabled = true;
        showModal(createGroupModalEl);
        $("groupNameInput").focus();
    }

    /* ── User Search ───────────────────────────────────────────── */
    var searchTimeout = null;

    function onUserSearchInput(e) {
        clearTimeout(searchTimeout);
        var q = e.target.value.trim();
        if (!q) {
            $("userSearchResults").innerHTML = "";
            return;
        }
        searchTimeout = setTimeout(function () {
            searchUsers(q, "userSearchResults", function (user) {
                hideModal(userSearchModalEl);
                createDirectConversation(user.id);
            });
        }, 300);
    }

    function searchUsers(query, resultsId, onSelect) {
        var resultsEl = $(resultsId);
        resultsEl.innerHTML = '<div class="user-search-empty">Searching...</div>';

        api("/api/users/search?q=" + encodeURIComponent(query)).then(function (res) {
            if (res.status !== 200 || !Array.isArray(res.data)) {
                resultsEl.innerHTML = '<div class="user-search-empty">Search failed.</div>';
                return;
            }
            var users = res.data.filter(function (u) { return u.id !== currentUser.id; });
            if (users.length === 0) {
                resultsEl.innerHTML = '<div class="user-search-empty">No users found.</div>';
                return;
            }
            var html = "";
            for (var i = 0; i < users.length; i++) {
                html += '<div class="user-search-item" data-id="' + users[i].id + '" data-name="' + escapeHtml(users[i].username) + '">';
                html += '<span class="user-search-name">' + escapeHtml(users[i].username) + '</span>';
                html += '</div>';
            }
            resultsEl.innerHTML = html;
            var items = resultsEl.querySelectorAll(".user-search-item");
            for (var j = 0; j < items.length; j++) {
                items[j].addEventListener("click", function () {
                    var uid = this.getAttribute("data-id");
                    var uname = this.getAttribute("data-name");
                    onSelect({ id: uid, username: uname });
                });
            }
        }).catch(function () {
            resultsEl.innerHTML = '<div class="user-search-empty">Unable to connect to server.</div>';
        });
    }

    /* ── Create Direct Conversation ────────────────────────────── */
    function createDirectConversation(userId) {
        api("/api/conversations/direct", {
            method: "POST",
            body: { user_id: userId }
        }).then(function (res) {
            if ((res.status === 200 || res.status === 201) && res.data && res.data.id) {
                upsertConversation(res.data);
                try {
                    if (window.ChatSocket) window.ChatSocket.joinConversation(res.data.id);
                } catch (e) { /* ignore */ }
                openConversation(res.data.id);
            } else {
                alert(AppAuth.parseError(res.data));
            }
        }).catch(function () {
            alert("Failed to create conversation.");
        });
    }

    function fetchAndUpsertConversation(convId, cb) {
        api("/api/conversations/" + convId).then(function (res) {
            if (res.status === 200 && res.data && res.data.id) {
                upsertConversation(res.data);
                try {
                    if (window.ChatSocket) window.ChatSocket.joinConversation(res.data.id);
                } catch (e) { /* ignore */ }
            }
            if (cb) cb();
        }).catch(function () {
            if (cb) cb();
        });
    }

    function upsertConversation(conv) {
        for (var i = 0; i < conversations.length; i++) {
            if (conversations[i].id === conv.id) {
                conversations[i] = conv;
                renderConversationList();
                return;
            }
        }
        conversations.unshift(conv);
        renderConversationList();
    }

    /* ── Create Group ──────────────────────────────────────────── */
    function onGroupMemberSearch(e) {
        clearTimeout(searchTimeout);
        var q = e.target.value.trim();
        if (!q) {
            $("groupMemberResults").innerHTML = "";
            return;
        }
        searchTimeout = setTimeout(function () {
            searchUsers(q, "groupMemberResults", function (user) {
                addSelectedMember(user);
            });
        }, 300);
    }

    function addSelectedMember(user) {
        for (var i = 0; i < selectedGroupMembers.length; i++) {
            if (selectedGroupMembers[i].id === user.id) return;
        }
        selectedGroupMembers.push(user);
        renderSelectedMembers();
        $("groupMemberSearchInput").value = "";
        $("groupMemberResults").innerHTML = "";
        $("createGroupSubmit").disabled = !$("groupNameInput").value.trim();
    }

    function removeSelectedMember(userId) {
        selectedGroupMembers = selectedGroupMembers.filter(function (m) { return m.id !== userId; });
        renderSelectedMembers();
        $("createGroupSubmit").disabled = !$("groupNameInput").value.trim() || selectedGroupMembers.length === 0;
    }

    function renderSelectedMembers() {
        var html = "";
        for (var i = 0; i < selectedGroupMembers.length; i++) {
            var m = selectedGroupMembers[i];
            html += '<div class="selected-member">';
            html += '<span>' + escapeHtml(m.username) + '</span>';
            html += '<button data-id="' + m.id + '" aria-label="Remove">&times;</button>';
            html += '</div>';
        }
        $("selectedMembers").innerHTML = html;
        var btns = $("selectedMembers").querySelectorAll("button");
        for (var j = 0; j < btns.length; j++) {
            btns[j].addEventListener("click", function () {
                removeSelectedMember(this.getAttribute("data-id"));
            });
        }
    }

    function onGroupNameInput() {
        $("createGroupSubmit").disabled = !$("groupNameInput").value.trim();
    }

    function onCreateGroup() {
        var name = $("groupNameInput").value.trim();
        if (!name) return;

        var memberIds = selectedGroupMembers.map(function (m) { return m.id; });

        $("createGroupSubmit").disabled = true;
        $("createGroupSubmit").textContent = "Creating...";

        api("/api/conversations/group", {
            method: "POST",
            body: { name: name, member_ids: memberIds }
        }).then(function (res) {
            $("createGroupSubmit").textContent = "Create Group";
            $("createGroupSubmit").disabled = false;
            if ((res.status === 200 || res.status === 201) && res.data && res.data.id) {
                hideModal(createGroupModalEl);
                upsertConversation(res.data);
                try {
                    if (window.ChatSocket) window.ChatSocket.joinConversation(res.data.id);
                } catch (e) { /* ignore */ }
                openConversation(res.data.id);
            } else {
                alert(AppAuth.parseError(res.data));
            }
        }).catch(function () {
            $("createGroupSubmit").textContent = "Create Group";
            $("createGroupSubmit").disabled = false;
            alert("Failed to create group.");
        });
    }

    /* ── Group Info Panel ──────────────────────────────────────── */
    function showGroupInfo() {
        if (!activeConversationId) return;
        var conv = getConversationById(activeConversationId);
        if (!conv || conv.type !== "GROUP") return;

        $("groupInfoName").textContent = conv.name || "Group";
        var owner = isGroupOwner(conv);

        var memberHtml = "";
        for (var i = 0; i < conv.members.length; i++) {
            var m = conv.members[i];
            var isSelf = m.id === currentUser.id;
            var isOwnerMember = m.id === conv.owner_id;
            memberHtml += '<div class="group-member-item">';
            memberHtml += '<span>' + escapeHtml(m.username) + (isSelf ? ' (You)' : '') + (isOwnerMember ? ' ★' : '') + '</span>';
            if (owner && !isSelf && !isOwnerMember) {
                memberHtml += '<div class="group-member-actions">';
                memberHtml += '<button class="danger" data-action="remove" data-uid="' + m.id + '">Remove</button>';
                memberHtml += '</div>';
            }
            memberHtml += '</div>';
        }
        $("groupMemberList").innerHTML = memberHtml;

        var actionsHtml = "";
        if (owner) {
            actionsHtml += '<button id="renameGroupBtn">Rename</button>';
            actionsHtml += '<button id="addMemberBtn">Add member</button>';
        } else {
            actionsHtml += '<button class="danger" id="leaveGroupBtn">Leave group</button>';
        }
        $("groupActions").innerHTML = actionsHtml;

        showModal(groupInfoModalEl);

        /* Bind actions */
        var removeBtns = $("groupMemberList").querySelectorAll('[data-action="remove"]');
        for (var j = 0; j < removeBtns.length; j++) {
            removeBtns[j].addEventListener("click", function () {
                var uid = this.getAttribute("data-uid");
                removeGroupMember(uid);
            });
        }

        var renameBtn = $("renameGroupBtn");
        if (renameBtn) renameBtn.addEventListener("click", function () {
            hideModal(groupInfoModalEl);
            $("renameGroupInput").value = conv.name || "";
            showModal(renameGroupModalEl);
        });

        var addBtn = $("addMemberBtn");
        if (addBtn) addBtn.addEventListener("click", function () {
            hideModal(groupInfoModalEl);
            $("addMemberSearchInput").value = "";
            $("addMemberResults").innerHTML = "";
            showModal(addMemberModalEl);
            $("addMemberSearchInput").focus();
        });

        var leaveBtn = $("leaveGroupBtn");
        if (leaveBtn) leaveBtn.addEventListener("click", function () {
            leaveGroup();
        });
    }

    function removeGroupMember(userId) {
        if (!activeConversationId) return;
        api("/api/conversations/" + activeConversationId + "/members/" + userId, {
            method: "DELETE"
        }).then(function (res) {
            if (res.status === 200 && res.data && res.data.id) {
                upsertConversation(res.data);
                showGroupInfo();
            } else {
                alert(AppAuth.parseError(res.data));
            }
        }).catch(function () {
            alert("Failed to remove member.");
        });
    }

    function leaveGroup() {
        if (!activeConversationId) return;
        api("/api/conversations/" + activeConversationId + "/leave", {
            method: "POST"
        }).then(function (res) {
            hideModal(groupInfoModalEl);
            if (res.status === 200) {
                conversations = conversations.filter(function (c) { return c.id !== activeConversationId; });
                activeConversationId = null;
                chatViewEl.classList.add("hidden");
                emptyStateEl.classList.remove("hidden");
                renderConversationList();
            } else {
                var msg = AppAuth.parseError(res.data);
                if (msg.indexOf("CANNOT_LEAVE_AS_OWNER") !== -1) {
                    alert("The group owner cannot leave the group.");
                } else {
                    alert(msg);
                }
            }
        }).catch(function () {
            alert("Failed to leave group.");
        });
    }

    /* ── Rename Group ──────────────────────────────────────────── */
    function onRenameGroup() {
        var name = $("renameGroupInput").value.trim();
        if (!name || !activeConversationId) return;

        api("/api/conversations/" + activeConversationId, {
            method: "PATCH",
            body: { name: name }
        }).then(function (res) {
            if (res.status === 200 && res.data && res.data.id) {
                hideModal(renameGroupModalEl);
                upsertConversation(res.data);
                chatHeaderNameEl.textContent = getConversationDisplayName(res.data);
            } else {
                alert(AppAuth.parseError(res.data));
            }
        }).catch(function () {
            alert("Failed to rename group.");
        });
    }

    /* ── Add Member ────────────────────────────────────────────── */
    function onAddMemberSearch(e) {
        clearTimeout(searchTimeout);
        var q = e.target.value.trim();
        if (!q) {
            $("addMemberResults").innerHTML = "";
            return;
        }
        searchTimeout = setTimeout(function () {
            searchUsers(q, "addMemberResults", function (user) {
                addGroupMember(user.id);
            });
        }, 300);
    }

    function addGroupMember(userId) {
        if (!activeConversationId) return;
        api("/api/conversations/" + activeConversationId + "/members", {
            method: "POST",
            body: { user_id: userId }
        }).then(function (res) {
            if (res.status === 200 && res.data && res.data.id) {
                hideModal(addMemberModalEl);
                upsertConversation(res.data);
            } else {
                alert(AppAuth.parseError(res.data));
            }
        }).catch(function () {
            alert("Failed to add member.");
        });
    }

    /* ── Mobile back ───────────────────────────────────────────── */
    function onBackClick() {
        $("sidebar").classList.remove("hidden-mobile");
        chatViewEl.classList.add("hidden");
        emptyStateEl.classList.remove("hidden");
        activeConversationId = null;
        renderConversationList();
    }

    /* ── Modal close handlers ──────────────────────────────────── */
    function setupModalClose() {
        var modals = [
            { overlay: newChatModalEl, close: $("newChatModalClose") },
            { overlay: userSearchModalEl, close: $("userSearchModalClose") },
            { overlay: createGroupModalEl, close: $("createGroupModalClose") },
            { overlay: groupInfoModalEl, close: $("groupInfoModalClose") },
            { overlay: renameGroupModalEl, close: $("renameGroupModalClose") },
            { overlay: addMemberModalEl, close: $("addMemberModalClose") }
        ];
        modals.forEach(function (m) {
            m.close.addEventListener("click", function () { hideModal(m.overlay); });
            m.overlay.addEventListener("click", function (e) {
                if (e.target === m.overlay) hideModal(m.overlay);
            });
        });
    }

    /* ── Expose for socket.js ──────────────────────────────────── */
    window.ChatApp = {
        currentUser: currentUser,
        getActiveConversationId: function () { return activeConversationId; },
        getConversations: function () { return conversations; },
        getConversationById: getConversationById,
        getConversationDisplayName: getConversationDisplayName,
        appendMessage: appendMessage,
        updateConversationListPreview: updateConversationListPreview,
        upsertConversation: upsertConversation,
        fetchAndUpsertConversation: fetchAndUpsertConversation,
        openConversation: openConversation,
        renderConversationList: renderConversationList,
        loadMessages: loadMessages,
        renderMessages: renderMessages,
        sortMessages: sortMessages,
        messages: messages,
        renderAttachmentHtml: renderAttachmentHtml,
        formatFileSize: formatFileSize,
        escapeHtml: escapeHtml
    };

    /* ── Init ──────────────────────────────────────────────────── */
    function init() {
        setupModalClose();
        loadConversations();

        sendBtnEl.addEventListener("click", onSendClick);
        messageInputEl.addEventListener("input", autoResizeInput);
        messageInputEl.addEventListener("keydown", onInputKeyDown);
        attachBtnEl.addEventListener("click", onAttachClick);
        fileInputEl.addEventListener("change", onFileSelected);
        removeAttachmentEl.addEventListener("click", clearAttachment);
        backBtnEl.addEventListener("click", onBackClick);
        groupInfoBtnEl.addEventListener("click", showGroupInfo);
        messagesContainerEl.addEventListener("scroll", onMessagesScroll);

        $("newChatBtn").addEventListener("click", onNewChatClick);
        $("newDirectBtn").addEventListener("click", onNewDirectClick);
        $("newGroupBtn").addEventListener("click", onNewGroupClick);

        $("userSearchInput").addEventListener("input", onUserSearchInput);
        $("groupMemberSearchInput").addEventListener("input", onGroupMemberSearch);
        $("groupNameInput").addEventListener("input", onGroupNameInput);
        $("createGroupSubmit").addEventListener("click", onCreateGroup);
        $("renameGroupSubmit").addEventListener("click", onRenameGroup);
        $("addMemberSearchInput").addEventListener("input", onAddMemberSearch);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
