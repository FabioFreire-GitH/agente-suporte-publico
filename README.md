# 🤖 Agente de Suporte RAG (Retrieval-Augmented Generation)

Este repositório contém o código-fonte de um **Produto Mínimo Viável (MVP)** de um Assistente de Suporte Técnico baseado em IA. Ele utiliza a arquitetura RAG para fornecer respostas precisas e contextualizadas com base na documentação oficial de sistemas (neste exemplo, configurado para as documentações públicas do Streamlit e FastAPI).

## 🚀 Arquitetura e Tecnologias

O projeto foi construído focando em resiliência, isolamento de contexto e precisão nas respostas:

- **Frontend:** [Streamlit](https://streamlit.io/) para uma interface de chat interativa e amigável.
- **Orquestração de Agentes:** [Agno (Phidata)](https://github.com/agno-agi/agno) para gerenciar o fluxo lógico da IA, prompts e ferramentas.
- **Modelos de Linguagem (LLM):** Google Gemini (gemini-2.5-flash), atuando tanto na geração de respostas quanto na vetorização de textos (Embeddings).
- **Web Scraping:** [Firecrawl](https://www.firecrawl.dev/) para extrair e processar dinamicamente o conteúdo das páginas de documentação.
- **Banco de Dados Vetorial:** ChromaDB (local) para armazenamento semântico persistente e buscas em alta velocidade.
- **Memória de Sessão:** SQLite para manter o histórico conversacional de forma consistente.

## ✨ Principais Funcionalidades

- **Múltiplos Contextos Isolados:** O agente consegue transitar entre diferentes "Sistemas" (ex: Alpha e Beta), criando bancos vetoriais isolados para cada um, impedindo que regras de uma documentação se misturem com a outra.
- **Prevenção de Alucinação:** O prompt do sistema é rigoroso em instruir a IA a não inventar procedimentos ou menus não documentados, encorajando respostas que esclarecem limitações do sistema.
- **Desambiguação Inteligente:** Caso a dúvida do usuário seja vaga (ex: "Não consigo acessar"), o agente formula automaticamente opções numeradas para guiar o atendimento antes de entregar a resposta definitiva.
- **Resiliência e Retentativas Automáticas:** O frontend possui mecanismos de backoff e etry para cenários de queda de API (erros 503 Service Unavailable ou 429 Too Many Requests), garantindo uma experiência estável.

## 💻 Como rodar o projeto localmente

### Pré-requisitos
- Python 3.12+
- Gerenciador de pacotes uv (opcional, mas recomendado)
- Chaves de API do Google Gemini e Firecrawl.

### Instalação

1. Clone o repositório:
`ash
git clone https://github.com/FabioFreire-GitH/agente-suporte-publico.git
cd agente-suporte-publico
`

2. Crie as variáveis de ambiente:
Copie o arquivo de exemplo e insira suas credenciais:
`ash
cp .env.example .env
`

3. Instale as dependências:
`ash
uv sync
# ou via pip: pip install -r requirements.txt
`

4. Execute a aplicação web:
`ash
uv run streamlit run app.py
`
A aplicação abrirá no seu navegador no endereço http://localhost:8501.

---

> *Este projeto faz parte do meu portfólio de estudos e transição de carreira para a área de Tecnologia, com foco em desenvolvimento em Python, IA e orquestração de Agentes.*
