"use strict";

const form = document.getElementById("chat-form");
const input = document.getElementById("question");
const sendButton = document.getElementById("send-button");
const messages = document.getElementById("messages");
const conversation = document.getElementById("conversation");
const welcomeScreen = document.getElementById("welcome-screen");
const chatView = document.getElementById("chat-view");
const guideView = document.getElementById("guide-view");
const chatNav = document.getElementById("chat-nav");
const guideNav = document.getElementById("guide-nav");
const mobileGuideNav = document.getElementById("mobile-guide-nav");
const pageContext = document.getElementById("page-context");
let sessionId = sessionStorage.getItem("makerere-support-session");

function createSessionId() {
  return `web_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

if (!sessionId) {
  sessionId = createSessionId();
  sessionStorage.setItem("makerere-support-session", sessionId);
}

function showView(view) {
  const isGuide = view === "guide";
  chatView.hidden = isGuide;
  guideView.hidden = !isGuide;
  chatView.classList.toggle("active", !isGuide);
  guideView.classList.toggle("active", isGuide);
  chatNav.classList.toggle("active", !isGuide);
  guideNav.classList.toggle("active", isGuide);
  mobileGuideNav.textContent = isGuide ? "Back to chat" : "How it works";
  pageContext.textContent = isGuide ? "How it works" : "Student support";

  if (isGuide) {
    guideNav.setAttribute("aria-current", "page");
    chatNav.removeAttribute("aria-current");
  } else {
    chatNav.setAttribute("aria-current", "page");
    guideNav.removeAttribute("aria-current");
  }
}

chatNav.addEventListener("click", () => showView("chat"));
guideNav.addEventListener("click", () => showView("guide"));
mobileGuideNav.addEventListener("click", () => showView(guideView.hidden ? "guide" : "chat"));
document.getElementById("back-to-chat").addEventListener("click", () => showView("chat"));

function appendInlineText(parent, text) {
  const emphasis = /\*\*([^*]+)\*\*/g;
  let start = 0;
  let match;

  while ((match = emphasis.exec(text)) !== null) {
    parent.append(document.createTextNode(text.slice(start, match.index)));
    const strong = document.createElement("strong");
    strong.textContent = match[1];
    parent.append(strong);
    start = emphasis.lastIndex;
  }

  parent.append(document.createTextNode(text.slice(start)));
}

function appendFormattedText(parent, text) {
  const paragraphs = text.trim().split(/\n\s*\n/);
  for (const paragraph of paragraphs) {
    const lines = paragraph.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    if (!lines.length) continue;

    const heading = lines.length === 1 ? lines[0].match(/^#{1,3}\s+(.+)$/) : null;
    if (heading) {
      const element = document.createElement("h3");
      appendInlineText(element, heading[1]);
      parent.append(element);
      continue;
    }

    const isList = lines.every((line) => /^([-*]|\d+[.)])\s+/.test(line));
    if (isList) {
      const ordered = /^\d+[.)]\s+/.test(lines[0]);
      const list = document.createElement(ordered ? "ol" : "ul");
      for (const line of lines) {
        const item = document.createElement("li");
        appendInlineText(item, line.replace(/^([-*]|\d+[.)])\s+/, ""));
        list.append(item);
      }
      parent.append(list);
      continue;
    }

    const element = document.createElement("p");
    lines.forEach((line, index) => {
      if (index) element.append(document.createElement("br"));
      appendInlineText(element, line);
    });
    parent.append(element);
  }
}

function citationKey(value) {
  return value.toLowerCase().replace(/[\[\]\s.,;:()_-]/g, "");
}

function renderAnswer(parent, text, citations) {
  const citationPattern = /\[([A-Za-z0-9_\-]+,\s*Pages?\s+\d+(?:-\d+)?)\]/gi;
  const references = (citations || []).map((citation) => ({
    citation: String(citation).replace(/^\[|\]$/g, ""),
    title: "",
  }));

  // Clean raw prefixes if present
  let cleanText = text.trim();
  const rawPrefix = /^According to official Makerere University policy:\s*/i;
  const rawPrefix2 = /^Based on official Makerere University policy[,:]?\s*(here is the relevant guidance[^:]*:\s*)?/i;
  cleanText = cleanText.replace(rawPrefix, "").replace(rawPrefix2, "");

  // Strip trailing "Sources: ..." list from the body because we display references separately
  cleanText = cleanText.replace(/\n*\s*\*\*Sources:\*\*[\s\S]*$/i, "");
  cleanText = cleanText.replace(/\n*\s*Sources?:\s*\[?[mak-policy-[\s\S]*$/i, "");

  // Map any inline citations to clean numerical footnotes
  let footnoteMap = new Map();
  cleanText = cleanText.replace(citationPattern, (match, tag) => {
    let cleanTag = tag.trim();
    if (!footnoteMap.has(cleanTag)) {
      let refIdx = references.findIndex((r) => r.citation.toLowerCase() === cleanTag.toLowerCase());
      if (refIdx < 0) {
        references.push({ citation: cleanTag, title: "" });
        refIdx = references.length - 1;
      }
      footnoteMap.set(cleanTag, refIdx + 1);
    }
    const num = footnoteMap.get(cleanTag);
    return ` **[${num}]**`;
  });

  // Render the formatted answer
  appendFormattedText(parent, cleanText);

  // Render references in a neat collapsible section
  if (references.length) {
    const details = document.createElement("details");
    details.className = "references";
    details.style.marginTop = "0.75rem";
    details.style.fontSize = "0.85rem";
    const summary = document.createElement("summary");
    summary.style.cursor = "pointer";
    summary.style.fontWeight = "600";
    summary.style.color = "var(--color-primary, #006633)";
    summary.textContent = `Official Policy Sources (${references.length})`;
    const list = document.createElement("ol");
    list.className = "references-list";
    list.style.paddingLeft = "1.25rem";
    list.style.marginTop = "0.4rem";
    references.forEach((reference) => {
      const item = document.createElement("li");
      item.style.marginBottom = "0.25rem";
      item.textContent = reference.title
        ? `${reference.title} - ${reference.citation}`
        : reference.citation;
      list.append(item);
    });
    details.append(summary, list);
    parent.append(details);
  }
}

function addMessage(role, text, options = {}) {
  const message = document.createElement("article");
  message.className = `message ${role}`;

  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  if (role === "assistant") {
    const logo = document.createElement("img");
    logo.src = "/static/makerere-crest.png";
    logo.alt = "";
    avatar.append(logo);
  }

  const body = document.createElement("div");
  body.className = "message-body";
  const label = document.createElement("div");
  label.className = "message-label";
  label.textContent = role === "assistant" ? "Makerere Support" : "You";

  if (options.status) {
    const status = document.createElement("span");
    status.className = `status-pill ${options.status}`;
    status.textContent = {
      success: "Policy guidance",
      refused: "Safety notice",
      fallback: "Could not verify",
    }[options.status] || options.status;
    label.append(status);
  }

  body.append(label);
  if (role === "assistant") {
    renderAnswer(body, text, options.citations || []);
  } else {
    const content = document.createElement("p");
    content.className = "message-text";
    content.textContent = text;
    body.append(content);
  }

  if (options.escalation) {
    const escalation = document.createElement("div");
    escalation.className = "escalation";
    escalation.textContent = `For further help, contact: ${options.escalation}`;
    body.append(escalation);
  }

  message.append(avatar, body);
  messages.append(message);
  conversation.scrollTop = conversation.scrollHeight;
}

function setLoading(loading) {
  sendButton.disabled = loading;
  input.disabled = loading;
  sendButton.setAttribute("aria-label", loading ? "Sending message" : "Send message");
}

function addLoadingMessage() {
  const message = document.createElement("article");
  message.className = "message assistant";
  message.id = "loading-message";
  message.setAttribute("aria-label", "Assistant is finding an answer");

  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  const logo = document.createElement("img");
  logo.src = "/static/makerere-crest.png";
  logo.alt = "";
  avatar.append(logo);

  const body = document.createElement("div");
  body.className = "message-body";
  const label = document.createElement("div");
  label.className = "message-label";
  label.textContent = "Searching available guidance";
  const dots = document.createElement("div");
  dots.className = "loading-dots";
  dots.setAttribute("aria-hidden", "true");
  for (let index = 0; index < 3; index += 1) dots.append(document.createElement("span"));

  body.append(label, dots);
  message.append(avatar, body);
  messages.append(message);
  conversation.scrollTop = conversation.scrollHeight;
}

async function submitQuestion(question) {
  const trimmed = question.trim();
  if (!trimmed || sendButton.disabled) return;

  welcomeScreen.hidden = true;
  addMessage("user", trimmed);
  input.value = "";
  input.style.height = "auto";
  setLoading(true);
  addLoadingMessage();

  try {
    const response = await fetch("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: trimmed, session_id: sessionId }),
    });
    const data = await response.json();
    if (!response.ok) {
      const detail = typeof data.detail === "string" ? data.detail : "The support service could not process that question.";
      throw new Error(detail);
    }
    document.getElementById("loading-message")?.remove();
    addMessage("assistant", data.response, {
      status: data.status,
      citations: Array.isArray(data.citations) ? data.citations : [],
      escalation: data.escalation_office,
    });
  } catch (error) {
    document.getElementById("loading-message")?.remove();
    addMessage(
      "assistant",
      `I couldn’t reach the support service. ${error instanceof Error ? error.message : "Please try again in a moment."}`,
      { status: "fallback" },
    );
  } finally {
    setLoading(false);
    input.focus();
  }
}

function startNewChat() {
  messages.replaceChildren();
  welcomeScreen.hidden = false;
  conversation.scrollTop = 0;
  sessionId = createSessionId();
  sessionStorage.setItem("makerere-support-session", sessionId);
  input.value = "";
  input.style.height = "auto";
  showView("chat");
  input.focus();
}

document.getElementById("new-chat").addEventListener("click", startNewChat);

form.addEventListener("submit", (event) => {
  event.preventDefault();
  submitQuestion(input.value);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    submitQuestion(button.querySelector("span:last-child").textContent);
  });
});
