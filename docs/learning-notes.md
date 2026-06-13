# ProspectPilot — Öğrenme Notları

_Bu dosya proje boyunca öğrenilen kavramları ders notu formatında tutar._
_outreach-automation-developer ajanı geliştirme yaparken buraya başvurur ve yeni kavramlar öğrenildikçe günceller._

---

## 1. Outreach Automation Nedir?

Satış ekiplerinin manuel yaptığı 4 işi otomatize etmek:

1. **Prospect research** — "Bu şirket ne yapar, büyüyor mu, doğru kişi kim?"
2. **Lead enrichment** — "Bu kişinin email adresi ne, LinkedIn profili hangisi?"
3. **Personalized outreach** — "Bu kişiye özgü, jenerik olmayan mesaj yaz"
4. **Follow-up** — "Cevap gelmedi, 3 gün sonra tekrar dene"

Bu 4 adımın tamamını bir AI agent sistemi yapıyor. İnsan sadece onaylıyor.

---

## 2. AI Agent Nedir? (ReAct Pattern)

Bir LLM'e sadece soru sorup cevap almak değil — araç kullanmasını sağlamak.

**ReAct döngüsü:**
```
Düşün (Reasoning) → Araç kullan (Action) → Sonucu gözlemle (Observation) → Tekrar düşün
```

**Örnek:**
```
Görev: "Acme Corp hakkında araştırma yap"

Düşün: "Önce şirketi web'de aramalıyım"
Araç: web_search("Acme Corp company overview 2026")
Gözlemle: "SaaS şirketi, 50 çalışan, son 6 ayda %30 büyüme"

Düşün: "Şimdi CEO'yu aramalıyım"
Araç: web_search("Acme Corp CEO LinkedIn")
Gözlemle: "CEO: Jane Smith"

Düşün: "Yeterli bilgi var, özet çıkarayım"
Cevap: {company: "Acme Corp", size: "50 employees", growth: "30%", ceo: "Jane Smith"}
```

Bu döngüyü Claude'un `tool_use` özelliği ile kuruyoruz.

---

## 3. Claude Tool Use (Function Calling)

Claude'a "şu araçları kullanabilirsin" diyoruz, o da gerektiğinde çağırıyor.

**Temel yapı:**
```python
import anthropic

client = anthropic.Anthropic()

# Araçları tanımla
tools = [
    {
        "name": "web_search",
        "description": "Web'de arama yapar, sonuçları döner",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Arama sorgusu"}
            },
            "required": ["query"]
        }
    }
]

# İlk mesajı gönder
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    tools=tools,
    messages=[{"role": "user", "content": "Acme Corp hakkında araştırma yap"}]
)

# Claude araç çağırdıysa
if response.stop_reason == "tool_use":
    tool_call = response.content[-1]  # tool_use block
    # tool_call.name → "web_search"
    # tool_call.input → {"query": "Acme Corp company overview"}
    
    # Aracı gerçekten çalıştır
    result = web_search(tool_call.input["query"])
    
    # Sonucu Claude'a geri ver
    # ... döngü devam eder
```

**Kritik nokta:** Claude aracı "çağırmaz" — aslında "şu aracı çağır" diye sinyal verir. Sen çalıştırıp sonucu geri gönderiyorsun.

---

## 4. LangGraph — Agent State Machine

LangGraph, multi-step agent workflow'larını **state machine** olarak modeller.

**Neden gerekli?**
- Saf Python döngüsü büyüdükçe karmaşıklaşır
- LangGraph: her adımı node, geçişleri edge olarak tanımla → temiz mimari

**Temel kavramlar:**
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# 1. State tanımla — pipeline boyunca taşınan veri
class ProspectState(TypedDict):
    company_name: str
    research_summary: str
    email: str
    draft: str
    approved: bool

# 2. Node'ları yaz — her adım bir fonksiyon
def research_node(state: ProspectState) -> ProspectState:
    # web araştırması yap
    return {"research_summary": "..."}

def enrich_node(state: ProspectState) -> ProspectState:
    # email bul
    return {"email": "jane@acme.com"}

