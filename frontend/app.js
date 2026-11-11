const API_URL = "http://localhost:3000/api";

const tableBody = document.getElementById("files-table-body");
const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const fileLabel = document.getElementById("file-label");
const statusMessage = document.getElementById("status-message");
const btnRefresh = document.getElementById("btn-refresh");

// Atualiza o texto quando um arquivo é selecionado
fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    fileLabel.textContent = `Arquivo selecionado: ${fileInput.files[0].name}`;
  } else {
    fileLabel.textContent = "Arraste um arquivo aqui ou clique para selecionar";
  }
});

// Formatar tamanho em bytes para KB ou MB
function formatSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// Formatar data ISO para padrão local
function formatDate(isoString) {
  if (!isoString) return "-";
  const date = new Date(isoString);
  return date.toLocaleString("pt-BR");
}

function showStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${isError ? "error" : "success"}`;
  setTimeout(() => {
    statusMessage.textContent = "";
    statusMessage.className = "status-message";
  }, 4000);
}

// Buscar e listar arquivos do backend
async function loadFiles() {
  tableBody.innerHTML = `<tr><td colspan="4" class="text-center">Carregando arquivos...</td></tr>`;

  try {
    const res = await fetch(`${API_URL}/files`);
    if (!res.ok) throw new Error("Falha ao consultar a API");

    const files = await res.json();

    if (files.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="4" class="text-center">Nenhum arquivo encontrado no bucket.</td></tr>`;
      return;
    }

    tableBody.innerHTML = "";
    files.forEach(file => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${file.name}</strong></td>
        <td>${formatSize(file.size)}</td>
        <td>${formatDate(file.lastModified)}</td>
        <td>
          <button class="btn-download" onclick="downloadFile('${file.name}')">Download</button>
          <button class="btn-delete" onclick="deleteFile('${file.name}')">Excluir</button>
        </td>
      `;
      tableBody.appendChild(tr);
    });
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="4" class="text-center" style="color: var(--danger)">Erro ao carregar arquivos: ${err.message}</td></tr>`;
  }
}

// Enviar arquivo
uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!fileInput.files.length) {
    showStatus("Selecione um arquivo primeiro.", true);
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    showStatus("Enviando arquivo para o S3...");
    const res = await fetch(`${API_URL}/upload`, {
      method: "POST",
      body: formData
    });

    if (!res.ok) throw new Error("Erro no envio do arquivo");

    showStatus("Arquivo enviado com sucesso!");
    uploadForm.reset();
    fileLabel.textContent = "Arraste um arquivo aqui ou clique para selecionar";
    loadFiles();
  } catch (err) {
    showStatus(`Erro: ${err.message}`, true);
  }
});

// Download via URL segura (pré-assinada)
async function downloadFile(fileName) {
  try {
    const res = await fetch(`${API_URL}/download/${encodeURIComponent(fileName)}`);
    if (!res.ok) throw new Error("Não foi possível gerar link de download");

    const data = await res.json();
    window.open(data.url, "_blank");
  } catch (err) {
    alert(`Erro ao baixar arquivo: ${err.message}`);
  }
}

// Excluir arquivo
async function deleteFile(fileName) {
  if (!confirm(`Deseja realmente excluir "${fileName}"?`)) return;

  try {
    const res = await fetch(`${API_URL}/files/${encodeURIComponent(fileName)}`, {
      method: "DELETE"
    });

    if (!res.ok) throw new Error("Erro ao excluir arquivo");

    showStatus("Arquivo excluído com sucesso.");
    loadFiles();
  } catch (err) {
    alert(`Erro: ${err.message}`);
  }
}

btnRefresh.addEventListener("click", loadFiles);

// Carregamento inicial
loadFiles();
