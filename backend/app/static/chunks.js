const chunksForm = document.querySelector("#chunks-form");
const viewerIndexSelect = document.querySelector("#viewer-index-name");
const viewerNamespaceSelect = document.querySelector("#viewer-namespace");
const viewerLimitInput = document.querySelector("#viewer-limit");
const chunksButton = document.querySelector("#chunks-button");
const chunksStatus = document.querySelector("#chunks-status");
const chunksResultPanel = document.querySelector("#chunks-result-panel");
const chunksMeta = document.querySelector("#chunks-meta");
const viewerChunksList = document.querySelector("#viewer-chunks-list");
const chunksErrorPanel = document.querySelector("#chunks-error-panel");
const chunksErrorMessage = document.querySelector("#chunks-error-message");

function resetChunkPanels() {
  chunksResultPanel.classList.add("hidden");
  chunksErrorPanel.classList.add("hidden");
  chunksMeta.innerHTML = "";
  viewerChunksList.innerHTML = "";
  chunksErrorMessage.textContent = "";
}

function setViewerBusy(isBusy) {
  chunksButton.disabled = isBusy;
  chunksButton.textContent = isBusy ? "Loading..." : "Load chunks";
  viewerIndexSelect.disabled = isBusy;
  viewerNamespaceSelect.disabled = isBusy;
  viewerLimitInput.disabled = isBusy;
}

function showChunkError(message) {
  chunksErrorMessage.textContent = message;
  chunksErrorPanel.classList.remove("hidden");
}

function setSelectOptions(select, options, placeholder) {
  select.innerHTML = "";

  if (placeholder) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = placeholder;
    select.append(option);
  }

  for (const item of options) {
    const option = document.createElement("option");
    option.value = item.value;
    option.textContent = item.label;
    select.append(option);
  }
}

async function getJson(url) {
  const response = await fetch(url);
  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(body.detail || `Request failed with status ${response.status}`);
  }

  return body;
}

async function loadIndexes() {
  resetChunkPanels();
  chunksStatus.textContent = "Loading available Pinecone indexes...";
  viewerIndexSelect.disabled = true;
  viewerNamespaceSelect.disabled = true;
  chunksButton.disabled = true;

  try {
    const body = await getJson("/pinecone/indexes");
    const indexes = Array.isArray(body.indexes) ? body.indexes : [];

    setSelectOptions(
      viewerIndexSelect,
      indexes.map((name) => ({ value: name, label: name })),
      indexes.length ? "Select an index" : "No indexes found"
    );

    chunksStatus.textContent = indexes.length
      ? "Select an index and namespace."
      : "No Pinecone indexes are available.";

    viewerIndexSelect.disabled = indexes.length === 0;
    chunksButton.disabled = indexes.length === 0;

    if (indexes.length === 1) {
      viewerIndexSelect.value = indexes[0];
      await loadNamespaces(indexes[0]);
    }
  } catch (error) {
    chunksStatus.textContent = "";
    setSelectOptions(viewerIndexSelect, [], "Unable to load indexes");
    showChunkError(error.message || "Could not load Pinecone indexes.");
  }
}

async function loadNamespaces(indexName) {
  resetChunkPanels();
  viewerNamespaceSelect.disabled = true;
  setSelectOptions(viewerNamespaceSelect, [], "Loading namespaces...");

  if (!indexName) {
    chunksStatus.textContent = "Select an index.";
    setSelectOptions(viewerNamespaceSelect, [], "Select an index first");
    return;
  }

  chunksStatus.textContent = "Loading namespaces...";

  try {
    const params = new URLSearchParams({ index_name: indexName });
    const body = await getJson(`/pinecone/namespaces?${params.toString()}`);
    const namespaces = Array.isArray(body.namespaces) ? body.namespaces : [];

    setSelectOptions(
      viewerNamespaceSelect,
      namespaces.map((item) => ({
        value: item.name,
        label: `${item.name} (${item.vector_count} vectors)`,
      })),
      namespaces.length ? "Select a namespace" : "No namespaces found"
    );

    chunksStatus.textContent = namespaces.length
      ? "Select a namespace, then load chunks."
      : "No namespaces are available for this index.";

    viewerNamespaceSelect.disabled = namespaces.length === 0;

    if (namespaces.length === 1) {
      viewerNamespaceSelect.value = namespaces[0].name;
    }
  } catch (error) {
    chunksStatus.textContent = "";
    setSelectOptions(viewerNamespaceSelect, [], "Unable to load namespaces");
    showChunkError(error.message || "Could not load namespaces.");
  }
}

