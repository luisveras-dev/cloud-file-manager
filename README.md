# Cloud Drive - Gerenciador de Arquivos em Nuvem

Aplicação desenvolvida para o Projeto Final da disciplina de Computação em Nuvem (UNIMA).

Permite enviar, listar, visualizar metadados, baixar com link seguro e excluir arquivos utilizando a infraestrutura da **AWS (Amazon Web Services)**.

---

## Estrutura do Repositório

```text
├── backend/          # API Node.js integrada com AWS S3
│   ├── server.js     # Servidor Express e rotas HTTP
│   ├── s3Service.js  # Lógica de integração com AWS SDK v3
│   └── package.json
├── frontend/         # Interface Web (HTML, CSS e JavaScript puro)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docs/             # Documentação técnica e guia do relatório
│   └── arquitetura.md
└── README.md
```

---

## Como Executar Localmente

### 1. Pré-requisitos
* Node.js (versão 18 ou superior) instalado.
* Conta AWS com credenciais de acesso (`Access Key` e `Secret Key`) e um bucket S3 criado.

### 2. Configurar o Backend
1. Acesse a pasta do backend:
   ```bash
   cd backend
   ```
2. Instale as dependências:
   ```bash
   npm install
   ```
3. Crie o arquivo `.env` com base no `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Preencha as credenciais da AWS no arquivo `.env`:
   ```env
   PORT=3000
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=sua_access_key_aqui
   AWS_SECRET_ACCESS_KEY=sua_secret_key_aqui
   AWS_S3_BUCKET_NAME=nome-do-seu-bucket-aqui
   ```
5. Inicie a aplicação:
   ```bash
   npm start
   ```
   O servidor estará rodando em `http://localhost:3000`.

### 3. Executar o Frontend
Basta abrir o arquivo `frontend/index.html` diretamente em seu navegador (ou utilizando extensões como o *Live Server* no VS Code).

---

## Segurança (Requisito R6)
* As credenciais da AWS **nunca** são enviadas para o frontend nem versionadas no Git.
* O arquivo `.env` está explicitamente ignorado no `.gitignore`.
* Os downloads utilizam URLs pré-assinadas temporárias com validade de 15 minutos geradas pelo backend.
