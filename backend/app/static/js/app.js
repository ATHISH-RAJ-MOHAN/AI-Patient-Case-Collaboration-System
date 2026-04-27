import {
    ApiError,
    addCaseMember,
    createCase,
    fetchCaseDocuments,
    fetchCaseMembers,
    fetchCaseMessages,
    fetchCaseSummaries,
    fetchMe,
    logout,
    searchUsers,
    sendCaseMessage,
    uploadDocument,
} from "./api.js";
import { ROUTES, fileUrl, websocketUrl } from "./config.js";
import {
    clearSession,
    getActiveCaseId,
    getCurrentUser,
    getToken,
    setActiveCaseId,
    setCurrentUser,
} from "./storage.js";
import {
    autoResizeTextarea,
    escapeHtml,
    formatConversationTime,
    formatFullDateTime,
    formatMessageTime,
    getInitials,
    isNearBottom,
    scrollToBottom,
    truncateText,
} from "./utils.js";

const body = document.body;
const caseList = document.querySelector("#case-list");
const caseSearch = document.querySelector("#case-search");
const sidebarUserAvatar = document.querySelector("#sidebar-user-avatar");
const sidebarUserName = document.querySelector("#sidebar-user-name");
const sidebarUserEmail = document.querySelector("#sidebar-user-email");
const caseHeaderKicker = document.querySelector("#case-header-kicker");
const caseTitle = document.querySelector("#case-title");
const caseSubtitle = document.querySelector("#case-subtitle");
const connectionBadge = document.querySelector("#connection-badge");
const globalBanner = document.querySelector("#global-banner");
const messageList = document.querySelector("#message-list");
const composerForm = document.querySelector("#composer-form");
const messageInput = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const composerStatus = document.querySelector("#composer-status");
const detailsCaseLabel = document.querySelector("#details-case-label");
const caseMeta = document.querySelector("#case-meta");
const documentUpload = document.querySelector("#document-upload");
const documentList = document.querySelector("#document-list");
const documentFeedback = document.querySelector("#document-feedback");
const memberList = document.querySelector("#member-list");
const memberCountPill = document.querySelector("#member-count-pill");
const memberSearchInput = document.querySelector("#member-search-input");
const memberSearchFeedback = document.querySelector("#member-search-feedback");
const memberSearchResults = document.querySelector("#member-search-results");
const openSidebarButton = document.querySelector("#open-sidebar-button");
const closeSidebarButton = document.querySelector("#close-sidebar-button");
const toggleDetailsButton = document.querySelector("#toggle-details-button");
const closeDetailsButton = document.querySelector("#close-details-button");
const mobileOverlay = document.querySelector("#mobile-overlay");
const newCaseButton = document.querySelector("#new-case-button");
const refreshButton = document.querySelector("#refresh-button");
const logoutButton = document.querySelector("#logout-button");
const caseModal = document.querySelector("#case-modal");
const caseModalClose = document.querySelector("#case-modal-close");
const caseCancelButton = document.querySelector("#case-cancel-button");
const caseForm = document.querySelector("#case-form");
const caseFormFeedback = document.querySelector("#case-form-feedback");
const caseCreateButton = document.querySelector("#case-create-button");

const state = {
    token: getToken(),
    currentUser: getCurrentUser(),
    cases: [],
    activeCaseId: getActiveCaseId(),
    messages: [],
    members: [],
    documents: [],
    loadingCases: true,
    loadingConversation: false,
    sendingMessage: false,
    creatingCase: false,
    uploadingDocument: false,
    searchQuery: "",
    bannerMessage: "",
    bannerType: "error",
    memberSearch: {
        query: "",
        results: [],
        loading: false,
        error: "",
        invitingUserId: null,
        requestId: 0,
    },
    socketStatus: "offline",
    socket: null,
    reconnectTimer: null,
    pollTimer: null,
};

function redirectToLogin() {
    clearSession();
    window.location.replace(ROUTES.login);
}

function getActiveCase() {
    return state.cases.find((item) => item.id === state.activeCaseId) || null;
}

function getMemberMap() {
    return new Map(state.members.map((member) => [member.user_id, member]));
}

