# ProspectPilot — Proje Günlüğü

_Bu dosya her geliştirme oturumunda güncellenir. Ne bitti, nerede kaldık, ne sırada._

---

## Mevcut Durum

**Hafta:** Hafta 3 tamamlandı → Hafta 4 başlıyor  
**Son oturum:** 2026-06-13  
**Aktif görev:** GitHub + README + Loom demo

### Tamamlananlar
- [x] İlan analizi yapıldı (Upwork: AI Agent Developer - Outreach & Lead Generation)
- [x] Proje kararlaştırıldı: ProspectPilot
- [x] 4 haftalık roadmap tasarlandı
- [x] Stack kararları alındı
- [x] Klasör yapısı belirlendi
- [x] outreach-automation-developer ajanı oluşturuldu
- [x] Notlar ve dökümanlar hazırlandı
- [x] `requirements.txt` ve `.env.example` oluşturuldu
- [x] Virtual environment kuruldu, paketler yüklendi
- [x] `src/agents/research_agent.py` — çalışıyor, domain otomatik buluyor
- [x] `src/agents/draft_agent.py` — kişiye özel email yazıyor, stil sistemi var
- [x] `src/tools/enrichment.py` — Hunter.io kişi seçimi çalışıyor
- [x] `src/tools/email_sender.py` — SendGrid entegrasyonu çalışıyor
- [x] `src/db/models.py` + `crud.py` — SQLite kayıt sistemi çalışıyor
- [x] `src/pipeline/run_pipeline.py` — uçtan uca pipeline çalışıyor
- [x] `main.py` — tek giriş noktası
- [x] `config/outreach_styles.json` — kayıt edilebilir stil sistemi
- [x] SendGrid DNS kurulumu yapıldı (GoDaddy), email teslimi test edildi

### Tamamlananlar (devam)
- [x] `src/tools/follow_up.py` — cevap kontrolü + follow-up taslağı + onay menüsü
- [x] `src/scheduler.py` — APScheduler, her gün 09:00'da otomatik çalışır
- [x] `src/db/viewer.py` — sent_at, follow_up_count, replied işaretle, sil
- [x] İstatistikler + sıfırlama (viewer + main.py)
- [x] Config centralize — SENDER_NAME/ROLE/SERVICE .env'e taşındı
- [x] `.env.example` güncellendi
- [x] `app.py` — Streamlit UI (5 sekme: Yeni Lead, Toplu İşle, Dashboard, Leads, Follow-ups)
- [x] DB şeması güncellendi — sent_at, follow_up_count, last_follow_up_at

