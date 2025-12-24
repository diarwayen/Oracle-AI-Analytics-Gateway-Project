import oracledb
import os
from dotenv import load_dotenv

load_dotenv()

def extract_schema():
    print("--- 🔍 Genişletilmiş Veritabanı Taraması Başlıyor ---")
    
    try:
        connection = oracledb.connect(
            user=os.getenv("ORACLE_USER"),
            password=os.getenv("ORACLE_PASSWORD"),
            dsn=os.getenv("ORACLE_DSN")
        )
        cursor = connection.cursor()

        # 1. TABLOLARI VE KOLONLARI ÇEK (ALL_TAB_COLUMNS)
        # Sadece bizim kullanıcının değil, yetkisi olan tüm tabloları çeker.
        # SYS ve SYSTEM gibi Oracle'ın kendi tablolarını filtreliyoruz.
        print("\n⏳ Tüm erişilebilir tablolar taranıyor...")
        
        cols_sql = """
            SELECT owner, table_name, column_name, data_type
            FROM all_tab_columns
            WHERE owner NOT IN (
                'SYS', 'SYSTEM', 'OUTLN', 'DBSNMP', 'APPQOSSYS', 'GSMADMIN_INTERNAL', 
                'XDB', 'WMSYS', 'CTXSYS', 'ORDDATA', 'ORDSYS', 'MDSYS', 'OLAPSYS'
            )
            ORDER BY owner, table_name, column_id
        """
        cursor.execute(cols_sql)
        columns = cursor.fetchall()

        # 2. İLİŞKİLERİ ÇEK (ALL_CONS_COLUMNS)
        print("⏳ İlişkiler (Foreign Keys) analiz ediliyor...")
        relations_sql = """
            SELECT 
                a.owner,
                a.table_name, 
                a.column_name, 
                c_pk.table_name as r_table_name, 
                c.constraint_type
            FROM all_cons_columns a
            JOIN all_constraints c 
                ON a.owner = c.owner 
                AND a.constraint_name = c.constraint_name
            LEFT JOIN all_constraints c_pk 
                ON c.r_owner = c_pk.owner 
                AND c.r_constraint_name = c_pk.constraint_name
            WHERE c.constraint_type IN ('P', 'R')
            AND a.owner NOT IN ('SYS', 'SYSTEM') 
        """
        cursor.execute(relations_sql)
        relations = cursor.fetchall()

        # İlişkileri haritala
        rel_map = {}
        for r in relations:
            # r[0]: Owner, r[1]: Table, r[2]: Column
            key = f"{r[0]}.{r[1]}.{r[2]}"
            if r[4] == 'P':
                rel_map[key] = "🔑 (PK)"
            elif r[4] == 'R' and r[3]:
                rel_map[key] = f"🔗 (FK -> {r[3]})"

        print("\n" + "="*60)
        print("VERİTABANI HARİTASI (ŞEMA SAHİBİNE GÖRE)")
        print("="*60)

        current_table = ""
        current_owner = ""
        table_count = 0

        for col in columns:
            owner = col[0]
            table_name = col[1]
            col_name = col[2]
            data_type = col[3]

            # Yeni tabloya geçiş kontrolü
            full_table_name = f"{owner}.{table_name}"
            
            if full_table_name != current_table:
                if current_table != "": print("-" * 40)
                print(f"\n📂 ŞEMA: {owner} | TABLO: {table_name}")
                current_table = full_table_name
                table_count += 1
            
            # İlişki kontrolü
            key = f"{owner}.{table_name}.{col_name}"
            extra_info = rel_map.get(key, "")
            
            print(f"   - {col_name:<25} {data_type:<15} {extra_info}")

        print("\n" + "="*60)
        print(f"✅ Tarama Bitti. Toplam {table_count} tablo bulundu.")
        print("="*60)

        cursor.close()
        connection.close()

    except Exception as e:
        print(f"\n❌ HATA: {str(e)}")

if __name__ == "__main__":
    extract_schema()