function setBanner(message = "", type = "error") {
    state.bannerMessage = message;
    state.bannerType = type;

    if (!message) {
        globalBanner.hidden = true;
        globalBanner.textContent = "";
        globalBanner.dataset.type = "";
        return;
    }

    globalBanner.hidden = false;
    globalBanner.dataset.type = type;
    globalBanner.textContent = message;
}

function sortCases() {
    state.cases.sort((left, right) => {
        const leftValue = new Date(left.last_message_at || left.updated_at || left.created_at || 0).getTime();
        const rightValue = new Date(right.last_message_at || right.updated_at || right.created_at || 0).getTime();
        return rightValue - leftValue;
    });
}

function buildPreview(caseItem) {
    if (!caseItem.last_message) {
        return "No messages yet. Start the care-team discussion.";
    }

    if (caseItem.last_message_type === "ai") {
        return `AI: ${truncateText(caseItem.last_message, 88)}`;
    }

    return truncateText(caseItem.last_message, 88);
}

function renderIdentity() {
    if (!state.currentUser) {
        sidebarUserAvatar.textContent = "CC";
        sidebarUserName.textContent = "Session not available";
        sidebarUserEmail.textContent = "Please sign in";
        return;
    }

    sidebarUserAvatar.textContent = getInitials(state.currentUser.full_name);
    sidebarUserName.textContent = state.currentUser.full_name;
    sidebarUserEmail.textContent = state.currentUser.email;
}

function renderSidebar() {
    const matchingCases = state.cases.filter((caseItem) => {
        const haystack = `${caseItem.case_title} ${caseItem.patient_code}`.toLowerCase();
        return haystack.includes(state.searchQuery.toLowerCase());
    });

    if (state.loadingCases) {
        caseList.innerHTML = `
            <div class="skeleton-list">
                <div class="skeleton-row"></div>
                <div class="skeleton-row"></div>
                <div class="skeleton-row"></div>
                <div class="skeleton-row"></div>
            </div>
        `;
        return;
    }

    if (!state.cases.length) {
        caseList.innerHTML = `
            <article class="panel-empty-state">
                <h3>No case rooms yet</h3>
                <p>Create your first case to start a group conversation, upload files, and invite collaborators through the existing backend APIs.</p>
                <button class="secondary-button" type="button" data-open-case-modal="true">Create First Case</button>
            </article>
        `;
        return;
    }

    if (!matchingCases.length) {
        caseList.innerHTML = `
            <article class="panel-empty-state panel-empty-state--compact">
                <h3>No matching conversations</h3>
                <p>Try a different case title or patient code.</p>
            </article>
        `;
        return;
    }

    caseList.innerHTML = matchingCases
        .map((caseItem) => {
            const isSelected = caseItem.id === state.activeCaseId;
            return `
                <button class="case-row ${isSelected ? "is-selected" : ""}" type="button" data-case-id="${caseItem.id}">
                    <span class="case-row__avatar">${escapeHtml(getInitials(caseItem.case_title))}</span>
                    <span class="case-row__content">
                        <span class="case-row__title-line">
                            <strong>${escapeHtml(caseItem.case_title)}</strong>
                            <time datetime="${escapeHtml(caseItem.last_message_at || caseItem.updated_at || "")}">
                                ${escapeHtml(formatConversationTime(caseItem.last_message_at || caseItem.updated_at || caseItem.created_at))}
                            </time>
                        </span>
                        <span class="case-row__meta">Patient ${escapeHtml(caseItem.patient_code)} • ${caseItem.member_count} members</span>
                        <span class="case-row__preview">${escapeHtml(buildPreview(caseItem))}</span>
                    </span>
                    <span class="case-row__count">${caseItem.document_count}</span>
                </button>
            `;
        })
        .join("");
}

