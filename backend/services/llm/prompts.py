def build_system_prompt(schema: str) -> str:
    return f"""Sen uzman bir Oracle SQL veritabanı yöneticisisin.

VERİTABANI ŞEMASI:
{schema}

KURALLAR:
1. Sadece JSON formatında cevap ver: {{"sql": "SELECT...", "explanation": "..."}}
2. 'SELECT TOP 1' KULLANMA. Oracle bunu desteklemez.
3. 'LIMIT' KULLANMA.
4. Satır sınırlamak için SONA 'FETCH FIRST 1 ROWS ONLY' ekle.

DOĞRU ÖRNEK:
SELECT urun_adi, fiyat FROM urunler ORDER BY fiyat DESC FETCH FIRST 1 ROWS ONLY

YANLIŞ ÖRNEK (BUNLARI YAPMA):
SELECT TOP 1 urun_adi... (YANLIŞ)
SELECT urun_adi... LIMIT 1 (YANLIŞ)
"""


from typing import Optional


def build_user_content(question: str, error: Optional[str]) -> str:
    content = f"Soru: {question}"
    if error:
        content += f"\n\nÖnceki SQL hatalıydı: {error}. Lütfen Oracle 21c syntax'ına uygun düzelt."
    return content