def draft_node(state: ProspectState) -> ProspectState:
    # email taslağı yaz
    return {"draft": "Hi Jane..."}

# 3. Graph kur
graph = StateGraph(ProspectState)
graph.add_node("research", research_node)
graph.add_node("enrich", enrich_node)
graph.add_node("draft", draft_node)

graph.set_entry_point("research")
graph.add_edge("research", "enrich")
graph.add_edge("enrich", "draft")
graph.add_edge("draft", END)

app = graph.compile()
```

**Human-in-the-loop:**
```python
# Node'dan önce insan onayı iste
graph.add_edge("draft", "human_approval")
# interrupt_before=["human_approval"] ile derlence, burada durur
app = graph.compile(interrupt_before=["human_approval"])
```

---

## 5. Lead Enrichment

Ham veri (şirket adı, kişi adı) → zenginleştirilmiş veri (email, unvan, LinkedIn).

**Hunter.io API:**
```python
import requests

def find_email(first_name: str, last_name: str, domain: str) -> str:
    response = requests.get(
        "https://api.hunter.io/v2/email-finder",
        params={
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": HUNTER_API_KEY
        }
    )
    data = response.json()
    return data["data"]["email"]  # "jane@acme.com"
```

**Alternatifler:**
- Clearbit (daha kapsamlı ama pahalı)
- Apollo.io (hem enrichment hem outreach tool)
- Proxycurl (LinkedIn verisi, ücretli)

---

## 6. Email Delivery (SendGrid)

Onaylanan emaili gerçekten göndermek.

```python
import sendgrid
from sendgrid.helpers.mail import Mail

def send_email(to_email: str, subject: str, body: str):
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    message = Mail(
        from_email="outreach@yourdomain.com",
        to_emails=to_email,
        subject=subject,
        plain_text_content=body
    )
    sg.send(message)
```

**Deliverability kritik kavramlar:**
- **SPF/DKIM/DMARC:** Domain'in email gönderme yetkisini kanıtlayan DNS kayıtları
- **Warm-up:** Yeni domain'den yavaş başla, spam'e düşme
- **Bounce handling:** Geçersiz email adreslerini kaydet, tekrar deneme

---

## 7. Human-in-the-Loop Pattern

Sistemin her şeyi otomatik yapmaması — kritik noktalarda insan kararı beklemesi.

**Bu projede nerede kullanılıyor:**
1. Email taslağı yazıldıktan sonra → insan onaylar/düzenler
2. Follow-up taslağı yazıldıktan sonra → insan onaylar

**Airtable ile implementasyon:**
- Agent taslağı Airtable'a "Pending" status ile kaydeder
- İnsan Airtable'da görür, düzenler, "Approved" yapar
- Agent periyodik olarak "Approved" kayıtları çeker ve gönderir

**LangGraph ile implementasyon:**
- `interrupt_before=["send_node"]` — send node'undan önce dur
- Kullanıcı terminal'de onay verir
- `app.invoke(None, config)` ile devam et

---

## 8. Outreach Automation Katmanları

| Katman | Ne | Araç |
|--------|----|----|
| 1. Veri | Lead bulma, enrichment | Hunter.io, Tavily, Apollo |
| 2. AI/Agent | Araştırma, kişiselleştirme, taslak | Claude, LangGraph |
| 3. Delivery | Gönderme, reply detection, follow-up | SendGrid, Gmail API |
| 4. Deliverability | SPF/DKIM, warm-up, bounce | Domain ayarları, outreach tool |

ProspectPilot katman 1-3'ü kapsar. Katman 4 outreach tool'lara (Instantly.ai, Lemlist) devredilir.

---

## 9. Parse Etmek Nedir?

**Parse = ham metni okuyup anlamlı yapıya (veri) dönüştürmek.**

Bir API'den veya LLM'den gelen cevap başlangıçta sadece bir **string** (metin). Python bu metni `"company"` anahtarına erişebileceğin bir nesne olarak görmez — önce parse edilmesi gerekir.

**JSON parse örneği:**
```python
import json