function renderHeader() {
    const activeCase = getActiveCase();

    if (!activeCase) {
        caseHeaderKicker.textContent = "Select a case";
        caseTitle.textContent = "Case collaboration workspace";
        caseSubtitle.textContent = "Choose a conversation from the left sidebar to load messages.";
        connectionBadge.textContent = "Offline";
        connectionBadge.className = "status-pill";
        toggleDetailsButton.disabled = true;
        detailsCaseLabel.textContent = "No case selected";
        return;
    }

    caseHeaderKicker.textContent = `Patient ${activeCase.patient_code}`;
    caseTitle.textContent = activeCase.case_title;
    caseSubtitle.textContent = `${activeCase.member_count} members • ${activeCase.document_count} shared documents`;
    detailsCaseLabel.textContent = `${activeCase.case_title}`;
    toggleDetailsButton.disabled = false;

    const statusMap = {
        live: ["Live", "status-pill status-pill--live"],
        connecting: ["Connecting", "status-pill status-pill--warning"],
        offline: ["Polling", "status-pill status-pill--soft"],
    };
    const [label, className] = statusMap[state.socketStatus] || statusMap.offline;
    connectionBadge.textContent = label;
    connectionBadge.className = className;
}

function renderComposer() {
    const activeCase = getActiveCase();
    const isDisabled = !activeCase || state.loadingConversation || state.sendingMessage;

    messageInput.disabled = isDisabled;
    sendButton.disabled = isDisabled;
    sendButton.textContent = state.sendingMessage ? "Sending..." : "Send";

    composerStatus.innerHTML = activeCase
        ? `Use <code>@ai</code> or <code>/ai</code> in the chat to ask case-grounded questions.`
        : "Select a case to send messages and collaborate in real time.";
}

function renderMessages(shouldStick = false) {
    const activeCase = getActiveCase();
    const shouldAutoScroll = shouldStick || isNearBottom(messageList);
    const memberMap = getMemberMap();

    if (!activeCase) {
        messageList.innerHTML = `
            <article class="chat-empty-state">
                <span class="eyebrow">Conversation view</span>
                <h2>No conversation selected</h2>
                <p>Pick a case from the sidebar to review the shared timeline, send updates, and ask AI for document-grounded help.</p>
            </article>
        `;
        return;
    }

    if (state.loadingConversation) {
        messageList.innerHTML = `
            <div class="message-skeleton">
                <div class="skeleton-bubble skeleton-bubble--short"></div>
                <div class="skeleton-bubble skeleton-bubble--long skeleton-bubble--right"></div>
                <div class="skeleton-bubble skeleton-bubble--medium"></div>
            </div>
        `;
        return;
    }

    if (!state.messages.length) {
        messageList.innerHTML = `
            <article class="chat-empty-state">
                <span class="eyebrow">Case timeline</span>
                <h2>No messages yet</h2>
                <p>Start the conversation with a handoff update, plan, or question for the rest of the case team.</p>
            </article>
        `;
        return;
    }

    messageList.innerHTML = state.messages
        .map((message) => {
            const isAi = message.message_type === "ai";
            const isOutgoing = !isAi && message.sender_id === state.currentUser?.id;
            const member = memberMap.get(message.sender_id);
            const author = isAi
                ? "Case AI assistant"
                : (isOutgoing ? "You" : (member?.full_name || `Clinician ${message.sender_id}`));

            return `
                <article class="message ${isOutgoing ? "message--outgoing" : ""} ${isAi ? "message--ai" : ""}">
                    <div class="message__meta">
                        <span>${escapeHtml(author)}</span>
                        <time title="${escapeHtml(formatFullDateTime(message.sent_at))}">
                            ${escapeHtml(formatMessageTime(message.sent_at))}
                        </time>
                    </div>
                    <div class="message__bubble">${escapeHtml(message.content)}</div>
                </article>
            `;
        })
        .join("");

    if (shouldAutoScroll) {
        scrollToBottom(messageList);
    }
}

