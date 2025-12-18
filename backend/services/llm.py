try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # Model başlatılıyor (Zincir değil, sadece model)
        print(f"--- LLM Modeli Başlatılıyor: {settings.LLM_MODEL} ---")
        self.llm = ChatOllama(
            model=settings.LLM_MODEL,
            base_url="http://ollama:11434",
            format="json",
            temperature=0,
        )

    def get_sql(self, user_question: str, schema_info: str):
        """
        Zincir (Chain) burada kuruluyor ve çalıştırılıyor.
        """
        try:
            # 1. Prompt
            template = """
            Sen bir veritabanı uzmanısın. Aşağıdaki şemaya göre Oracle SQL sorgusu yaz.
            Sadece JSON formatında cevap ver.
            
            Şema Bilgisi:
            {schema}
            
            Kullanıcı Sorusu:
            {question}
            
            Cevap Formatı:
            {{
                "sql": "SELECT ...",
                "explanation": "..."
            }}
            """
            
            prompt = ChatPromptTemplate.from_template(template)
            
            # 2. Parser
            parser = JsonOutputParser()
            
            # 3. ZİNCİR KURULUMU (Senin istediğin LangChain yapısı burada)
            chain = prompt | self.llm | parser
            
            # 4. Çalıştırma
            response = chain.invoke({
                "schema": schema_info, 
                "question": user_question
            })
            
            return response

        except Exception as e:
            logger.error(f"LLM Hatası: {str(e)}")
            # Hata dönerse sistem çökmesin, hata mesajı dönsün
            return {"sql": "ERROR", "explanation": str(e)}

# Router'ların kullanacağı hazır nesne
llm_service = LLMService()