# ProspectPilot — Kurulum Rehberi

_Bu rehber, ProspectPilot'u sıfırdan kurma adımlarını kapsar._
_Müşteriye teslimde ilgili bölümler kesilerek verilebilir._

---

## Gereksinimler

Başlamadan önce şunlar gerekli:

- Python 3.10 veya üzeri
- VS Code (veya başka bir kod editörü)
- Bir alan adı (SendGrid için — örn. cesastudio.com)
- Aşağıdaki servislerde hesap (ücretsiz planlar yeterli)

---

## Bölüm 1 — Python ve VS Code Kurulumu

### Python

1. `python.org/downloads` adresine git
2. En güncel sürümü indir ve kur
3. Kurulum sırasında **"Add Python to PATH"** kutusunu işaretle — kritik
4. Kurulum bitti mi kontrol et:
   ```powershell
   python --version
   # → Python 3.12.x gibi bir şey çıkmalı
   ```

### VS Code

1. `code.visualstudio.com` adresine git, indir ve kur
2. VS Code'u aç → Sol çubukta **Extensions** (Ctrl+Shift+X)
3. Şu eklentiyi yükle: **Python** (Microsoft tarafından)

---

## Bölüm 2 — Projeyi Alma

### GitHub'dan clone (önerilen)

```powershell
git clone https://github.com/CESA-tech/prospectpilot.git
cd prospectpilot
```

### Ya da manuel

1. GitHub'dan ZIP olarak indir
2. İstediğin bir klasöre çıkart
3. VS Code'da `File → Open Folder` ile aç

---

## Bölüm 3 — Virtual Environment ve Paketler

Virtual environment (venv), projenin ihtiyaç duyduğu paketleri izole tutar. Farklı projeler birbirini etkilemez.

```powershell
# Proje klasöründeyken çalıştır

# 1. venv oluştur
python -m venv venv

# 2. Tüm paketleri yükle
.\venv\Scripts\python -m pip install -r requirements.txt
```

Yükleme bitince `venv/` klasörü oluşmuş olmalı.

---

## Bölüm 4 — API Hesapları ve Key'ler

Her servis için hesap aç, key'i kopyala, bir yere not et. Hepsini sonra `.env` dosyasına yazacaksın.

### 4.1 Anthropic (Claude AI)

1. `console.anthropic.com` → hesap aç
2. Sol menüden **API Keys** → **Create Key**
3. Key'i kopyala → `sk-ant-...` ile başlar

### 4.2 Tavily (Web Araştırma)

1. `app.tavily.com` → hesap aç
2. Dashboard'da API key görünür → kopyala
3. Ücretsiz planda aylık 1000 arama hakkı var

### 4.3 Hunter.io (Email Bulma)

1. `hunter.io` → hesap aç
2. Sağ üst köşe → profil → **API** → key'i kopyala
3. Ücretsiz planda aylık 25 arama hakkı var

### 4.4 SendGrid (Email Gönderme)

1. `sendgrid.com` → hesap aç (60 gün trial, sonra ücretsiz 100 email/gün)
2. Sol menü → **Settings → API Keys → Create API Key**
3. **Full Access** seç → **Create & View**
4. Key'i kopyala → `SG.` ile başlar — **bir daha gösterilmez, şimdi kopyala**

### 4.5 Gmail (Kişisel)

Mevcut Gmail hesabın yeterli. Yeni hesap açmana gerek yok.
Sadece adresi not et — `REPLY_TO_EMAIL` için kullanılacak.

---

## Bölüm 5 — .env Dosyasını Doldur

Proje kökünde `.env.example` dosyası var. Bunu kopyalayıp `.env` adıyla kaydet:

```powershell
Copy-Item .env.example .env
```

Sonra VS Code'da `.env` dosyasını aç ve doldur:

```env
ANTHROPIC_API_KEY=sk-ant-...buraya-kendi-key-in...
TAVILY_API_KEY=tvly-...buraya-kendi-key-in...
HUNTER_API_KEY=...buraya-kendi-key-in...
SENDGRID_API_KEY=SG....buraya-kendi-key-in...

FROM_EMAIL=outreach@kendi-domain.com
REPLY_TO_EMAIL=kisisel@gmail.com

SENDER_NAME=Adın Soyadın
SENDER_ROLE=Unvanın (örn. AI Automation Consultant)
SERVICE_OFFERED=Ne sunduğunu tek cümleyle yaz
```

**Önemli:** `.env` dosyası asla GitHub'a yüklenmez — içinde gizli key'ler var.

---

## Bölüm 6 — SendGrid DNS Kurulumu

Email'lerin spam'e düşmemesi için alan adına DNS kayıtları eklenmesi gerekiyor.
Bu işlem **bir kez** yapılır.

### Adım 1 — SendGrid'de Domain Doğrulama

1. SendGrid → **Settings → Sender Authentication**
2. **Authenticate Your Domain** → **Get Started**
3. Domain registrar olarak **GoDaddy** seç (veya kullandığın provider)
4. Alan adını gir (örn. `cesastudio.com`)
5. SendGrid sana **5 DNS kaydı** verir — bunları bir sonraki adımda ekleyeceksin

