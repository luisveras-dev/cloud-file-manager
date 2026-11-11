# Arquitetura e Guia do Projeto (Cloud Drive)

Documento de apoio para o integrante responsável pelo **Relatório Técnico** e **Diagrama**.

---

## 1. Visão Geral da Solução
* **Nome do Projeto:** Cloud Drive - Sistema de Gerenciamento de Arquivos em Nuvem
* **Objetivo:** Permitir aos usuários fazer upload, listar com metadados, baixar com link temporário seguro e deletar arquivos na nuvem.
* **Provedor Cloud:** AWS (Amazon Web Services).

---

## 2. Componentes e Serviços Utilizados
* **Armazenamento Persistente (PaaS / Object Storage):**
  * **AWS S3 (Simple Storage Service):** Armazena os arquivos de maneira durável e escalável em um bucket privado.
* **Processamento e API (PaaS / Computação):**
  * **Node.js (API Express):** Executa as regras de validação, manipulação do stream de dados e comunicação autenticada com o S3 via AWS SDK v3.
* **Interface do Usuário (Frontend):**
  * HTML5, CSS3 moderno e Vanilla JavaScript.

---

## 3. Fluxo de Dados (Para o Diagrama de Arquitetura)
```text
[ Usuário / Navegador ]
         │
         ▼  (HTTP / JSON)
[ Frontend (HTML / JS) ]
         │
         ▼  (Chamadas REST: /upload, /files, /download)
[ Backend (Node.js API) ]  <─── Autenticação via Variáveis de Ambiente (.env)
         │
         ▼  (AWS SDK v3 via HTTPS)
[ AWS S3 Bucket ] (Armazenamento de Objetos)
```

---

## 4. Requisitos Atendidos para o Relatório
* **R1 (Nuvem):** Utilização de serviços gerenciados na nuvem da AWS.
* **R2 (Armazenamento):** AWS S3 armazena os arquivos binários de forma persistente.
* **R3 (Processamento):** O backend processa o arquivo em memória, extrai metadados (nome, tamanho, mimetype, data) e gera URLs pré-assinadas temporárias.
* **R4 (Aplicação Funcional):** Interface web intuitiva com upload, listagem e ações em tempo real.
* **R5 (Integração):** Integração direta entre Frontend -> Backend -> S3.
* **R6 (Segurança):** Credenciais da AWS (`ACCESS_KEY` e `SECRET_KEY`) ficam salvas apenas no `.env` do backend, nunca expostas no código-fonte nem no navegador. Downloads são protegidos com URLs assinadas válidas por 15 minutos.