function renderCaseMeta() {
    const activeCase = getActiveCase();

    if (!activeCase) {
        caseMeta.className = "empty-copy";
        caseMeta.textContent = "Select a case to view metadata, members, and shared resources.";
        return;
    }

    caseMeta.className = "meta-grid";
    caseMeta.innerHTML = `
        <div class="meta-item">
            <span>Status</span>
            <strong>${escapeHtml(activeCase.status)}</strong>
        </div>
        <div class="meta-item">
            <span>Patient code</span>
            <strong>${escapeHtml(activeCase.patient_code)}</strong>
        </div>
        <div class="meta-item">
            <span>Last activity</span>
            <strong>${escapeHtml(formatFullDateTime(activeCase.last_message_at || activeCase.updated_at || activeCase.created_at) || "No activity yet")}</strong>
        </div>
        <div class="meta-item">
            <span>Documents</span>
            <strong>${activeCase.document_count}</strong>
        </div>
    `;
}

function renderDocuments() {
    const activeCase = getActiveCase();
    documentUpload.disabled = !activeCase || state.uploadingDocument;

    if (!activeCase) {
        documentFeedback.textContent = "";
        documentList.innerHTML = `<div class="empty-copy">Shared files will appear here once a case is selected.</div>`;
        return;
    }

    if (!state.documents.length) {
        documentList.innerHTML = `<div class="empty-copy">No documents uploaded yet.</div>`;
        return;
    }

    documentList.innerHTML = state.documents
        .map(
            (document) => `
                <a class="document-row" href="${escapeHtml(fileUrl(document.file_path))}" target="_blank" rel="noreferrer">
                    <span class="document-row__icon">↗</span>
                    <span class="document-row__copy">
                        <strong>${escapeHtml(document.file_name)}</strong>
                        <span>${escapeHtml(formatFullDateTime(document.created_at))}</span>
                    </span>
                </a>
            `
        )
        .join("");
}

function renderMembers() {
    const activeCase = getActiveCase();
    memberCountPill.textContent = `${state.members.length} members`;

    if (!activeCase) {
        memberList.innerHTML = `<div class="empty-copy">The care team for the selected case will appear here.</div>`;
        return;
    }

    if (!state.members.length) {
        memberList.innerHTML = `<div class="empty-copy">No members found for this case.</div>`;
        return;
    }

    memberList.innerHTML = state.members
        .map(
            (member) => `
                <article class="member-row">
                    <span class="member-row__avatar">${escapeHtml(getInitials(member.full_name))}</span>
                    <span class="member-row__copy">
                        <strong>${escapeHtml(member.full_name)}</strong>
                        <span>${escapeHtml(member.role)} • ${escapeHtml(member.member_role)}</span>
                    </span>
                </article>
            `
        )
        .join("");
}

function renderMemberInvite() {
    const activeCase = getActiveCase();
    const memberIds = new Set(state.members.map((member) => member.user_id));
    const availableResults = state.memberSearch.results.filter((user) => !memberIds.has(user.id));

    memberSearchInput.disabled = !activeCase || state.memberSearch.loading;

    if (!activeCase) {
        memberSearchInput.value = "";
        memberSearchFeedback.className = "muted member-search-feedback";
        memberSearchFeedback.textContent = "Select a case before adding teammates.";
        memberSearchResults.innerHTML = "";
        return;
    }

    memberSearchInput.value = state.memberSearch.query;

    if (state.memberSearch.error) {
        memberSearchFeedback.className = "form-feedback";
        memberSearchFeedback.dataset.type = "error";
        memberSearchFeedback.textContent = state.memberSearch.error;
    } else if (state.memberSearch.loading) {
        memberSearchFeedback.className = "muted member-search-feedback";
        delete memberSearchFeedback.dataset.type;
        memberSearchFeedback.textContent = "Searching users...";
    } else if (state.memberSearch.query.trim().length < 2) {
        memberSearchFeedback.className = "muted member-search-feedback";
        delete memberSearchFeedback.dataset.type;
        memberSearchFeedback.textContent = "Search by teammate name or email.";
    } else if (!state.memberSearch.results.length) {
        memberSearchFeedback.className = "muted member-search-feedback";
        delete memberSearchFeedback.dataset.type;
        memberSearchFeedback.textContent = "No matching users found.";
    } else if (!availableResults.length) {
        memberSearchFeedback.className = "muted member-search-feedback";
        delete memberSearchFeedback.dataset.type;
        memberSearchFeedback.textContent = "All matching users are already in this case.";
    } else {
        memberSearchFeedback.className = "muted member-search-feedback";
        delete memberSearchFeedback.dataset.type;
        memberSearchFeedback.textContent = "Select a teammate below to add them to this case.";
    }

    memberSearchResults.innerHTML = availableResults
        .map(
            (user) => `
                <article class="member-search-row">
                    <div class="member-search-row__copy">
                        <strong>${escapeHtml(user.full_name)}</strong>
                        <span>${escapeHtml(user.email)} • ${escapeHtml(user.role)}</span>
                    </div>
                    <button
                        class="secondary-button secondary-button--compact"
                        type="button"
                        data-invite-user-id="${user.id}"
                        ${state.memberSearch.invitingUserId === user.id ? "disabled" : ""}
                    >
                        ${state.memberSearch.invitingUserId === user.id ? "Adding..." : "Add"}
                    </button>
                </article>
            `
        )
        .join("");
}

