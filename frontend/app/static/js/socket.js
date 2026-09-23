/* socket.js — Socket.IO real-time messaging */

(function () {
    "use strict";

    var socket = null;
    var connected = false;

    var connectionBarEl = document.getElementById("connectionBar");
    var connectionDotEl = document.getElementById("connectionDot");
    var connectionTextEl = document.getElementById("connectionText");

    function updateConnectionUI(state) {
        if (!connectionBarEl) return;
        connectionBarEl.classList.add("visible");
        connectionDotEl.className = "connection-dot " + state;
        if (state === "connected") {
            connectionTextEl.textContent = "Connected";
            setTimeout(function () {
                connectionBarEl.classList.remove("visible");
            }, 2000);
        } else if (state === "connecting") {
            connectionTextEl.textContent = "Connecting...";
        } else {
            connectionTextEl.textContent = "Disconnected — retrying...";
        }
    }

    function connect() {
        var token = window.__ACCESS_TOKEN__;
        var backendUrl = window.__BACKEND_URL__ || "http://localhost:5000";
        if (!token || socket) return;

        updateConnectionUI("connecting");

        socket = io(backendUrl, {
            query: { token: token },
            transports: ["websocket", "polling"],
            reconnection: true,
            reconnectionAttempts: Infinity,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000
        });

        socket.on("connect", function () {
            connected = true;
            updateConnectionUI("connected");
            // Re-join the active conversation after (re)connect so the
            // first message after a refresh / reconnect is never lost.
            try {
                var app = window.ChatApp;
                if (app && app.getActiveConversationId()) {
                    joinConversation(app.getActiveConversationId());
                }
            } catch (e) { /* ignore */ }
        });

        socket.on("disconnect", function () {
            connected = false;
            updateConnectionUI("disconnected");
        });

        socket.on("connect_error", function () {
            connected = false;
            updateConnectionUI("disconnected");
        });

        socket.on("receive_message", function (msg) {
            if (!msg || !msg.conversation_id) return;

            var app = window.ChatApp;
            if (!app) return;

            var activeId = app.getActiveConversationId();
            var conv = app.getConversationById(msg.conversation_id);

            // New conversation we don't know about yet (e.g. someone else
            // started a DM with us): fetch it so it appears instantly.
            if (!conv) {
                app.fetchAndUpsertConversation(msg.conversation_id, function () {
                    app.updateConversationListPreview(msg.conversation_id, msg);
                    if (msg.conversation_id === app.getActiveConversationId()) {
                        app.appendMessage(msg);
                    } else {
                        var c2 = app.getConversationById(msg.conversation_id);
                        if (c2) {
                            c2.__unread = true;
                            app.renderConversationList();
                        }
                    }
                });
                return;
            }

            if (msg.conversation_id === activeId) {
                app.appendMessage(msg);
            }

            // Clear unread when the message is for the open chat.
            if (msg.conversation_id === activeId) {
                conv.__unread = false;
            }

            app.updateConversationListPreview(msg.conversation_id, msg);

            if (msg.conversation_id !== activeId) {
                conv.__unread = true;
                app.renderConversationList();
            }
        });

        socket.on("error", function (data) {
            if (data && data.message) {
                console.error("Socket error:", data.message);
            }
        });
    }

    function disconnect() {
        if (socket) {
            socket.removeAllListeners();
            socket.disconnect();
            socket = null;
            connected = false;
        }
    }

    function joinConversation(conversationId) {
        if (!socket || !connected || !conversationId) return;
        try {
            socket.emit("join_conversation", { conversation_id: conversationId });
        } catch (e) { /* ignore */ }
    }

    function sendMessage(content, attachmentId) {
        if (!socket || !connected) return false;
        socket.emit("send_message", {
            conversation_id: window.ChatApp.getActiveConversationId(),
            content: content || null,
            attachment_id: attachmentId || null
        });
        return true;
    }

    function isConnected() {
        return connected && socket && socket.connected;
    }

    window.ChatSocket = {
        connect: connect,
        disconnect: disconnect,
        joinConversation: joinConversation,
        sendMessage: sendMessage,
        isConnected: isConnected
    };

    window.addEventListener("beforeunload", function () {
        disconnect();
    });
})();
