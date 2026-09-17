import sys
import pathlib

# Adiciona o diretório 'src' ao sys.path para permitir execução direta do script
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from agente_suporte.agente import criar_agente_suporte


def main():
    # 1. Defina as URLs do sistema Sistema Alpha
    urls_alpha = [
        "https://docs.streamlit.io/",
        "https://docs.streamlit.io/get-started",
        "https://docs.streamlit.io/develop/api-reference",
        "https://docs.streamlit.io/develop/concepts",
    ]
    
    # 2. Defina as URLs do sistema Sistema Beta (quando for testar)
    urls_beta = [
        "https://fastapi.tiangolo.com/",
        "https://fastapi.tiangolo.com/tutorial/",
        "https://fastapi.tiangolo.com/advanced/",
    ]

    # 3. Cria (ou carrega) o agente do Sistema Alpha
    agente_sistema_alpha = criar_agente_suporte(
        nome_sistema="sistema_alpha", 
        urls_documentacao=urls_alpha, 
        recriar_banco=False, 
        modo_teste=True
    )  # modo_teste=True desabilita histórico entre perguntas
    
    # 4. Cria (ou carrega) o agente do Sistema Beta
    agente_sistema_beta = criar_agente_suporte(
        nome_sistema="sistema_beta", 
        urls_documentacao=urls_beta, 
        recriar_banco=False, 
        modo_teste=True
    )

    # ──────────────────────────────────────────────────────────────────
    # Bateria de Testes Genérica
    # ──────────────────────────────────────────────────────────────────
    print("\n--- Testando Agente Sistema Alpha (Streamlit) ---\n")
    agente_sistema_alpha.print_response("O que é o Streamlit?")
    agente_sistema_alpha.print_response("Como eu crio um botão?")
    agente_sistema_alpha.print_response("Como faço o deploy de uma aplicação no Streamlit Community Cloud?")
    
    print("\n--- Testando Agente Sistema Beta (FastAPI) ---\n")
    # agente_sistema_beta.print_response("O que é o FastAPI e quais suas vantagens?")
    # agente_sistema_beta.print_response("Como crio uma rota de POST?")

if __name__ == "__main__":
    main()
