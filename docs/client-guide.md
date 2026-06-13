# ProspectPilot — Kurulum Rehberi

_Bu rehber, ProspectPilot'u bilgisayarına kurmak ve çalıştırmak için gereken adımları içerir._

---

## Gereksinimler

- Windows 10 veya üzeri
- İnternet bağlantısı
- Aşağıdaki servisler için API key'ler (sağlanacak veya kendin açacaksın)

---

## Bölüm 1 — Python Kurulumu

1. `python.org/downloads` adresine git
2. **Download Python 3.12.x** butonuna tıkla
3. İndirilen dosyayı çalıştır
4. Kurulum ekranında **"Add Python to PATH"** kutusunu işaretle — bu adım kritik
5. **Install Now** butonuna bas, kurulum tamamlansın
6. Kurulumu doğrula — Windows arama çubuğuna `cmd` yaz, aç, şunu yaz:
   ```
   python --version
   ```
   `Python 3.12.x` gibi bir çıktı görmelisin

---

## Bölüm 2 — VS Code Kurulumu

1. `code.visualstudio.com` adresine git
2. **Download for Windows** butonuna tıkla, kur
3. VS Code'u aç
4. Sol çubukta blok ikon (Extensions) → arama kutusuna `Python` yaz
5. Microsoft tarafından olan **Python** eklentisini yükle

---

## Bölüm 3 — Projeyi Al

### GitHub'dan (önerilen)

Komut istemcisini aç (Windows arama → `cmd`) ve şunu çalıştır:

```
git clone https://github.com/kullanici-adi/prospectpilot.git
cd prospectpilot
```

### ZIP olarak

1. GitHub sayfasında **Code → Download ZIP**
2. ZIP'i istediğin klasöre çıkart
3. VS Code'da `File → Open Folder` ile o klasörü aç

---

## Bölüm 4 — Paketleri Yükle

VS Code'da terminal aç (`Ctrl + `` ` ``) ve şu iki komutu sırayla çalıştır:

```powershell
python -m venv venv
.\venv\Scripts\python -m pip install -r requirements.txt
```

İkinci komut birkaç dakika sürebilir — paketler yüklenirken bekle.

---

## Bölüm 5 — .env Dosyasını Doldur

1. Proje klasöründe `.env.example` dosyasını bul
2. Kopyala, adını `.env` yap
3. VS Code'da `.env` dosyasını aç ve şu alanları doldur:

```
ANTHROPIC_API_KEY=buraya-anthropic-key-ini-yaz
TAVILY_API_KEY=buraya-tavily-key-ini-yaz
HUNTER_API_KEY=buraya-hunter-key-ini-yaz
SENDGRID_API_KEY=buraya-sendgrid-key-ini-yaz

FROM_EMAIL=gonderici@kendi-domain.com
REPLY_TO_EMAIL=kisisel@gmail.com

SENDER_NAME=Adın Soyadın
SENDER_ROLE=Unvanın
SERVICE_OFFERED=Ne sunduğunu tek cümleyle yaz
```

> API key'leri nereden alacağını bilmiyorsan geliştirici ile iletişime geç.

---

## Bölüm 6 — Uygulamayı Başlat

VS Code terminalinde şunu çalıştır:

```powershell
.\venv\Scripts\streamlit run app.py
```

Tarayıcı otomatik açılır ve uygulama yüklenir.
İlk açılışta email adresi sorarsa **Enter** ile geç.

Bir sonraki kullanımda da aynı komutu çalıştırmak yeterli.

---

## Sorun Giderme

**"python komut bulunamadı" hatası:**
Python kurulumunda "Add Python to PATH" işaretlenmemiş. Python'u kaldırıp tekrar kur, bu sefer işareti koy.

**"Module not found" hatası:**
```powershell
.\venv\Scripts\python -m pip install -r requirements.txt
```
komutunu tekrar çalıştır.

**Tarayıcı açılmadı:**
Tarayıcını aç, adres çubuğuna `localhost:8501` yaz.

**Başka bir sorunla karşılaştıysan:**
Hata mesajının ekran görüntüsünü al ve geliştirici ile paylaş.

---

_ProspectPilot — AI-Powered Outreach Automation_
