const form = document.querySelector("#upload-form");
const fileInput = document.querySelector("#pdf-file");
const indexNameInput = document.querySelector("#index-name");
const namespaceInput = document.querySelector("#namespace");
const fileName = document.querySelector("#file-name");
const uploadButton = document.querySelector("#upload-button");
const statusBox = document.querySelector("#status");
const resultPanel = document.querySelector("#result-panel");
const resultList = document.querySelector("#result-list");
const errorPanel = document.querySelector("#error-panel");
const errorMessage = document.querySelector("#error-message");

const resultFields = [
  ["run_id", "Run ID"],
  ["uploaded_vectors", "Uploaded vectors"],
  ["markdown_path", "Markdown"],
  ["chunks_path", "Chunks"],
  ["embeddings_path", "Embeddings"],
  ["pinecone_index", "Pinecone index"],
  ["pinecone_namespace", "Namespace"],
];

function resetPanels() {
  resultPanel.classList.add("hidden");
  errorPanel.classList.add("hidden");
  resultList.innerHTML = "";
  errorMessage.textContent = "";
}

function setBusy(isBusy) {
  uploadButton.disabled = isBusy;
  uploadButton.textContent = isBusy ? "Processing..." : "Upload PDF";
  fileInput.disabled = isBusy;
  indexNameInput.disabled = isBusy;
  namespaceInput.disabled = isBusy;
}

function showError(message) {
  errorMessage.textContent = message;
  errorPanel.classList.remove("hidden");
}

function showResult(data) {
  resultList.innerHTML = "";

  for (const [key, label] of resultFields) {
    const term = document.createElement("dt");
    term.textContent = label;

    const description = document.createElement("dd");
    description.textContent = data[key] ?? "";

    resultList.append(term, description);
  }

  resultPanel.classList.remove("hidden");
}

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  fileName.textContent = file ? file.name : "No file selected";
  resetPanels();
  statusBox.textContent = "";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetPanels();

  const file = fileInput.files[0];
  if (!file) {
    showError("Select a PDF file before uploading.");
    return;
  }

  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showError("Only PDF files are supported.");
    return;
  }

  const indexName = indexNameInput.value.trim();
  const namespace = namespaceInput.value.trim();
  if (!indexName) {
    showError("Enter a Pinecone index name.");
    indexNameInput.focus();
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("index_name", indexName);
  formData.append("namespace", namespace);

  setBusy(true);
  statusBox.textContent = "Uploading and processing. This can take a minute or more...";

  try {
    const response = await fetch("/ingest/pdf", {
      method: "POST",
      body: formData,
    });

    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(body.detail || `Request failed with status ${response.status}`);
    }

    statusBox.textContent = "Processing complete.";
    showResult(body);
  } catch (error) {
    statusBox.textContent = "";
    showError(error.message || "Upload failed.");
  } finally {
    setBusy(false);
  }
});
