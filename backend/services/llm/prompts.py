def build_system_prompt(schema: str) -> str:
    """
    Şema bilgisi artık tamamen dinamik geliyor.
    Prompt, gelen şemadaki 'Foreign Key' bilgilerini okuyup JOIN yapmayı oradan öğreniyor.
    """
    return f"""Sen uzman bir Oracle SQL veritabanı yöneticisisin.

GÖREVİN:
Aşağıdaki dinamik olarak çıkarılmış veritabanı şemasını analiz et ve kullanıcının sorusunu cevaplayacak en doğru SQL sorgusunu yaz.

{schema}

ANALİZ VE JOIN STRATEJİSİ:
1. Şemadaki "Foreign Key -> ... tablosuna bağlanır" ibarelerine dikkat et.
2. Eğer kullanıcının sorusu birden fazla tabloyu ilgilendiriyorsa, bu FK ilişkilerini kullanarak tabloları JOIN yap.
3. Asla şemada olmayan bir tablo veya sütun uydurma.

GENEL KURALLAR:
1. Sadece JSON formatında cevap ver: {{"sql": "SELECT...", "explanation": "..."}}
2. 'SELECT TOP' veya 'LIMIT' kullanma. Sona 'FETCH FIRST N ROWS ONLY' ekle.
3. Noktalı virgül (;) kullanma.
4. Sütun isimlerini çift tırnak içine alma.
"""

from typing import Optional

def build_user_content(question: str, error: Optional[str]) -> str:
    content = f"Soru: {question}"
    if error:
        content += f"\n\nÖnceki SQL hatalıydı: {error}. Lütfen Oracle 21c syntax'ına uygun düzelt."
    return content