function renderDetails() {
    renderCaseMeta();
    renderDocuments();
    renderMemberInvite();
    renderMembers();
}

function renderAll(shouldStickMessages = false) {
    renderIdentity();
    renderSidebar();
    renderHeader();
    renderMessages(shouldStickMessages);
    renderComposer();
    renderDetails();
}

function setModalFeedback(message = "", type = "error") {
    if (!message) {
        caseFormFeedback.hidden = true;
        caseFormFeedback.textContent = "";
        caseFormFeedback.dataset.type = "";
        return;
    }

    caseFormFeedback.hidden = false;
    caseFormFeedback.textContent = message;
    caseFormFeedback.dataset.type = type;
}

function setCaseFormPending(isPending) {
    if (!caseForm) {
        return;
    }

    Array.from(caseForm.elements).forEach((element) => {
        element.disabled = isPending;
    });
    caseCreateButton.textContent = isPending ? "Creating..." : "Create Case";
}

function openSidebar() {
    body.classList.add("sidebar-open");
    mobileOverlay.hidden = false;
}

function closeSidebar() {
    body.classList.remove("sidebar-open");
    if (!body.classList.contains("details-open")) {
        mobileOverlay.hidden = true;
    }
}

function openDetails() {
    if (!getActiveCase()) {
        return;
    }

    if (!window.matchMedia("(max-width: 1280px)").matches) {
        return;
    }

    body.classList.add("details-open");
    mobileOverlay.hidden = false;
}

function closeDetails() {
    body.classList.remove("details-open");
    if (!body.classList.contains("sidebar-open")) {
        mobileOverlay.hidden = true;
    }
}

function openCaseModal() {
    caseModal.hidden = false;
    body.classList.add("modal-open");
    setModalFeedback("");
}

function closeCaseModal() {
    caseModal.hidden = true;
    body.classList.remove("modal-open");
    setModalFeedback("");
    caseForm.reset();
}

function cleanupRealtime() {
    if (state.reconnectTimer) {
        window.clearTimeout(state.reconnectTimer);
        state.reconnectTimer = null;
    }

    if (state.pollTimer) {
        window.clearInterval(state.pollTimer);
        state.pollTimer = null;
    }

    if (state.socket) {
        state.socket.onopen = null;
        state.socket.onmessage = null;
        state.socket.onerror = null;
        state.socket.onclose = null;
        state.socket.close();
        state.socket = null;
    }

    state.socketStatus = "offline";
}

function startPolling(caseId) {
    if (state.pollTimer) {
        window.clearInterval(state.pollTimer);
    }

    state.pollTimer = window.setInterval(async () => {
        if (state.activeCaseId !== caseId || state.socketStatus === "live") {
            return;
        }

        try {
            const messages = await fetchCaseMessages(caseId, state.token);
            if (state.activeCaseId !== caseId) {
                return;
            }

            state.messages = normalizeMessages(messages);
            renderMessages();
        } catch (_error) {
            // Let the existing banner and reconnect flow handle visibility.
        }
    }, 15000);
}

