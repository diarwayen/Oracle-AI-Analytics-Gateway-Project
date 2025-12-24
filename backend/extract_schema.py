import oracledb
import os
from dotenv import load_dotenv

# .env yükle
load_dotenv()

def extract_schema():
    print("--- 🔍 Veritabanı Şeması Analiz Ediliyor ---")
    
    try:
        # Bağlan
        connection = oracledb.connect(
            user=os.getenv("ORACLE_USER"),
            password=os.getenv("ORACLE_PASSWORD"),
            dsn=os.getenv("ORACLE_DSN")
        )
        cursor = connection.cursor()

        # 1. TABLOLARI VE KOLONLARI ÇEK
        # Sadece senin kullanıcına ait tabloları getirir
        print("\n⏳ Tablolar ve Sütunlar okunuyor...")
        cols_sql = """
            SELECT table_name, column_name, data_type
            FROM user_tab_columns
            ORDER BY table_name, column_id
        """
        cursor.execute(cols_sql)
        columns = cursor.fetchall()

        # 2. İLİŞKİLERİ (BAĞLANTILARI) ÇEK
        # Hangi tablo hangisine bağlı? (Primary Key / Foreign Key)
        print("⏳ İlişkiler (Foreign Keys) analiz ediliyor...")
        relations_sql = """
            SELECT 
                a.table_name, 
                a.column_name, 
                c_pk.table_name as r_table_name, 
                c.constraint_type
            FROM user_cons_columns a
            JOIN user_constraints c ON a.owner = c.owner AND a.constraint_name = c.constraint_name
            LEFT JOIN user_constraints c_pk ON c.r_owner = c_pk.owner AND c.r_constraint_name = c_pk.constraint_name
            WHERE c.constraint_type IN ('P', 'R')
        """
        cursor.execute(relations_sql)
        relations = cursor.fetchall()

        # --- SONUÇLARI BİRLEŞTİR VE YAZDIR ---
        
        # İlişkileri sözlüğe çevir (Hızlı erişim için)
        rel_map = {}
        for r in relations:
            # r[0]: Tablo, r[1]: Kolon, r[2]: Hedef Tablo, r[3]: Tip (P/R)
            key = f"{r[0]}.{r[1]}"
            if r[3] == 'P':
                rel_map[key] = "🔑 (Primary Key)"
            elif r[3] == 'R' and r[2]:
                rel_map[key] = f"🔗 (Foreign Key -> {r[2]} tablosuna gider)"

        print("\n" + "="*50)
        print("VERİTABANI HARİTASI")
        print("="*50)

        current_table = ""
        table_count = 0

        for col in columns:
            table_name = col[0]
            col_name = col[1]
            data_type = col[2]

            # Yeni tabloya geçince başlık at
            if table_name != current_table:
                if current_table != "": print("-" * 30) # Önceki tablo bitti
                print(f"\n📂 TABLO: {table_name}")
                current_table = table_name
                table_count += 1
            
            # Kolon detayını yaz
            extra_info = rel_map.get(f"{table_name}.{col_name}", "")
            print(f"   - {col_name:<20} {data_type:<15} {extra_info}")

        print("\n" + "="*50)
        print(f"✅ Analiz Tamamlandı. Toplam {table_count} tablo bulundu.")
        print("="*50)

        cursor.close()
        connection.close()

    except Exception as e:
        print(f"\n❌ HATA OLUŞTU: {str(e)}")

if __name__ == "__main__":
    extract_schema()