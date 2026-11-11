require("dotenv").config();
const express = require("express");
const cors = require("cors");
const multer = require("multer");
const s3Service = require("./s3Service");

const app = express();
const port = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Limite de 50MB por arquivo em memória
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 50 * 1024 * 1024 }
});

// Listar arquivos
app.get("/api/files", async (req, res) => {
  try {
    const files = await s3Service.listFiles();
    res.json(files);
  } catch (error) {
    res.status(500).json({ error: "Erro ao listar arquivos do S3", details: error.message });
  }
});

// Fazer upload
app.post("/api/upload", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "Nenhum arquivo enviado" });
    }

    const uploaded = await s3Service.uploadFile(req.file);
    res.status(201).json(uploaded);
  } catch (error) {
    res.status(500).json({ error: "Erro ao enviar arquivo para o S3", details: error.message });
  }
});

// Obter link de download
app.get("/api/download/:fileName", async (req, res) => {
  try {
    const { fileName } = req.params;
    const downloadUrl = await s3Service.getDownloadUrl(fileName);
    res.json({ url: downloadUrl });
  } catch (error) {
    res.status(500).json({ error: "Erro ao gerar link de download", details: error.message });
  }
});

// Deletar arquivo
app.delete("/api/files/:fileName", async (req, res) => {
  try {
    const { fileName } = req.params;
    const result = await s3Service.deleteFile(fileName);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: "Erro ao deletar arquivo", details: error.message });
  }
});

app.listen(port, () => {
  console.log(`Backend rodando em http://localhost:${port}`);
});