function connectRealtime(caseId) {
    cleanupRealtime();

    state.socketStatus = "connecting";
    renderHeader();

    const socket = new WebSocket(
        websocketUrl(`/cases/ws/cases/${caseId}?token=${encodeURIComponent(state.token)}`)
    );
    state.socket = socket;

    socket.onopen = () => {
        if (state.activeCaseId !== caseId) {
            socket.close();
            return;
        }

        state.socketStatus = "live";
        renderHeader();
    };

    socket.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            if (payload.type === "new_message" && payload.data?.case_id === state.activeCaseId) {
                mergeMessage(payload.data);
                updateCaseSummaryFromMessage(payload.data);
                renderSidebar();
                renderHeader();
                renderMessages(true);
            } else if (payload.type === "error") {
                setBanner(payload.message || "Realtime update failed.");
            }
        } catch (_error) {
            setBanner("Received an invalid realtime payload.");
        }
    };

    socket.onerror = () => {
        state.socketStatus = "offline";
        renderHeader();
    };

    socket.onclose = () => {
        if (state.activeCaseId !== caseId) {
            return;
        }

        state.socketStatus = "offline";
        renderHeader();
        startPolling(caseId);

        state.reconnectTimer = window.setTimeout(() => {
            if (state.activeCaseId === caseId) {
                connectRealtime(caseId);
            }
        }, 4000);
    };
}

function normalizeMessages(messages) {
    return [...messages].sort((left, right) => (
        new Date(left.sent_at).getTime() - new Date(right.sent_at).getTime()
    ));
}

function mergeMessage(nextMessage) {
    const currentMessage = state.messages.find((message) => message.id === nextMessage.id);
    if (currentMessage) {
        state.messages = state.messages.map((message) => (
            message.id === nextMessage.id ? nextMessage : message
        ));
    } else {
        state.messages = normalizeMessages([...state.messages, nextMessage]);
    }
}

function updateCaseSummaryFromMessage(message) {
    const caseItem = state.cases.find((item) => item.id === message.case_id);
    if (!caseItem) {
        return;
    }

    caseItem.last_message = message.content;
    caseItem.last_message_at = message.sent_at;
    caseItem.last_message_sender_id = message.sender_id;
    caseItem.last_message_type = message.message_type;
    sortCases();
}

async function loadCaseSummaries(options = {}) {
    const { preferredCaseId = state.activeCaseId, reloadConversation = true } = options;

    state.loadingCases = true;
    renderSidebar();

    const summaries = await fetchCaseSummaries(state.token);
    state.cases = summaries;
    sortCases();
    state.loadingCases = false;

    const nextCaseId = preferredCaseId && state.cases.some((item) => item.id === Number(preferredCaseId))
        ? Number(preferredCaseId)
        : (state.cases[0]?.id || null);

    if (!nextCaseId) {
        state.activeCaseId = null;
        setActiveCaseId(null);
        state.messages = [];
        state.members = [];
        state.documents = [];
        cleanupRealtime();
        renderAll();
        return;
    }

    if (reloadConversation || nextCaseId !== state.activeCaseId) {
        await selectCase(nextCaseId);
    } else {
        renderAll();
    }
}

async function selectCase(caseId) {
    state.activeCaseId = Number(caseId);
    setActiveCaseId(state.activeCaseId);
    state.loadingConversation = true;
    state.memberSearch = {
        query: "",
        results: [],
        loading: false,
        error: "",
        invitingUserId: null,
        requestId: 0,
    };
    documentFeedback.textContent = "";
    renderAll();
    closeSidebar();

    const selectedCaseId = state.activeCaseId;

    try {
        const [messages, members, documents] = await Promise.all([
            fetchCaseMessages(selectedCaseId, state.token),
            fetchCaseMembers(selectedCaseId, state.token),
            fetchCaseDocuments(selectedCaseId, state.token),
        ]);

        if (state.activeCaseId !== selectedCaseId) {
            return;
        }

        state.messages = normalizeMessages(messages);
        state.members = members;
        state.documents = documents;
        state.loadingConversation = false;
        setBanner("");
        renderAll(true);
        connectRealtime(selectedCaseId);
    } catch (error) {
        if (state.activeCaseId !== selectedCaseId) {
            return;
        }

        state.loadingConversation = false;
        handleError(error, "Could not load the selected case.");
        renderAll();
    }
}

