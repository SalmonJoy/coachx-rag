const chatForm = document.querySelector("#chat-form");
const queryInput = document.querySelector("#query");
const chatIndexNameInput = document.querySelector("#chat-index-name");
const chatNamespaceInput = document.querySelector("#chat-namespace");
const topKInput = document.querySelector("#top-k");
const chatButton = document.querySelector("#chat-button");
const chatStatus = document.querySelector("#chat-status");
const answerPanel = document.querySelector("#answer-panel");
const answerText = document.querySelector("#answer-text");
const chatMeta = document.querySelector("#chat-meta");
const chunksList = document.querySelector("#chunks-list");
const chatErrorPanel = document.querySelector("#chat-error-panel");
const chatErrorMessage = document.querySelector("#chat-error-message");

const metaFields = [
  ["index_name", "Pinecone index"],
  ["namespace", "Namespace"],
  ["top_k", "Top K"],
];

function resetChatPanels() {
  answerPanel.classList.add("hidden");
  chatErrorPanel.classList.add("hidden");
  answerText.textContent = "";
  chatMeta.innerHTML = "";
  chunksList.innerHTML = "";
  chatErrorMessage.textContent = "";
}

function setChatBusy(isBusy) {
  chatButton.disabled = isBusy;
  chatButton.textContent = isBusy ? "Searching..." : "Ask question";
  queryInput.disabled = isBusy;
  chatIndexNameInput.disabled = isBusy;
  chatNamespaceInput.disabled = isBusy;
  topKInput.disabled = isBusy;
}

function showChatError(message) {
  chatErrorMessage.textContent = message;
  chatErrorPanel.classList.remove("hidden");
}

function appendMeta(data) {
  for (const [key, label] of metaFields) {
    const term = document.createElement("dt");
    term.textContent = label;

    const description = document.createElement("dd");
    description.textContent = data[key] ?? "";

    chatMeta.append(term, description);
  }
}

function appendChunk(chunk, index) {
  const article = document.createElement("article");
  article.className = "chunk";

  const title = document.createElement("h3");
  title.textContent = `${index}. ${chunk.id || "Unknown chunk"}`;

  const score = document.createElement("p");
  score.className = "chunk-score";
  const numericScore = Number(chunk.score);
  score.textContent = Number.isFinite(numericScore)
    ? `Score: ${numericScore.toFixed(4)}`
    : "Score: unavailable";

  const text = document.createElement("p");
  text.className = "chunk-text";
  text.textContent = chunk.text || "";

  article.append(title, score, text);
  chunksList.append(article);
}

function showAnswer(data) {
  answerText.textContent = data.answer || "";
  appendMeta(data);

  const chunks = Array.isArray(data.chunks) ? data.chunks : [];
  if (chunks.length === 0) {
    const empty = document.createElement("p");
    empty.className = "chunk-text";
    empty.textContent = "No source chunks were returned.";
    chunksList.append(empty);
  } else {
    chunks.forEach((chunk, index) => appendChunk(chunk, index + 1));
  }

  answerPanel.classList.remove("hidden");
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetChatPanels();

  const query = queryInput.value.trim();
  const indexName = chatIndexNameInput.value.trim();
  const namespace = chatNamespaceInput.value.trim();
  const topK = Number.parseInt(topKInput.value, 10);

  if (!query) {
    showChatError("Enter a question.");
    queryInput.focus();
    return;
  }

  if (!indexName) {
    showChatError("Enter a Pinecone index name.");
    chatIndexNameInput.focus();
    return;
  }

  if (!Number.isInteger(topK) || topK <= 0) {
    showChatError("Top K must be a number greater than 0.");
    topKInput.focus();
    return;
  }

  setChatBusy(true);
  chatStatus.textContent = "Embedding the question, searching Pinecone, and generating an answer...";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        index_name: indexName,
        namespace,
        top_k: topK,
      }),
    });

    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(body.detail || `Request failed with status ${response.status}`);
    }

    chatStatus.textContent = "Answer ready.";
    showAnswer(body);
  } catch (error) {
    chatStatus.textContent = "";
    showChatError(error.message || "Chat request failed.");
  } finally {
    setChatBusy(false);
  }
});