function appendMetaItem(label, value) {
  const term = document.createElement("dt");
  term.textContent = label;

  const description = document.createElement("dd");
  description.textContent = value ?? "";

  chunksMeta.append(term, description);
}

function appendViewerChunk(chunk, index) {
  const article = document.createElement("article");
  article.className = "chunk";

  const title = document.createElement("h3");
  title.textContent = `${index}. ${chunk.id || "Unknown chunk"}`;

  const details = document.createElement("p");
  details.className = "chunk-score";
  const lineRange = chunk.start_line || chunk.end_line
    ? `Lines ${chunk.start_line || "?"}-${chunk.end_line || "?"}`
    : "Lines unavailable";
  details.textContent = [
    chunk.heading || "Untitled heading",
    lineRange,
    chunk.embedding_model || "Unknown model",
  ].join(" | ");

  const source = document.createElement("p");
  source.className = "chunk-source";
  source.textContent = chunk.source_file ? `Source: ${chunk.source_file}` : "Source unavailable";

  const text = document.createElement("p");
  text.className = "chunk-text";
  text.textContent = chunk.text || "";

  article.append(title, details, source, text);
  viewerChunksList.append(article);
}

function showChunks(data) {
  appendMetaItem("Pinecone index", data.index_name);
  appendMetaItem("Namespace", data.namespace);
  appendMetaItem("Chunks shown", data.count);

  const chunks = Array.isArray(data.chunks) ? data.chunks : [];
  if (chunks.length === 0) {
    const empty = document.createElement("p");
    empty.className = "chunk-text";
    empty.textContent = "No chunks were found in this namespace.";
    viewerChunksList.append(empty);
  } else {
    chunks.forEach((chunk, index) => appendViewerChunk(chunk, index + 1));
  }

  chunksResultPanel.classList.remove("hidden");
}

viewerIndexSelect.addEventListener("change", async () => {
  await loadNamespaces(viewerIndexSelect.value);
});

chunksForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetChunkPanels();

  const indexName = viewerIndexSelect.value.trim();
  const namespace = viewerNamespaceSelect.value.trim();
  const limit = Number.parseInt(viewerLimitInput.value, 10);

  if (!indexName) {
    showChunkError("Select a Pinecone index.");
    viewerIndexSelect.focus();
    return;
  }

  if (!namespace) {
    showChunkError("Select a Pinecone namespace.");
    viewerNamespaceSelect.focus();
    return;
  }

  if (!Number.isInteger(limit) || limit <= 0 || limit > 1000) {
    showChunkError("Limit must be between 1 and 1000.");
    viewerLimitInput.focus();
    return;
  }

  setViewerBusy(true);
  chunksStatus.textContent = "Loading chunk metadata from Pinecone...";

  try {
    const params = new URLSearchParams({
      index_name: indexName,
      namespace,
      limit: String(limit),
    });
    const body = await getJson(`/pinecone/chunks?${params.toString()}`);

    chunksStatus.textContent = "Chunks loaded.";
    showChunks(body);
  } catch (error) {
    chunksStatus.textContent = "";
    showChunkError(error.message || "Could not load chunks.");
  } finally {
    setViewerBusy(false);
  }
});

loadIndexes();
