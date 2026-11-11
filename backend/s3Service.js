const {
  S3Client,
  ListObjectsV2Command,
  PutObjectCommand,
  GetObjectCommand,
  DeleteObjectCommand
} = require("@aws-sdk/client-s3");
const { getSignedUrl } = require("@aws-sdk/s3-request-presigner");

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  }
});

const BUCKET = process.env.AWS_S3_BUCKET_NAME;

async function listFiles() {
  const command = new ListObjectsV2Command({ Bucket: BUCKET });
  const response = await s3.send(command);

  if (!response.Contents) return [];

  return response.Contents.map(item => ({
    name: item.Key,
    size: item.Size,
    lastModified: item.LastModified
  }));
}

async function uploadFile(file) {
  const command = new PutObjectCommand({
    Bucket: BUCKET,
    Key: file.originalname,
    Body: file.buffer,
    ContentType: file.mimetype
  });

  await s3.send(command);
  return { name: file.originalname, size: file.size };
}

async function getDownloadUrl(fileName) {
  const command = new GetObjectCommand({
    Bucket: BUCKET,
    Key: fileName,
    ResponseContentDisposition: `attachment; filename="${fileName}"`
  });

  // URL temporária válida por 15 minutos
  return await getSignedUrl(s3, command, { expiresIn: 900 });
}

async function deleteFile(fileName) {
  const command = new DeleteObjectCommand({
    Bucket: BUCKET,
    Key: fileName
  });

  await s3.send(command);
  return { message: "Arquivo removido com sucesso" };
}

module.exports = {
  listFiles,
  uploadFile,
  getDownloadUrl,
  deleteFile
};