async function handleLogout() {
    try {
        if (state.token) {
            await logout(state.token);
        }
    } catch (_error) {
        // Logging out locally is enough for this token-based first version.
    } finally {
        cleanupRealtime();
        redirectToLogin();
    }
}

function handleError(error, fallbackMessage) {
    if (error instanceof ApiError && error.status === 401) {
        redirectToLogin();
        return;
    }

    setBanner(error.message || fallbackMessage || "Something went wrong.");
}

async function boot() {
    if (!state.token) {
        redirectToLogin();
        return;
    }

    renderAll();

    try {
        const currentUser = await fetchMe(state.token);
        state.currentUser = currentUser;
        setCurrentUser(currentUser);
        renderIdentity();
        await loadCaseSummaries({
            preferredCaseId: state.activeCaseId,
            reloadConversation: true,
        });
    } catch (error) {
        handleError(error, "Your session could not be restored.");
    }
}

async function handleRefresh() {
    try {
        setBanner("");
        await loadCaseSummaries({
            preferredCaseId: state.activeCaseId,
            reloadConversation: Boolean(state.activeCaseId),
        });
    } catch (error) {
        handleError(error, "Could not refresh the workspace.");
    }
}

async function handleMessageSubmit(event) {
    event.preventDefault();
    const activeCase = getActiveCase();
    const content = messageInput.value.trim();

    if (!activeCase || !content) {
        return;
    }

    state.sendingMessage = true;
    renderComposer();

    try {
        const createdMessage = await sendCaseMessage(
            activeCase.id,
            {
                content,
                message_type: "text",
            },
            state.token,
        );

        mergeMessage(createdMessage);
        updateCaseSummaryFromMessage(createdMessage);
        state.sendingMessage = false;
        messageInput.value = "";
        autoResizeTextarea(messageInput);
        setBanner("", "success");
        renderSidebar();
        renderHeader();
        renderMessages(true);
        renderComposer();
    } catch (error) {
        state.sendingMessage = false;
        handleError(error, "Message could not be sent.");
        renderComposer();
    }
}

async function handleDocumentUpload(event) {
    const activeCase = getActiveCase();
    const file = event.target.files?.[0];

    if (!activeCase || !file) {
        return;
    }

    state.uploadingDocument = true;
    documentFeedback.textContent = `Uploading ${file.name}...`;
    renderDocuments();

    try {
        await uploadDocument(activeCase.id, file, state.token);
        documentFeedback.textContent = `${file.name} uploaded successfully.`;
        state.documents = await fetchCaseDocuments(activeCase.id, state.token);

        const activeSummary = state.cases.find((item) => item.id === activeCase.id);
        if (activeSummary) {
            activeSummary.document_count = state.documents.length;
        }

        renderSidebar();
        renderHeader();
        renderDocuments();
    } catch (error) {
        documentFeedback.textContent = error.message || "Document upload failed.";
    } finally {
        state.uploadingDocument = false;
        documentUpload.value = "";
        renderDocuments();
    }
}

async function handleCreateCase(event) {
    event.preventDefault();
    const formData = new FormData(caseForm);
    const payload = {
        case_title: String(formData.get("case_title") || "").trim(),
        patient_code: String(formData.get("patient_code") || "").trim(),
    };

    if (!payload.case_title || !payload.patient_code) {
        setModalFeedback("Case title and patient code are required.");
        return;
    }

    state.creatingCase = true;
    setCaseFormPending(true);
    setModalFeedback("");

    try {
        const createdCase = await createCase(payload, state.token);
        closeCaseModal();
        setBanner("Case created successfully.", "success");
        await loadCaseSummaries({
            preferredCaseId: createdCase.id,
            reloadConversation: true,
        });
    } catch (error) {
        setModalFeedback(error.message || "Case creation failed.");
    } finally {
        state.creatingCase = false;
        setCaseFormPending(false);
    }
}