### Adım 2 — GoDaddy'de DNS Kayıtları Ekle

1. `godaddy.com` → hesabına giriş → **My Products**
2. Alan adının yanındaki **DNS** butonuna tıkla
3. SendGrid'in verdiği her kayıt için **Add New Record** yap:

**3 adet CNAME kaydı:**
| Type | Host | Value |
|------|------|-------|
| CNAME | em1234 | u1234567.wl.sendgrid.net |
| CNAME | s1._domainkey | s1.domainkey.u1234567.wl.sendgrid.net |
| CNAME | s2._domainkey | s2.domainkey.u1234567.wl.sendgrid.net |

**1 adet TXT kaydı:**
| Type | Host | Value |
|------|------|-------|
| TXT | _dmarc | v=DMARC1; p=none; |

> **Dikkat:** Host alanına sadece prefix yaz (`em1234`), tam domain değil.
> TTL varsayılan bırakılır.

### Adım 3 — Doğrulamayı Tamamla

1. SendGrid'e dön → **Verify**
2. DNS yayılması 5-30 dakika sürebilir
3. Yeşil tik görünce hazır

---

## Bölüm 7 — Gmail API Kurulumu (Reply Detection)

Gönderilen emaillere cevap gelip gelmediğini kontrol etmek için Gmail API gerekli.
Bu işlem de **bir kez** yapılır.

### Adım 1 — Google Cloud Projesi Oluştur

1. `console.cloud.google.com` → Google hesabınla giriş yap
2. Üst çubukta proje seçici → **New Project**
3. Proje adı: `ProspectPilot` → **Create**

### Adım 2 — Gmail API'yi Aktive Et

1. Sol menü → **APIs & Services → Library**
2. Arama kutusuna `Gmail API` yaz
3. **Gmail API** → **Enable**

### Adım 3 — OAuth Consent Screen

1. Sol menü → **APIs & Services → OAuth consent screen**
2. User Type: **External** → **Create**
3. Doldur:
   - App name: `ProspectPilot`
   - User support email: kendi Gmail adresin
   - Developer contact: kendi Gmail adresin
4. **Save and Continue**
5. **Scopes** adımında → **Add or Remove Scopes**
6. Listeden `gmail.readonly` seç → **Update**
7. **Save and Continue**
8. **Test Users** adımında → **Add Users** → kendi Gmail adresini ekle
9. **Save and Continue** → **Back to Dashboard**

### Adım 4 — OAuth Credentials Oluştur

1. Sol menü → **APIs & Services → Credentials**
2. **Create Credentials → OAuth client ID**
3. Application type: **Desktop app**
4. Name: `ProspectPilot Desktop`
5. **Create**
6. Çıkan pencerede **Download JSON** → dosyayı indir
7. İndirilen dosyayı proje köküne koy, adını `credentials.json` yap

### Adım 5 — İlk Bağlantıyı Test Et

```powershell
.\venv\Scripts\python src\tools\reply_detector.py
```

Tarayıcı açılır → Google hesabına giriş yap → izin ver.
`Bağlantı başarılı!` yazarsa kurulum tamamdır. `token.pickle` dosyası oluşur — bir daha izin sormaz.

---

## Bölüm 8 — Uygulamayı Çalıştır

### Streamlit Arayüzü (Önerilen)

```powershell
.\venv\Scripts\streamlit run app.py
```

Tarayıcıda `localhost:8501` otomatik açılır. İlk açılışta email sorarsa Enter ile geç.

### Terminal Menüsü

```powershell
.\venv\Scripts\python main.py
```

---

## Bölüm 9 — İlk Test

1. Streamlit'te **Yeni Lead** sekmesine git
2. Bir şirket adı yaz (örn. `Linear`)
3. **Araştır** butonuna bas — 30-60 saniye sürer
4. Domain'i onayla → kişi seç → draft incele → **Taslak Kaydet**
5. **Leads** sekmesinde lead'in göründüğünü doğrula

---

## Sorun Giderme

**"Module not found" hatası:**
```powershell
.\venv\Scripts\python -m pip install -r requirements.txt
```

**SendGrid email gitmiyor:**
- DNS kayıtlarının doğrulandığından emin ol (SendGrid → Sender Authentication → yeşil tik)
- `FROM_EMAIL` değerinin doğrulanmış domain'den olduğunu kontrol et

**Gmail API "Access denied" hatası:**
- Google Cloud Console → OAuth consent screen → Test Users → kendi adresin ekli mi kontrol et
- `token.pickle` dosyasını sil, tekrar çalıştır → yeni izin akışı başlar

**Hunter.io kişi bulunamadı:**
- Büyük şirketlerde (Google, Meta vb.) veri indexlenmemiş olabilir — bu Hunter.io sınırlaması
- Daha küçük B2B SaaS şirketlerinde çalışır

---

_Son güncelleme: 2026-06-13_
