# ProspectPilot — Proje Yol Haritası

_Oluşturulma: 2026-06-11 | job-to-project ajanı tarafından tasarlandı_

## Projenin Amacı

Upwork'te "AI Agent Developer - Outreach & Lead Generation Automation" kategorisindeki ilanlar için proposal atabilmek. Bunun için gerçek, çalışan, GitHub'da gösterilebilir bir proje gerekiyor.

## Projenin Tek Cümlelik Tanımı

> Bir şirket listesi verirsin, ajan her birini araştırır, kişiselleştirilmiş email taslağı yazar, sen onaylarsın, sistem gönderir ve takip eder.

## Klasör Yapısı (Hedef)

```
outreach automation/
├── docs/
│   ├── roadmap.md          ← bu dosya
│   ├── learning-notes.md   ← kavram notları
│   └── project-log.md      ← ne bitti, nerede kaldık
├── src/
│   ├── agents/             ← agent kodları
│   ├── tools/              ← araç fonksiyonları (search, enrich, send)
│   ├── pipeline/           ← orchestration
│   └── db/                 ← SQLite modelleri
├── data/
│   └── leads.csv           ← örnek input
├── .env.example
├── requirements.txt
└── README.md
```

## 4 Haftalık Roadmap

### Hafta 1 — Claude Tool Use + Araştırma Ajanı
**Hedef:** Bir şirket adı ver, ajan web'de araştırır, özet çıkarır.

**Stack:**
- Python 3.11+
- `anthropic` SDK
- Tavily API (web search)
- SQLite (basit kayıt)

**Teslim edilecek:**
- [ ] `src/agents/research_agent.py` çalışıyor
- [ ] Tek şirket için araştırma yapıp JSON çıktısı üretiyor
- [ ] CSV'den birden fazla şirket işleyebiliyor

---

### Hafta 2 — Enrichment + Email Taslağı + Onay Kuyruğu
**Hedef:** Email bul, kişisel taslak yaz, Airtable'a "pending" kaydet.

**Stack:**
- Hunter.io API (email enrichment)
- Airtable API (onay UI)
- Claude (email draft generation)

**Teslim edilecek:**
- [ ] `src/tools/enrichment.py` — Hunter.io entegrasyonu
- [ ] `src/agents/draft_agent.py` — email taslağı üretiyor
- [ ] Airtable'da "Pending Approval" kuyruğu çalışıyor

---

### Hafta 3 — LangGraph Refactor + Human-in-the-Loop
**Hedef:** Pipeline'ı LangGraph ile yeniden yaz, GitHub'a koy.

**Stack:**
- LangGraph (StateGraph)
- GitHub (README + demo video)
- Loom (demo kaydı)

**Teslim edilecek:**
- [ ] `src/pipeline/graph.py` — LangGraph StateGraph
- [ ] Human-in-the-loop interrupt çalışıyor
- [ ] GitHub repo açık, README yazılmış
- [ ] Loom demo videosu hazır

---

### Hafta 4 — Delivery Katmanı (Email Gönderme + Follow-up)
**Hedef:** Onaylanan emailler gerçekten gitsin, cevap gelmeyene follow-up yapılsın.

**Stack:**
- SendGrid API (email gönderimi)
- Gmail API (reply detection)
- APScheduler (günlük kontrol)

**Follow-up Sequence:**
| Gün | Aksiyon |
|-----|---------|
| 0 | İlk email gönderildi |
| 3 | Reply yok → Follow-up 1 taslağı Airtable'a düşer |
| 7 | Hâlâ reply yok → Follow-up 2 taslağı |
| 10 | Yok → "No Response" olarak kapat |

**Teslim edilecek:**
- [ ] `src/tools/email_sender.py` — SendGrid entegrasyonu
- [ ] `src/tools/reply_detector.py` — Gmail API kontrolü
- [ ] `src/pipeline/scheduler.py` — günlük çalışan kontrol

---

## Stack Özeti

| Katman | Araç | Neden |
|--------|------|-------|
| LLM | Claude (claude-sonnet-4-6) | Tool use, structured output |
| Agent framework | LangGraph | Multi-step state machine |
| Web search | Tavily API | Prospect araştırma |
| Enrichment | Hunter.io | Email bulma |
| Database | SQLite | Local, sıfır setup |
| Onay UI | Airtable | Human-in-the-loop dashboard |
| Email delivery | SendGrid | Transactional email |
| Reply detection | Gmail API | Follow-up kararı |
| Scheduling | APScheduler | Günlük kontrol |

## Proposal Cümlesi (Hafta 4 sonunda söylenecek)

> "Research → enrich → draft → human approval → send → follow-up sequence — uçtan uca pipeline kurdum. İşte GitHub linki, işte demo."
