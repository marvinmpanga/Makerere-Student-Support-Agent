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

function parseMarkdown(markdownText) {
  if (typeof marked !== "undefined" && typeof marked.parse === "function") {
    return marked.parse(markdownText);
  }
  // Simple fallback parser if marked CDN fails to load
  let html = markdownText
    .replace(/^### (.*$)/gim, "<h3>$1</h3>")
    .replace(/^## (.*$)/gim, "<h2>$1</h2>")
    .replace(/^# (.*$)/gim, "<h1>$1</h1>")
    .replace(/\*\*(.*?)\*\*/gim, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/gim, "<em>$1</em>")
    .replace(/^\* (.*$)/gim, "<li>$1</li>")
    .replace(/^\- (.*$)/gim, "<li>$1</li>")
    .replace(/\n\n+/gim, "</p><p>")
    .replace(/\n/gim, "<br>");
  return `<p>${html}</p>`.replace(/<p><\/p>/g, "");
}

function prepareAnswerContent(text, citations) {
  const citationPattern = /\[([A-Za-z0-9_\-]+,\s*Pages?\s+\d+(?:-\d+)?)\]/gi;
  const references = (citations || []).map((c) => ({
    citation: String(c).replace(/^\[|\]$/g, ""),
    title: "",
  }));

  let cleanText = text.trim();
  cleanText = cleanText.replace(/^According to official Makerere University policy:\s*/i, "");
  cleanText = cleanText.replace(/^Based on official Makerere University policy[,:]?\s*(here is the relevant guidance[^:]*:\s*)?/i, "");
  cleanText = cleanText.replace(/\n*\s*\*\*Sources:\*\*[\s\S]*$/i, "");
  cleanText = cleanText.replace(/\n*\s*Sources?:\s*\[?[mak-policy-[\s\S]*$/i, "");

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
    return `<sup class="footnote-ref" title="${cleanTag}">[${num}]</sup>`;
  });

  return { html: parseMarkdown(cleanText), rawText: cleanText, references };
}

function createTypewriterEffect(element, fullHtml, onComplete) {
  // Real-time streaming simulation: reveals words in smooth natural cadence
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = fullHtml;
  const fullText = tempDiv.innerText || tempDiv.textContent || "";
  
  if (fullText.length < 50) {
    element.innerHTML = fullHtml;
    if (onComplete) onComplete();
    return;
  }

  element.innerHTML = '<span class="typewriter-cursor"></span>';
  let charIndex = 0;
  const totalChars = fullHtml.length;
  const chunkStep = 5; // characters per tick for smooth streaming

  const timer = setInterval(() => {
    charIndex = Math.min(charIndex + chunkStep, totalChars);
    // Find nearest safe HTML tag boundary
    let safeSubstr = fullHtml.slice(0, charIndex);
    // If inside a tag, extend to closing '>'
    const lastOpen = safeSubstr.lastIndexOf("<");
    const lastClose = safeSubstr.lastIndexOf(">");
    if (lastOpen > lastClose) {
      const nextClose = fullHtml.indexOf(">", lastOpen);
      if (nextClose !== -1) {
        charIndex = nextClose + 1;
        safeSubstr = fullHtml.slice(0, charIndex);
      }
    }

    element.innerHTML = safeSubstr + '<span class="typewriter-cursor"></span>';
    conversation.scrollTop = conversation.scrollHeight;

    if (charIndex >= totalChars) {
      clearInterval(timer);
      element.innerHTML = fullHtml;
      if (onComplete) onComplete();
    }
  }, 18);
}

function renderReferencesDrawer(parent, references) {
  if (!references || !references.length) return;
  const details = document.createElement("details");
  details.className = "references";
  details.style.marginTop = "0.85rem";
  details.style.fontSize = "0.85rem";
  
  const summary = document.createElement("summary");
  summary.style.cursor = "pointer";
  summary.style.fontWeight = "600";
  summary.style.color = "var(--makerere-green, #00843d)";
  summary.textContent = `Official Policy Sources (${references.length})`;
  
  const list = document.createElement("ol");
  list.className = "references-list";
  list.style.paddingLeft = "1.25rem";
  list.style.marginTop = "0.5rem";
  
  references.forEach((ref) => {
    const item = document.createElement("li");
    item.style.marginBottom = "0.3rem";
    item.textContent = ref.title ? `${ref.title} — ${ref.citation}` : ref.citation;
    list.append(item);
  });
  
  details.append(summary, list);
  parent.append(details);
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
    const { html, references } = prepareAnswerContent(text, options.citations || []);
    const content = document.createElement("div");
    content.className = "message-text markdown-body";

    if (options.stream) {
      createTypewriterEffect(content, html, () => {
        renderReferencesDrawer(body, references);
        if (options.escalation) {
          const escalation = document.createElement("div");
          escalation.className = "escalation";
          escalation.textContent = `For further help, contact: ${options.escalation}`;
          body.append(escalation);
        }
        conversation.scrollTop = conversation.scrollHeight;
      });
    } else {
      content.innerHTML = html;
      renderReferencesDrawer(body, references);
    }
    body.append(content);
  } else {
    const content = document.createElement("p");
    content.className = "message-text";
    content.textContent = text;
    body.append(content);
  }

  if (role !== "assistant" && options.escalation) {
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
  label.textContent = "Checking university policies";
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
      stream: true,
    });
  } catch (error) {
    document.getElementById("loading-message")?.remove();
    addMessage(
      "assistant",
      `I couldn't reach the support service. ${error instanceof Error ? error.message : "Please try again in a moment."}`,
      { status: "fallback", stream: false },
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
