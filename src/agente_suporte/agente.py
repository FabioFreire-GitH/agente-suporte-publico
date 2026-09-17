import os
import shutil 
from dotenv import load_dotenv
import pathlib
import time

from agno.agent import Agent
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.firecrawl_reader import FirecrawlReader
from agno.knowledge.chunking.recursive import RecursiveChunking
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.vectordb.chroma import ChromaDb

load_dotenv()

def criar_agente_suporte(nome_sistema: str, urls_documentacao: list, recriar_banco: bool = False, modo_teste: bool = False) -> Agent:
    """
    Cria um agente isolado para um sistema específico.
    Se recriar_banco for True, ele apaga a pasta física do banco e baixa tudo do zero.
    """

    BASE_DIR = pathlib.Path(__file__).parent.parent.parent

    caminho_sqlite = str(BASE_DIR / "tmp" / f"chat_{nome_sistema}.db")
    caminho_chroma = str(BASE_DIR / "tmp" / f"chroma_{nome_sistema}")
    nome_colecao = f"docs_{nome_sistema}"

    # 1. Limpeza Física Brutal (Se solicitado)
    if recriar_banco and os.path.exists(caminho_chroma):
        print(f"🧹 [{nome_sistema.upper()}] Deletando a pasta física do banco antigo...")
        shutil.rmtree(caminho_chroma, ignore_errors=True)
    
    # 2. Banco de memória específico do sistema
    db = SqliteDb(db_file=caminho_sqlite)

    # 3. Vector DB (Agora ele recria a pasta sozinho se a gente deletou)
    vector_db = ChromaDb(
        collection=nome_colecao,
        path=caminho_chroma, 
        embedder=GeminiEmbedder(api_key=os.getenv("GOOGLE_API_KEY")),
        persistent_client=True,
    )

    # 4. Leitor web
    firecrawl_reader = FirecrawlReader(
        api_key=os.getenv("FIRECRAWL_API_KEY"),
        mode="scrape",
        chunking_strategy=RecursiveChunking(
            chunk_size=1500,
            overlap=200,
        ),
    )

    knowledge = Knowledge(vector_db=vector_db, max_results=10)

    # 5. Checagem do tamanho do banco
    tamanho_banco = 0
    try:
        tamanho_banco = vector_db.get_count()
    except Exception:
        pass

    # 6. Lógica de Inserção Real
    if tamanho_banco == 0 or recriar_banco:
        print(f"🤖 [{nome_sistema.upper()}] Iniciando a leitura e vetorização do manual...")
        for url in urls_documentacao:
            print(f"📥 [{nome_sistema.upper()}] Baixando: {url}")
            try:
                # knowledge.insert gerencia internamente o chunking e os IDs únicos por chunk
                knowledge.insert(url=url, reader=firecrawl_reader, upsert=True)
                print(f"✅ Inserido no banco de dados!")
            except Exception as e:
                print(f"❌ Erro ao processar {url}: {e}")
            
            time.sleep(3)
                
        print(f"📊 [{nome_sistema.upper()}] Sucesso! Total de pedaços salvos: {vector_db.get_count()}")
    else:
        print(f"🚀 [{nome_sistema.upper()}] Banco já contém {tamanho_banco} blocos de texto! Carregando agente...")

    # 7. Construção do Agente
    instrucoes = f"""Você é um assistente de suporte técnico especializado no sistema {nome_sistema.upper()}.
    ## Seu Papel
    Você auxilia usuários gerais e desenvolvedores que utilizam o {nome_sistema.upper()}.

    ## Regras de Comportamento

    ### 1. Antes de responder, identifique a intenção
    Se a pergunta for vaga ou ambígua (por exemplo: "não lembro minha senha", "como faço para acessar"), 
    NÃO tente adivinhar. Em vez disso, apresente de 2 a 4 possibilidades objetivas e pergunte 
    qual delas representa o problema do usuário. Use o formato:
    "Sua dúvida pode ser sobre:
    1️⃣ [opção A]
    2️⃣ [opção B]
    3️⃣ [opção C]
    Qual dessas opções melhor descreve sua situação? Ou se nenhuma delas se aplica, me conte com mais detalhes."

    ### 2. Responda sempre com base na documentação
    Use APENAS as informações presentes na documentação do {nome_sistema.upper()} que foi fornecida.
    Nunca invente procedimentos, telas, campos ou funcionalidades que não estejam descritos.
    Se o usuário perguntar como realizar uma ação ou alteração que o sistema não permite 
    (por exemplo: alterar o e-mail de login, editar um campo bloqueado ou realizar uma ação exclusiva de outro perfil), 
    responda diretamente que o sistema não permite essa ação e explique o motivo conforme a documentação. NUNCA diga 
    que a informação não consta na documentação quando o manual explica que a ação é restrita ou bloqueada.

    ### 3. Quando a informação não estiver na documentação
    Se após analisar a pergunta com clareza a resposta não constar na documentação, diga:
    "Essa informação específica não está detalhada na documentação do {nome_sistema.upper()} que tenho acesso.
    Recomendo entrar em contato diretamente com o suporte do {nome_sistema.upper()} para obter orientação precisa."
    Nunca complemente com suposições ou conhecimento externo.

    ### 4. Formato das respostas
    - Seja direto e objetivo.
    - Use listas numeradas ou com marcadores quando houver passos ou opções.
    - Evite respostas muito longas. Se o procedimento for extenso, divida em etapas claras.
    - Use linguagem simples, acessível para usuários não técnicos.

    ### 5. Tom
    Seja cordial, paciente e profissional. O usuário pode estar frustrado com um problema técnico."""

    if modo_teste:
        print(f"🧪 [{nome_sistema.upper()}] Modo teste ativo: histórico de conversa desabilitado.")

    agente = Agent(
        name=f"suporte_{nome_sistema}",
        model=Gemini(id="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY")),
        instructions=instrucoes,
        db=db,
        add_history_to_context=not modo_teste,
        enable_user_memories=not modo_teste,
        knowledge=knowledge,
        search_knowledge=True,
        tool_call_limit=2,
        num_history_runs=0 if modo_teste else 2,
        max_tool_calls_from_history=0,
    )

    return agente