async function handleMemberSearchInput(event) {
    const activeCase = getActiveCase();
    state.memberSearch.query = event.target.value.trim();
    state.memberSearch.error = "";

    if (!activeCase || state.memberSearch.query.length < 2) {
        state.memberSearch.loading = false;
        state.memberSearch.results = [];
        renderMemberInvite();
        return;
    }

    const requestId = state.memberSearch.requestId + 1;
    state.memberSearch.requestId = requestId;
    state.memberSearch.loading = true;
    renderMemberInvite();

    try {
        const results = await searchUsers(state.memberSearch.query, state.token);
        if (requestId !== state.memberSearch.requestId) {
            return;
        }

        state.memberSearch.loading = false;
        state.memberSearch.results = results;
        renderMemberInvite();
    } catch (error) {
        if (requestId !== state.memberSearch.requestId) {
            return;
        }

        state.memberSearch.loading = false;
        state.memberSearch.results = [];
        state.memberSearch.error = error.message || "Could not search users.";
        renderMemberInvite();
    }
}

async function handleAddMember(userId) {
    const activeCase = getActiveCase();
    if (!activeCase || !userId) {
        return;
    }

    state.memberSearch.invitingUserId = userId;
    state.memberSearch.error = "";
    renderMemberInvite();

    try {
        await addCaseMember(
            activeCase.id,
            {
                user_id: userId,
                member_role: "doctor",
            },
            state.token,
        );

        state.members = await fetchCaseMembers(activeCase.id, state.token);
        const activeSummary = state.cases.find((item) => item.id === activeCase.id);
        if (activeSummary) {
            activeSummary.member_count = state.members.length;
        }

        state.memberSearch.query = "";
        state.memberSearch.results = [];
        state.memberSearch.error = "";
        state.memberSearch.invitingUserId = null;
        memberSearchInput.value = "";
        setBanner("Teammate added to the case.", "success");
        renderSidebar();
        renderHeader();
        renderDetails();
    } catch (error) {
        state.memberSearch.invitingUserId = null;
        state.memberSearch.error = error.message || "Could not add teammate to this case.";
        renderMemberInvite();
    }
}

caseSearch.addEventListener("input", (event) => {
    state.searchQuery = event.target.value.trim();
    renderSidebar();
});

caseList.addEventListener("click", (event) => {
    const modalTrigger = event.target.closest("[data-open-case-modal='true']");
    if (modalTrigger) {
        openCaseModal();
        return;
    }

    const caseRow = event.target.closest("[data-case-id]");
    if (!caseRow) {
        return;
    }

    const caseId = Number(caseRow.dataset.caseId);
    if (!caseId || caseId === state.activeCaseId) {
        return;
    }

    selectCase(caseId);
});

composerForm.addEventListener("submit", handleMessageSubmit);
documentUpload.addEventListener("change", handleDocumentUpload);
memberSearchInput.addEventListener("input", handleMemberSearchInput);
memberSearchResults.addEventListener("click", (event) => {
    const inviteButton = event.target.closest("[data-invite-user-id]");
    if (!inviteButton) {
        return;
    }

    handleAddMember(Number(inviteButton.dataset.inviteUserId));
});
messageInput.addEventListener("input", () => autoResizeTextarea(messageInput));
newCaseButton.addEventListener("click", openCaseModal);
refreshButton.addEventListener("click", handleRefresh);
logoutButton.addEventListener("click", handleLogout);
openSidebarButton.addEventListener("click", openSidebar);
closeSidebarButton.addEventListener("click", closeSidebar);
toggleDetailsButton.addEventListener("click", () => {
    if (body.classList.contains("details-open")) {
        closeDetails();
    } else {
        openDetails();
    }
});
closeDetailsButton.addEventListener("click", closeDetails);
mobileOverlay.addEventListener("click", () => {
    closeSidebar();
    closeDetails();
});
caseModalClose.addEventListener("click", closeCaseModal);
caseCancelButton.addEventListener("click", closeCaseModal);
caseModal.addEventListener("click", (event) => {
    if (event.target.matches("[data-close-modal='true']")) {
        closeCaseModal();
    }
});
caseForm.addEventListener("submit", handleCreateCase);

window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeSidebar();
        closeDetails();
        if (!caseModal.hidden) {
            closeCaseModal();
        }
    }
});

boot();