### Sıradaki Adım
**Hafta 4 — Delivery:**
1. GitHub repository + README (İngilizce, Upwork'e yönelik)
2. Loom demo videosu

---

## Oturum Günlüğü

### 2026-06-11 — İlan Analizi ve Proje Planlaması
**Ne yapıldı:**
- Upwork ilanı analiz edildi: "AI Agent Developer - Outreach & Lead Generation Automation"
- İlan: $3,000 fixed-price, Miami/ABD client, 50+ proposal var
- ProspectPilot projesi kararlaştırıldı
- 4 haftalık roadmap tasarlandı (sonradan delivery katmanı eklenerek 4. hafta eklendi)
- Stack kararları: Claude + LangGraph + Hunter.io + Tavily + Airtable + SendGrid
- Klasör yapısı ve ajan ekibi kuruldu

**Alınan kararlar:**
- Hafta 1-2: Saf Python (LangGraph öğrenmeden önce agent mantığını kavra)
- Hafta 3: LangGraph'a geç (refactor)
- Airtable → onay UI, SQLite → asıl database
- LangGraph öncesi Claude tool use ile başla

**Öğrenilen / dikkat edilecekler:**
- İlandaki "Adobe Illustrator" mandatory skill tamamen yanlış etiket — Upwork'te bu tür hatalar oluyor
- Human-in-the-loop bu iş tipinde standart — tam otonom istemiyorlar
- 50+ proposal var ama çoğu "n8n kullanırım" seviyesinde — AI agent + research kısmı fark yaratır

---

## Stack Kararları (Değişirse Buraya Yaz)

| Karar | Seçim | Alternatif | Neden bu |
|-------|-------|------------|---------|
| LLM | claude-sonnet-4-6 | GPT-4o | İlan Claude'u da belirtiyor, tool use güçlü |
| Agent framework | LangGraph | CrewAI, AutoGen | En yaygın, Upwork'te tanınan |
| Web search | Tavily | Serper, SerpAPI | Ücretsiz tier yeterli, LangGraph uyumlu |
| Enrichment | Hunter.io | Clearbit, Apollo | Ücretsiz 25/ay MVP için yeterli |
| Database | SQLite | PostgreSQL, Supabase | Sıfır setup, local development |
| Onay UI | Airtable | Custom web UI, Notion | Hızlı, görsel, sıfır frontend kodu |
| Email delivery | SendGrid | Mailgun, SES | Ücretsiz 100/gün, iyi dokümantasyon |
| Scheduling | APScheduler | n8n, Celery | Python içi, basit |
| Reply detection | Gmail API | IMAP, SendGrid webhooks | Ücretsiz, güvenilir |

---

## Bilinen Sorunlar / Riskler

- Hunter.io ücretsiz tier 25 arama/ay — demo için yeterli ama production'da ücretli plan gerekir
- Gmail API kurulumu biraz karmaşık (OAuth2) — dikkatli ilerle
- LangGraph'a geçiş (Hafta 3) refactor gerektirir — Hafta 1-2 kodunu temiz yaz
- LinkedIn scraping ToS ihlali riski — bu projede LinkedIn'den direkt scraping yok, sadece web search

---

### 2026-06-12 — Streamlit UI + Follow-up + Config İyileştirmeleri

**Ne yapıldı:**
- Follow-up sequence yazıldı (`src/tools/follow_up.py`)
  - Cevap kontrolü (Gmail API), 3/7 gün takip, stil menüsü + anlık düzenleme
- APScheduler eklendi (`src/scheduler.py`) — her gün 09:00'da otomatik çalışır
- DB şeması güncellendi: `sent_at`, `follow_up_count`, `last_follow_up_at`
- `crud.py`: `update_status` artık "sent" olunca `sent_at` kaydediyor, `increment_follow_up` eklendi
- Viewer iyileştirmeleri: `sent_at`, `follow_up_count` görünüyor, replied işaretle + sil eklendi
- İstatistikler + sıfırlama menüsü eklendi
- Config centralize: `SENDER_NAME`, `SENDER_ROLE`, `SERVICE_OFFERED` → `.env`
- `.env.example` güncellendi
- Streamlit `app.py` yazıldı — 5 sekme:
  - Yeni Lead: tam interaktif pipeline (araştır → domain → kişi → draft → gönder)
  - Toplu İşle: CSV yükle, pipeline otomatik çalışır
  - Dashboard: istatistikler, sıfırlama
  - Leads: lead yönetimi (onayla, sil, replied)
  - Follow-ups: cevap kontrolü + takip emailler

**Alınan kararlar:**
- Airtable yerine Streamlit — kendi arayüzümüzü yazdık, üçüncü partiye bağımlı değil
- LangGraph terminal/batch için kalıyor, Streamlit interaktif pipeline için session_state kullanıyor
- "şaşırtıcı" test stili silindi

### 2026-06-12 — Gmail API Kurulumu + Follow-up Hazırlığı

**Ne yapıldı:**
- `email_sender.py`'e Reply-To eklendi (kişisel Gmail → cevaplar oraya gelir)
- Google Cloud Console'da ProspectPilot projesi açıldı
- Gmail API enable edildi
- OAuth consent screen ayarlandı (External, gmail.readonly scope, test user)
- OAuth credentials JSON indirildi → `credentials.json` olarak proje köküne konuldu
- `src/tools/reply_detector.py` yazıldı
- Google API paketleri yüklendi
- `.env`'e `REPLY_TO_EMAIL` eklendi

**Yarım kalan:**
- `reply_detector.py` henüz test edilmedi (tarayıcı OAuth flow)
- Follow-up sequence yazılmadı
- APScheduler yazılmadı
- Airtable yazılmadı

**Sıradaki adım:**
1. `.\venv\Scripts\python src\tools\reply_detector.py` → Gmail bağlantısını test et
2. Follow-up sequence yaz
3. APScheduler ekle
4. Airtable
5. GitHub + README

---

### 2026-06-12 — LangGraph Refactor + Pipeline İyileştirmeleri

**Ne yapıldı:**
- `src/pipeline/graph.py` yazıldı — LangGraph StateGraph ile pipeline
- Conditional routing: domain yoksa enrichment atlanır
- Retry mekanizması: research 2 kez dener, başarısız olursa durur
- CSV batch processing: `data/leads.csv`'den toplu işlem
- `resume_lead()`: kayıtlı draft'ı yükleyip approval'dan devam ettirir
- Üstüne yaz / yeni draft seçeneği eklendi
- Approval menüsüne [Y] Yeni stil oluştur eklendi
- Viewer menüsü netleştirildi: "detay gör, düzenle, gönder"
- Duplicate stil (merak uyandırıcı) kaldırıldı

**Alınan kararlar:**
- Airtable ertelendi — terminal onayı şimdilik yeterli
- `run_pipeline.py` artık kullanılmıyor, `graph.py` ana pipeline

---

### 2026-06-11 — Hafta 2 Tamamlandı: Pipeline Uçtan Uca Çalışıyor

**Ne yapıldı:**
- `draft_agent.py` yazıldı — kişiye özel email, stil sistemi, anlık düzenleme
- `enrichment.py` yazıldı — Hunter.io domain search, departman + kişi seçimi
- `email_sender.py` yazıldı — SendGrid entegrasyonu
- SQLite database kuruldu (SQLAlchemy ile, Supabase'e geçiş kolay)
- `run_pipeline.py` tüm adımları birleştiriyor
- `main.py` tek giriş noktası oldu
- SendGrid DNS kurulumu GoDaddy'de yapıldı
- Kendi adresine test emaili başarıyla gönderildi

**Alınan kararlar:**
- Airtable şimdilik ertelendi — terminal onayı yeterli, LangGraph sonrası eklenecek
- FROM_EMAIL olarak mevcut domain adresi kullanılıyor (ayrı adres açmaya gerek yok)

**Öğrenilen:**
- DNS kayıtları (CNAME, TXT, DKIM, DMARC, SPF) — learning-notes.md'ye eklendi
- SendGrid gmail/outlook değil, API servisi

---

### 2026-06-11 — Research Agent Kurulum ve Test

**Ne yapıldı:**
- Virtual environment kuruldu (`venv/`)
- `requirements.txt` paketleri yüklendi (anthropic, tavily-python, python-dotenv, requests)
- `research_agent.py` test edildi — Notion araştırması başarıyla çalıştı
- JSON parse bug'ı düzeltildi (Claude bazen JSON öncesine açıklama metni ekliyor, regex ile çözüldü)

**Alınan kararlar:**
- LLM çıktısını parse ederken her zaman `re.search(r'\{.*\}', text, re.DOTALL)` kullan — markdown fence ve açıklama metni güvenli şekilde atlanır

**Öğrenilen:**
- Parse etmek, agentic loop, venv — learning-notes.md'ye eklendi

---

_Son güncelleme: 2026-06-11_