# Bu bir string — Python için sadece metin
raw = '{"company": "Notion", "summary": "A productivity tool"}'

# json.loads() parse eder → Python dict'ine çevirir
data = json.loads(raw)

print(data["company"])   # → "Notion"
print(data["summary"])   # → "A productivity tool"
```

**Neden hata çıktı? — Markdown code fence problemi**

Claude bazen JSON cevabını markdown kod bloğu içinde döndürür:

```
```json
{"company": "Notion", ...}
```
```

`json.loads()` ilk karaktere bakınca `` ` `` gördü, "bu JSON değil" dedi ve hata fırlattı.

**Fix — önce temizle, sonra parse et:**
```python
text = block.text.strip()

if text.startswith("```"):
    text = text.split("```")[1]   # ortadaki kısmı al
    if text.startswith("json"):
        text = text[4:]           # "json" kelimesini at
    text = text.strip()

data = json.loads(text)           # artık güvenle parse edilir
```

**Kural:** LLM'den JSON bekliyorsan, her zaman markdown temizliği yap. Claude prompt'ta "ONLY JSON, no markdown" dese bile bazen sarmalar.

---

## 10. Agentic Loop — Nasıl Çalışır?

`research_agent.py`'deki döngünün adım adım açıklaması:

```
1. Claude'a mesaj gönder
2. Claude cevap verdi — stop_reason nedir?

   → "tool_use":  Claude bir araç çağırmak istiyor
       - Aracı gerçekten çalıştır (web_search)
       - Sonucu Claude'a geri gönder
       - 1'e dön

   → "end_turn":  Claude işini bitirdi, son cevabı verdi
       - text block'u al
       - parse et → döndür
```

**Kod karşılığı:**
```python
while True:
    response = client.messages.create(...)

    if response.stop_reason == "tool_use":
        # aracı çalıştır, sonucu geri ver
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
        # döngü devam eder

    elif response.stop_reason == "end_turn":
        # bitti, JSON'u parse edip döndür
        return json.loads(text)
```

**Notion örneğinde 6 arama yaptı:**
- `web_search(Notion company overview 2024...)`
- `web_search(Notion recent news...)`
- `web_search(Notion tech stack...)`
- vs.

Her arama bir döngü turu. Claude "yeterli bilgi var" diyene kadar devam etti.

---

## 11. Virtual Environment (venv)

**Problem:** Farklı projeler farklı paket versiyonlarına ihtiyaç duyar. Global Python'a her şeyi yüklersen çakışma olur.

**Çözüm:** Her proje için izole bir Python ortamı — venv.

```powershell
# Oluştur
python -m venv venv

# Aktive et (Windows)
.\venv\Scripts\activate

# Paketleri yükle (artık sadece bu projeye gider)
pip install -r requirements.txt

