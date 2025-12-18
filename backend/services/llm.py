from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.config import settings

# 1. Model Tanımı (Tek seferlik kurulum)

llm_model = ChatOllama(
    model=settings.LLM_MODEL,      # Örn: "mistral"
    base_url=settings.OLLAMA_URL,  # Örn: "http://ollama:11434"
    format="json",
    temperature=0,
)

# 2. Parser
parser = JsonOutputParser()

# 3. Prompt Şablonu

prompt_template = ChatPromptTemplate.from_template("""
Sen bir Oracle SQL uzmanısın.
Şema:
{schema}

Soru:
{question}

Kurallar:
1. Sadece SELECT sorguları üret, asla INSERT/UPDATE/DELETE/ALTER/DROP yazma.
2. Sadece şemada verilen tablo ve kolonları kullan.
3. Her sorgunun sonuna güvenlik için 'FETCH FIRST 100 ROWS ONLY' ekle (uygunsa).
4. Tarih alanları için Oracle uyumlu ifadeler kullan (ör: SYSDATE - 30).
5. CEVABIN SADECE GEÇERLİ BİR JSON OLSUN.
6. JSON anahtarları: "sql", "aciklama".
7. JSON dışında hiçbir metin üretme.
""")


# 4. Zincir (Chain) Oluşturma (Modern LCEL Syntax)
# Prompt -> Model -> Parser

sql_chain = prompt_template | llm_model | parser

def generate_sql_from_text(user_question: str):
    try:
        # Zinciri çalıştır
        result = sql_chain.invoke({
            "schema": settings.TABLE_SCHEMA,
            "question": user_question
        })
        return result # Direkt Python Dictionary döner {"sql": "...", "aciklama": "..."}
    except Exception as e:
        print(f"LangChain Hatası: {e}")
        return None