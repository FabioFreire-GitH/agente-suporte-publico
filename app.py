import sys
import os
import time

# Adiciona o diretório 'src' ao path do Python para encontrar o pacote 'agente_suporte'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

import streamlit as st
from agente_suporte.agente import criar_agente_suporte

# ─────────────────────────────────────────────
# Configuração da página
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Agente de Suporte",
    page_icon="🤖",
    layout="centered",
)

# ─────────────────────────────────────────────
# URLs de cada sistema (edite aqui para adicionar páginas)
# ─────────────────────────────────────────────
URLS_ALPHA = [
    "https://docs.streamlit.io/",
    "https://docs.streamlit.io/get-started",
    "https://docs.streamlit.io/develop/api-reference",
    "https://docs.streamlit.io/develop/concepts",
]

URLS_BETA = [
    "https://fastapi.tiangolo.com/",
    "https://fastapi.tiangolo.com/tutorial/",
    "https://fastapi.tiangolo.com/advanced/",
]

# ─────────────────────────────────────────────
# Cache: carrega os agentes apenas uma vez
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner="⏳ Carregando agente Sistema Alpha...")
def carregar_agente_sistema_alpha():
    return criar_agente_suporte(
        nome_sistema="sistema_alpha",
        urls_documentacao=URLS_ALPHA,
        recriar_banco=False,  # Mude para True para forçar atualização do banco
    )

@st.cache_resource(show_spinner="⏳ Carregando agente Sistema Beta...")
def carregar_agente_sistema_beta():
    return criar_agente_suporte(
        nome_sistema="sistema_beta",
        urls_documentacao=URLS_BETA,
        recriar_banco=False,  # Mude para True para forçar atualização do banco
    )

# ─────────────────────────────────────────────
# Sidebar: seleção do sistema
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Agente de Suporte")
    st.divider()

    sistema = st.selectbox(
        "Selecione o sistema:",
        options=["Sistema Alpha", "Sistema Beta"],
        index=0,
    )

    st.divider()
    if st.button("🗑️ Limpar conversa", use_container_width=True):
        st.session_state.historico = []
        st.rerun()

    st.caption("Os agentes respondem com base na documentação oficial de cada sistema.")

# ─────────────────────────────────────────────
# Carrega o agente do sistema selecionado
# ─────────────────────────────────────────────
if sistema == "Sistema Alpha":
    agente = carregar_agente_sistema_alpha()
else:
    agente = carregar_agente_sistema_beta()

# ─────────────────────────────────────────────
# Estado da sessão: histórico de mensagens
# ─────────────────────────────────────────────
if "historico" not in st.session_state:
    st.session_state.historico = []

# Limpa o histórico ao trocar de sistema
if "sistema_atual" not in st.session_state:
    st.session_state.sistema_atual = sistema

if st.session_state.sistema_atual != sistema:
    st.session_state.historico = []
    st.session_state.sistema_atual = sistema

# ─────────────────────────────────────────────
# Cabeçalho principal
# ─────────────────────────────────────────────
st.title(f"Suporte {sistema}")
st.caption(f"Tire suas dúvidas sobre o sistema **{sistema}**. As respostas são baseadas na documentação oficial.")

# ─────────────────────────────────────────────
# Exibe histórico de mensagens
# ─────────────────────────────────────────────
for msg in st.session_state.historico:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─────────────────────────────────────────────
# Input do usuário
# ─────────────────────────────────────────────
pergunta = st.chat_input(f"Pergunte algo sobre o {sistema}...")

if pergunta:
    # Exibe a mensagem do usuário
    st.session_state.historico.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    # Chama o agente e exibe a resposta com retry automático e resiliência
    with st.chat_message("assistant"):
        texto_resposta = None
        sucesso = False
        erro_str = ""

        MAX_TENTATIVAS = 3
        ESPERA_BASE = 3  # segundos

        with st.spinner("Consultando a documentação..."):
            for tentativa in range(1, MAX_TENTATIVAS + 1):
                try:
                    resposta = agente.run(pergunta)
                    texto_resposta = resposta.content

                    # Detecção do erro capturado internamente pelo Agno
                    eh_erro_agno = (
                        (hasattr(resposta, "status") and str(resposta.status).lower().endswith("error"))
                        or (isinstance(texto_resposta, str) and ('"code": 400' in texto_resposta or '"code": 503' in texto_resposta or '"error":' in texto_resposta))
                    )
                    if eh_erro_agno:
                        raise Exception(texto_resposta or "Erro retornado pelo provedor de IA")

                    sucesso = True
                    break
                except Exception as e:
                    erro_str = str(e)
                    eh_503 = (
                        "503" in erro_str
                        or "service unavailable" in erro_str.lower()
                        or "overloaded" in erro_str.lower()
                        or "unavailable" in erro_str.lower()
                    )
                    eh_400_turn = (
                        "400" in erro_str
                        and ("function call turn" in erro_str.lower() or "invalid_argument" in erro_str.lower())
                    )

                    # Se o histórico de mensagens do agente ficou corrompido, limpa a sessão atual
                    if eh_400_turn:
                        try:
                            if hasattr(agente, "session_id") and agente.session_id:
                                agente.delete_session(session_id=agente.session_id)
                        except Exception:
                            pass
                        # Tenta uma vez mais imediatamente após limpar a sessão corrompida
                        try:
                            resposta = agente.run(pergunta)
                            texto_resposta = resposta.content
                            if not (isinstance(texto_resposta, str) and '"error":' in texto_resposta):
                                sucesso = True
                                break
                        except Exception as e2:
                            erro_str = str(e2)

                    # Se for 503 (serviço ocupado), aguarda e tenta novamente
                    if eh_503 and tentativa < MAX_TENTATIVAS:
                        espera = ESPERA_BASE * tentativa
                        st.toast(f"⏳ Conexão instável. Nova tentativa em {espera}s... ({tentativa}/{MAX_TENTATIVAS})")
                        time.sleep(espera)
                        continue

                    # Demais erros ou tentativas esgotadas
                    break

        if sucesso and texto_resposta:
            st.markdown(texto_resposta)
            st.session_state.historico.append({"role": "assistant", "content": texto_resposta})
        else:
            if "503" in erro_str or "service unavailable" in erro_str.lower() or "overloaded" in erro_str.lower() or "unavailable" in erro_str.lower():
                mensagem_erro = (
                    "⚠️ **Os servidores de inteligência estão temporariamente sobrecarregados (Erro 503).**\n\n"
                    "Tentamos reconectar automaticamente, mas o serviço ainda não respondeu. "
                    "Por favor, aguarde alguns instantes e tente novamente."
                )
            elif "429" in erro_str or "quota" in erro_str.lower() or "limit" in erro_str.lower():
                mensagem_erro = (
                    "⚠️ **Limite temporário de requisições atingido (Erro 429).**\n\n"
                    "O serviço está processando muitas perguntas no momento. Por favor, tente novamente em instantes."
                )
            else:
                mensagem_erro = (
                    "⚠️ **Não foi possível responder a sua pergunta neste momento.**\n\n"
                    "Ocorreu uma instabilidade na comunicação. Por favor, tente enviar sua pergunta novamente."
                )
            st.warning(mensagem_erro)
