import oracledb
import os
from dotenv import load_dotenv
import sys

# .env dosyasını yükle
load_dotenv()

def test_connection():
    print("--- 🔌 Veritabanı Bağlantı Testi Başlıyor ---")

    # Değişkenleri al
    user = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    dsn = os.getenv("ORACLE_DSN")
    lib_dir = os.getenv("ORACLE_LIB_DIR") # Eğer Client Library gerekiyorsa

    # Eksik bilgi kontrolü
    if not all([user, password, dsn]):
        print("❌ HATA: .env dosyasında eksik bilgiler var!")
        print(f"   User: {user}, DSN: {dsn}")
        return

    print(f"📡 Hedef: {user} @ {dsn}")
    
    try:
        # Eğer Thin mod yetmezse ve Thick mod gerekirse lib_dir kullanılır
        # oracledb.init_oracle_client(lib_dir=lib_dir) 

        # Bağlantıyı dene
        connection = oracledb.connect(
            user=user,
            password=password,
            dsn=dsn
        )
        
        # Basit bir sorgu at
        cursor = connection.cursor()
        cursor.execute("SELECT 'Bağlantı Başarılı! Veritabanı Tarihi: ' || TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') FROM DUAL")
        result = cursor.fetchone()
        
        print(f"✅ {result[0]}")
        print("--- Test Başarıyla Tamamlandı ---")

        cursor.close()
        connection.close()

    except oracledb.Error as e:
        error_obj, = e.args
        print("\n❌ BAĞLANTI HATASI:")
        print(f"   Hata Kodu: {error_obj.code}")
        print(f"   Mesaj: {error_obj.message}")
        print("\nOlası Sebepler:")
        if error_obj.code == 1017:
            print("   -> Kullanıcı adı veya şifre yanlış.")
        elif error_obj.code == 12541:
            print("   -> Hedef adreste Listener (Dinleyici) yok veya port yanlış.")
        elif error_obj.code == 12170:
            print("   -> Zaman aşımı (Timeout). VPN kapalı olabilir veya Firewall engelliyor.")
        elif error_obj.code == 12514:
            print("   -> Servis adı (DSN'deki /sonrası) yanlış.")
            
    except Exception as e:
        print(f"❌ Beklenmeyen Hata: {str(e)}")

if __name__ == "__main__":
    test_connection()