# Deaktive et
deactivate
```

**Pratikte:** `.\venv\Scripts\python script.py` ile direkt de çalıştırabilirsin — aktive etmene gerek yok.

---

## 12. Database Seçimi — Hangi Durumda Ne Kullanılır?

### SQLite
- Tek bir `.db` dosyası, sunucu gerekmez, kurulum yok
- **Ne zaman:** Local geliştirme, demo, tek kullanıcı, portfolio projesi
- **Ne zaman değil:** Birden fazla kullanıcı aynı anda yazıyorsa, uzaktan erişim gerekiyorsa
- Bu projede: Hafta 1-2 geliştirme ve GitHub demo için

### PostgreSQL
- Güçlü, production-grade ilişkisel veritabanı
- **Ne zaman:** Kendi sunucun var, karmaşık sorgular yazıyorsun, multi-user production
- **Ne zaman değil:** Hızlı prototip — kurulum ve yönetim efor ister
- Alternatif: Railway, Render, Heroku üzerinde hosted PostgreSQL

### Supabase
- PostgreSQL + hazır REST API + authentication + realtime + dashboard
- **Ne zaman:** Hızlı production, web arayüzü gerekiyor, teknik olmayan ekip veriye bakacak
- **Ne zaman değil:** Basit local script — fazla overhead
- Bu projede: Gerçek client tesliminde SQLite → Supabase geçişi yapılır

### MongoDB
- JSON benzeri dökümanlar saklar, şema zorunlu değil
- **Ne zaman:** Verinin yapısı değişken (her kayıt farklı alanlar içerebilir), hızlı iterasyon
- **Ne zaman değil:** İlişkisel veri (kullanıcı → sipariş → ürün gibi join'ler gerekiyorsa)

### Redis
- In-memory (RAM'de) anahtar-değer store
- **Ne zaman:** Cache (sık okunan veriyi hızlı sun), iş kuyruğu, oturum yönetimi
- **Ne zaman değil:** Kalıcı ana veri tabanı olarak — RAM dolunca veri kaybolabilir

### Airtable
- Görsel tablo arayüzü, API ile okunabilir
- **Ne zaman:** Teknik olmayan kullanıcı veriyi görecek/düzenleyecek, hızlı prototip
- Bu projede: Human approval UI olarak kullanılacak (Hafta 2-3)

### Geçiş Stratejisi (Bu Proje)
SQLAlchemy ORM kullanarak veritabanı katmanını soyutluyoruz. Böylece:
```python
# Sadece şu satırı değiştirmek yeterli:
DATABASE_URL = "sqlite:///data/prospectpilot.db"   # şimdi
DATABASE_URL = "postgresql://..."                   # production'da
```
Kod değişmez, sadece bağlantı adresi değişir.

---

## 13. SendGrid — Email Gönderimi

Ham email taslağı yazdık ama hiçbir yere gitmiyor. SendGrid bunu çözüyor — onaylanan emaili gerçekten alıcının inbox'ına gönderiyor.

**Gmail / Outlook'tan farkı:**
- Gmail/Outlook → sen emaillerini okuduğun platform, inbox var
- SendGrid → uygulama içinden otomatik email göndermek için API servisi, inbox yok
- "Şifrenizi sıfırlayın", "Siparişiniz onaylandı" gibi otomatik emailler hep böyle servislerden çıkar

**Kurulum adımları (bir kez yapılır):**

1. `sendgrid.com`'dan hesap aç (60 gün trial, sonra free plan — otomatik para çekmez)
2. **Domain doğrulaması:** SendGrid 4 DNS kaydı verir, bunları GoDaddy'ye eklersin:
   - 3x CNAME kaydı (email yönlendirme + DKIM imzası)
   - 1x TXT kaydı (DMARC politikası)
   - GoDaddy'de: alan adı sahibi olduğun hesaba giriş → DNS → Add New Record
   - Host alanına sadece prefix yaz (`em5987`), tam domain değil (`em5987.cesastudio.com` değil)
   - TTL varsayılan bırakılır
3. SendGrid'de **Settings → API Keys → Create API Key** → Full Access → kopyala
4. `.env`'e ekle:
   ```
   SENDGRID_API_KEY=SG.xxxx
   FROM_EMAIL=outreach@kendi-domain.com
   ```

**Test stratejisi — kendi domainini kullan:**
Kendi domainini araştırır, kendine email gönderirsin. 3. kişi dahil değil, tam pipeline test edilmiş olur.

**Kod:**
```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(to_email: str, subject: str, body: str) -> bool:
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    return response.status_code in (200, 202)
```

**Dikkat edilecekler:**
- Free plan: günde 100 email
- DNS yayılması 5-30 dakika sürer, SendGrid verify etmeden gönderilemez
- `FROM_EMAIL` SendGrid'de doğruladığın domain'den olmalı
- Bounce olan adresleri kaydet, tekrar deneme

**DNS kavramları:**
- **CNAME:** Bir domain adını başka bir adrese yönlendirir
- **TXT:** Domain hakkında metin bilgisi saklar (SPF, DMARC doğrulaması için)
- **DKIM:** Emailin gerçekten o domain'den geldiğini kriptografik olarak imzalar
- **DMARC:** "Bu domain'den sahte email gelirse ne yapılsın?" politikası
- **SPF:** Hangi sunucuların bu domain adına email gönderebileceğini tanımlar
- Bunlar olmadan email spam klasörüne düşer

---

## 14. CSV Input — Toplu Şirket İşleme

Tek tek şirket girmek yerine `leads.csv` dosyasına şirket listesi yazıp hepsini sırayla işlemek.

```csv
company,domain
Linear,linear.app
Notion,notion.so
Stripe,stripe.com
```

```python
import csv

