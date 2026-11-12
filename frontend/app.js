// Endpoints oficiais provisionados no AWS API Gateway
const API_LIST_URL = "https://cue8igv428.execute-api.us-east-2.amazonaws.com/prod";
const API_DOWNLOAD_URL = "https://87oyrf9w8a.execute-api.us-east-2.amazonaws.com/prod";
const API_UPLOAD_URL = "https://veicu6cgzb.execute-api.us-east-2.amazonaws.com/prod";

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
  if (!bytes || bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// Formatar data para padrão legível
function formatDate(dateStr) {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
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

// Buscar e listar arquivos do bucket S3 via API Gateway
async function loadFiles() {
  tableBody.innerHTML = `<tr><td colspan="4" class="text-center">Consultando arquivos na AWS...</td></tr>`;

  try {
    const res = await fetch(API_LIST_URL);
    if (!res.ok) throw new Error(`Falha ao consultar a API (${res.status})`);

    const data = await res.json();
    const files = data.files || [];

    if (files.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="4" class="text-center">Nenhum arquivo encontrado no bucket S3.</td></tr>`;
      return;
    }

    tableBody.innerHTML = "";
    files.forEach(file => {
      const fileName = file.key || file.name;
      const fileSize = file.size_bytes !== undefined ? file.size_bytes : file.size;
      const fileDate = file.last_modified || file.lastModified;

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${fileName}</strong></td>
        <td>${formatSize(fileSize)}</td>
        <td>${formatDate(fileDate)}</td>
        <td>
          <button class="btn-download" onclick="downloadFile('${fileName}')">Download</button>
        </td>
      `;
      tableBody.appendChild(tr);
    });
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="4" class="text-center" style="color: var(--danger)">Erro ao carregar arquivos da AWS: ${err.message}</td></tr>`;
  }
}

// Enviar arquivo: 1) Pede presigned URL para a Lambda; 2) Envia o arquivo direto para o S3
uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!fileInput.files.length) {
    showStatus("Selecione um arquivo primeiro.", true);
    return;
  }

  const selectedFile = fileInput.files[0];

  try {
    showStatus("Solicitando permissão de upload à AWS...");

    // Passo 1: Obter a presigned URL de upload
    const presignRes = await fetch(API_UPLOAD_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: selectedFile.name })
    });

    if (!presignRes.ok) {
      throw new Error(`Erro ao gerar link de upload (${presignRes.status})`);
    }

    const { upload_url } = await presignRes.json();
    if (!upload_url) {
      throw new Error("Resposta da AWS não continha a URL de upload.");
    }

    showStatus("Enviando arquivo diretamente para o S3...");

    // Passo 2: Upload direto para o S3 via PUT
    const uploadRes = await fetch(upload_url, {
      method: "PUT",
      body: selectedFile
    });

    if (!uploadRes.ok) {
      throw new Error(`Falha no upload para o S3 (${uploadRes.status})`);
    }

    showStatus("Arquivo enviado com sucesso para a AWS!");
    uploadForm.reset();
    fileLabel.textContent = "Arraste um arquivo aqui ou clique para selecionar";
    loadFiles();
  } catch (err) {
    showStatus(`Erro: ${err.message}`, true);
  }
});

// Download via URL temporária segura do S3
async function downloadFile(fileName) {
  try {
    const res = await fetch(`${API_DOWNLOAD_URL}?key=${encodeURIComponent(fileName)}`);
    if (!res.ok) throw new Error("Não foi possível gerar link de download");

    const data = await res.json();
    if (!data.presigned_url) throw new Error("URL de download não retornada");

    window.open(data.presigned_url, "_blank");
  } catch (err) {
    alert(`Erro ao baixar arquivo: ${err.message}`);
  }
}

btnRefresh.addEventListener("click", loadFiles);

// Carregamento inicial ao abrir a página
loadFiles();