with open("data/leads.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        run(row["company"], row["domain"])
```

**Ne işe yarar:** 50 şirketi tek seferde araştırıp taslak yazabilirsin. Gece bırakırsın, sabah hazır.

---

## 15. LangGraph — n8n Değil, Python Kütüphanesi

**n8n ile karıştırma:** n8n görsel, sürükle-bırak, kod yazmıyorsun. LangGraph ise Python kütüphanesi — sen kod yazıyorsun, müşteri kullanmıyor.

**Ne fark yaratır:**
Şu an pipeline düz sıralı fonksiyonlar:
```python
research() → enrich() → draft() → send()
```

LangGraph'ta aynı pipeline "graph" olarak modelleniyor:
```python
graph.add_node("research", research_fn)
graph.add_node("draft", draft_fn)
graph.add_node("send", send_fn)
graph.add_edge("research", "draft")
graph.add_edge("draft", "send")
```

**Neden değerli:**
- Dallanma kolaylaşır: "onay gelmezse geri dön", "hata olursa farklı yola git"
- Human-in-the-loop: `interrupt_before=["send"]` ile send node'undan önce dur, insan onaylasın
- Upwork ilanlarında "LangGraph biliyor musun?" sık soruluyor

**Özet:** Sen LangGraph ile otomasyon **geliştiriyorsun**, müşteri sonucu kullanıyor.

---

## 16. Gmail API — Reply Detection

Email gönderdik ama cevap geldi mi bilmiyoruz. Gmail API ile inbox'ı kontrol edip "bu kişi cevap verdi mi?" diye bakıyoruz.

**Reply-To stratejisi:**
- Emailler SendGrid ile `cesa@cesastudio.com`'dan gönderilir (profesyonel görünür)
- `Reply-To: kisisel@gmail.com` header'ı eklenir — alıcı görmez
- Karşı taraf "Reply" basınca cevap kişisel Gmail'e gelir
- Gmail API kişisel Gmail'i izler — kurumsal hesap OAuth karmaşasına gerek yok

**Kurulum adımları (bir kez yapılır):**
1. Google Cloud Console → yeni proje (ProspectPilot)
2. APIs & Services → Gmail API → Enable
3. OAuth consent screen → External, app name, support email, gmail.readonly scope, test user ekle
4. Credentials → OAuth client ID → Desktop app → JSON indir → `credentials.json` olarak proje köküne koy
5. `pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client`
6. İlk çalıştırmada tarayıcı açılır, izin verilir → `token.pickle` oluşur (bir daha sormaz)

**Önemli:** Google Cloud 2FA zorunlu (Mart 2026'dan itibaren). Kişisel hesapta "No organization" seçilir.

**Nasıl çalışır:**
```python
def check_reply(to_email: str, subject: str) -> bool:
    service = get_gmail_service()
    # Alıcının emailinden gelen mesajları ara
    query = f"from:{to_email}"
    messages = service.users().messages().list(userId="me", q=query).execute()
    # Subject eşleşmesi kontrol et (Re: prefix'i temizleyerek)
    # Eşleşme varsa True döner
```

**token.pickle:** OAuth token'ı saklar. Süresi dolunca otomatik yeniler. Silersen tekrar tarayıcı açılır.

---

## 17. Follow-up Sequence + APScheduler

Email attık, sessizlik var. Otomatik takip sistemi:

| Gün | Aksiyon |
|-----|---------|
| 0 | İlk email gönderildi |
| 3 | Cevap yok → Follow-up 1 yazılır, onaya düşer |
| 7 | Hâlâ yok → Follow-up 2 |
| 10 | Yok → "No Response" olarak kapatılır |

**APScheduler:** Python içinde çalışan zamanlayıcı. "Her gün sabah 09:00'da şunu çalıştır" diyebiliyorsun — sunucu veya cron job gerekmez.

```python
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

@scheduler.scheduled_job('cron', hour=9)
def daily_check():
    check_replies_and_queue_followups()

scheduler.start()
```

---

## 18. LangGraph — Detaylı Kullanım

LangGraph'ın temel kavramları ve bu projede nasıl kullandığımız:

### State
Tüm pipeline boyunca taşınan veri. Her node okur, günceller, bir sonrakine bırakır.
```python
class ProspectState(TypedDict):
    company_name: str
    domain: str
    research: Optional[dict]
    contact: Optional[dict]
    draft: Optional[dict]
    approved: bool
    sent: bool
    error: Optional[str]      # hata varsa buraya yaz
    retry_count: int           # kaç kez denendi
```

### Node
Bir iş yapan fonksiyon. State'i alır, güncellediği alanları dict olarak döner.
```python
def research_node(state: ProspectState) -> dict:
    research = research_company(state["company_name"])
    return {"research": research, "domain": research["domain"]}
```

### Edge — Düz bağlantı
```python
graph.add_edge("enrich", "draft")  # enrich bittikten sonra her zaman draft
```

### Conditional Edge — Koşullu yönlendirme
Routing fonksiyonu hangi node'a gidileceğine karar verir:
```python
def after_research(state) -> str:
    if state.get("error"):          # hata var mı?
        if state["retry_count"] < 2:
            return "research"       # tekrar dene
        return END                  # vazgeç
    return "enrich" if state["domain"] else "draft"  # domain varsa enrich, yoksa atla

graph.add_conditional_edges("research", after_research, {
    "research": "research",
    "enrich": "enrich",
    "draft": "draft",
    END: END
})
```

### Retry Mekanizması
Research agent bazen JSON parse hatası verebilir. State'e `error` ve `retry_count` ekliyoruz. Routing fonksiyonu hata görünce aynı node'a geri gönderiyor — maksimum 2 deneme.

### CSV Batch Processing
`data/leads.csv` dosyasındaki her şirket için pipeline'ı sırayla çalıştırır:
```python
def run_batch():
    with open("data/leads.csv") as f:
        for row in csv.DictReader(f):
            run(row["company"])
```
CSV formatı:
```
company,domain
Linear,linear.app
Vercel,vercel.com
```

### Bu Projedeki Graph Akışı
```
research → [koşullu] → enrich → draft → approval → [koşullu] → send → save
                    ↘ draft (domain yoksa)          ↘ save (taslak kaydet)
                    ↘ retry (hata varsa)            ↘ END (iptal)
```

### Resume — Yarıda Kalan Draft'a Devam
Kayıtlı bir draft lead'i yükleyip `approval_node`'dan devam ettirir. DB'den state yeniden oluşturulur, sadece approval → send → save kısmı çalışır:
```python
def resume_lead(lead_id: int):
    # DB'den lead yükle
    # State'i yeniden oluştur
    # Sadece approval → send → save graph'ını çalıştır
```

Kaydetme sırasında kullanıcıya sorulur:
- **Üstüne yaz** → mevcut lead güncellenir (yeni ID oluşmaz)
- **Yeni draft** → yeni lead kaydı oluşturulur

### Approval Menüsü Seçenekleri
```
[1..N] Mevcut stiller         → seçilen stil ile yeniden yaz
[D] Anlık düzenleme           → kaydetmeden uygula
[Y] Yeni stil oluştur ve kaydet → JSON'a ekler, uygular
[E] Onayla ve gönder          → approved=True → send node
[K] Taslak olarak kaydet      → save_as_draft=True → save node
[H] İptal et                  → END (kayıt yok)
```

---

## 19. Streamlit — Python ile Web Arayüzü

Streamlit, HTML/CSS/JS yazmadan Python ile web arayüzü oluşturmayı sağlayan bir kütüphane.

**Nasıl çalışır:**
```python
import streamlit as st

st.title("ProspectPilot")
st.button("Araştır")
st.text_area("Body", value="...")
st.metric("Gönderildi", 5)
```
Bu Python kodu, tarayıcıda otomatik render edilen bir web sayfasına dönüşür.

**Çalıştırma:**
```powershell
.\venv\Scripts\streamlit run app.py
# → localhost:8501 açılır
```

**Neden Streamlit?**
- Terminal bilmeyen müşterilere arayüz sunmak için
- Flask/FastAPI + HTML yazmaktan çok daha hızlı
- "Kendi arayüzümü yaptım" diyebiliyorsun (Airtable'a bağımlı değilsin)
- Demo videosunda çok daha etkileyici görünüyor

**Sınırlaması:** Her butona basışta tüm Python kodu baştan çalışır. Bu yüzden adımlar arası veriyi `session_state`'te saklamak gerekir.

---

## 20. Streamlit session_state — Adımlar Arası Veri

Streamlit her etkileşimde sayfayı baştan çalıştırır. Değişkenler sıfırlanır — ama `session_state`'e yazılanlar yaşar.

**Örnek — çok adımlı form:**
```python
# Adım 1: Şirket adı al
if "stage" not in st.session_state:
    company = st.text_input("Şirket adı")
    if st.button("Araştır"):
        st.session_state["company"] = company
        st.session_state["stage"] = "researching"
        st.rerun()

# Adım 2: Araştır
elif st.session_state["stage"] == "researching":
    with st.spinner("Araştırılıyor..."):
        result = research_company(st.session_state["company"])
        st.session_state["research"] = result
        st.session_state["stage"] = "review"
    st.rerun()

# Adım 3: İncele
elif st.session_state["stage"] == "review":
    st.write(st.session_state["research"])
```

**Kural:** Pahalı işlemler (API çağrıları) session_state'te saklanır — her rerun'da tekrar çalıştırılmaz.

---

## 21. Hardcoded vs Environment Variable

**Hardcoded** — değer doğrudan koda yazılmış:
```python
SENDER_NAME = "Alex"  # değiştirmek için kodu bul, düzenle, kaydet
```

**Environment variable** — `.env` dosyasından okunuyor:
```python
SENDER_NAME = os.getenv("SENDER_NAME", "Alex")  # .env'den gelir
```

**Neden önemli:** Müşteriye teslim ettiğinde Python bilmeyen biri bile `.env` dosyasını açıp değiştirebilir. Kod karıştırmasına gerek yok.

**Bu projede taşınanlar:**
```
SENDER_NAME=Alex
SENDER_ROLE=AI Automation Consultant
SERVICE_OFFERED=Building AI-powered outreach systems...
```

**İkinci faydası:** Aynı değer birden fazla dosyada kullanılıyorsa (graph.py, follow_up.py gibi) tek yerden yönetilir. Değişince her dosyayı aramak gerekmez.

---

## 22. Proje Mimarisi — Katmanlar

```
┌─────────────────────────────────────────────┐
│  app.py (Streamlit UI)                      │
│  Kullanıcı arayüzü — tarayıcıdan yönetim   │
└────────────────┬────────────────────────────┘
                 │ fonksiyon çağrıları
┌────────────────▼────────────────────────────┐
│  src/pipeline/graph.py (LangGraph)          │
│  Terminal/batch pipeline orchestration      │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│  src/agents/  research_agent, draft_agent   │
│  src/tools/   enrichment, email_sender,     │
│               reply_detector, follow_up     │
│  src/db/      models, crud, viewer          │
└─────────────────────────────────────────────┘
```

- **Streamlit** → görsel arayüz, müşteri kullanır
- **LangGraph** → terminal ve CSV batch, orchestration
- **agents/** → AI karar veren katman (Claude)
- **tools/** → dış servisler (Hunter.io, SendGrid, Gmail)
- **db/** → SQLite veri katmanı

---

_Son güncelleme: 2026-06-12_
