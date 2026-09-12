# EMANET — hesap veren otonom trading ajanı

> *Emanet:* birine güvenilerek bırakılan, olduğu gibi geri verilmesi gereken şey.

OKX TR üzerinde, **OKX Agent Trade Kit (ATK)** MCP sunucusuna doğrudan bağlanan, tamamen
deterministik bir otonom spot ajanı. Ürünün tezi tek cümle:

**İşlem yapan değil, hesap veren ajan.** Her karar — özellikle de *yapılmayan* işlemler —
gerekçesiyle kaydedilir. "Bana güvenin" demez; defteri verir.

Agentic Trading Hackathon · Komünite × OKX TR · 12.09.2026 · bireysel katılım (Osman Özcanlı)

---

## 1. Ne yapar

Her 3 dakikada bir, 8 USDT paritesi için:

1. **Sense** — bakiye, açık pozisyonlar ve üç bağımsız kaynaktan sinyal
2. **Reason** — *Üç Tanık Kuralı*: en az 2 tanık aynı yönü göstermeli, **hiçbiri karşı çıkmamalı**
3. **Act** — öneri **risk kapısından** geçer; kapı veto ederse emir gitmez, sebep deftere yazılır
4. **Evaluate** — açık pozisyonlar borsayla mutabakat edilir, zaman stopu uygulanır

| Tanık | ATK MCP aracı | Ne söyler |
|---|---|---|
| Teknik | `market_get_indicator` (RSI 14, EMA 20, 15m) | Fiyat hareketi |
| Akıllı para | `smartmoney_get_signal_overview_by_filter` | Kârlı traderların long/short dengesi |
| Duygu | `news_get_coin_sentiment` | Haber ve sosyal akışın tonu |

Tanıklardan biri ulaşılamazsa ya da tutarsız veri döndürürse (RSI 0, EMA fiyattan kopuk) `unknown` döner:
**çökmez, oy da vermez.** `unknown` veto değildir; kalan iki tanık aynı yönü gösterirse işlem yine olur
(`block_on_unknown: false`, bilinçli seçim: bir kaynağın kesilmesi ajanı kilitlememeli).

## 2. Mimari

```
ARAYUZ  localhost:8787        karar kartlari + "hangi kural kac kez devreye girdi"
   │
AGENT   src/agent.py          Sense -> Reason -> Act -> Evaluate, deterministik, LLM yok
   │
RISK    src/risk.py           saf fonksiyon, aga cikmaz, VETO yetkili — tek "hayir" diyebilen katman
   │
MCP     src/mcp.py            JSON-RPC/stdio istemcisi, sifir bagimlilik, 168 ATK araci
   │
ATK     okx-trade-mcp         iki profil: islem (demo veya canli) · istihbarat
   │
BORSA   OKX TR                her alim emri OCO kar-al/zarar-kes ile gider — ajan olse de calisir
```

**Üç tasarım kararı:**

1. **Risk kapısı her şeyi ezer.** Sinyal ne derse desin, kural ihlaliyse emir gitmez.
   Kapı ağa hiç çıkmaz; "API yavaşladı" diye atlanamaz.
2. **Risk borsada, ajanda değil.** Kâr-al/zarar-kes emirle birlikte gönderilir (`oco`).
   Ajan çökse, laptop kapansa, internet gitse stop borsada durur.
   Ajan ayrıca emirden sonra koruma emrinin **gerçekten oluştuğunu doğrular**; oluşmadıysa
   pozisyonu anında geri alır ve o pariteyi oturum boyunca kapatır.
3. **Karar yolunda LLM yok.** Zincirin hiçbir halkasında halüsinasyon görebilecek bileşen yok.
   (Bir LLM katmanı denendi, terk edildi — bkz. §7.)

## 3. Risk kuralları (`config.yaml`)

| Kural | Değer | Deftere yazılan gerekçe |
|---|---|---|
| Pozisyon boyutu | kalan sermayenin %10'u | — |
| Nakit tamponu | sermayenin %20'si **hiç kullanılmaz** | "Nakit tamponu korunuyor" |
| Aynı anda açık pozisyon | en fazla 4 | "Ayni anda en fazla 4 acik pozisyon" |
| Aynı pariteye ikinci giriş | yasak — borsaya sorularak | "borsada zaten acik pozisyon var" |
| Stop-loss | zorunlu, borsa tarafında, doğrulanır | "borsa koruma emrini olusturmadi… geri alindi" |
| Kâr-al / zarar-kes | +%0,8 / −%0,5 | — |
| Zaman stopu | 8 dk (demo penceresi) | "Zaman stopu… ajan pozisyonu kendisi kapatti" |
| Kapatma miktarı | borsadan okunur (OCO `sz`, yoksa cüzdan bakiyesi) | "KAPATMA BASARISIZ… sonraki turda yeniden denenecek" |
| Min. emir tutarı | borsadan okunur | "minimum emir tutarinin altinda" |
| Günlük kayıp | %3 → Safe Mode (kalıcı) | "Safe Mode aktif" — **gerçek kayıpla hiç tetiklenmedi**, bkz. §7 |
| Bakiye okunamazsa | işlem yok, Safe Mode **değil** | "Olculemeyen bakiyeyle islem yapilmaz — bu bir kayip degil, bilinmezliktir" |

Sermaye tavanı `virtual_cap_usdt: 30` demo hesabı canlıyla eşitler; boyutlandırma yüzdesel olduğu için
30 USDT ile de 3.000 USDT ile de aynı kod çalışır.

Risk kuralları ve tanık eşiklerinin çoğu config'te; akıllı para eşiği (%60 / %40), RSI periyodu (14) ve panel portu kodda sabit.

## 4. Kurulum ve çalıştırma

```bash
npm i -g @okx_ai/okx-trade-cli @okx_ai/okx-trade-mcp   # ATK CLI + MCP sunucusu
npx skills add okx/agent-skills                           # 10 OKX skill (.agents/skills/)
okx config init                                           # site: TR · demo: Y · API key
pip install pyyaml
python src/agent.py --once                        # tek tur, demo
python src/agent.py                               # otonom dongu, demo (config.yaml)
python src/agent.py --config config.live.yaml     # otonom dongu, canli (ayri defter + ayri state dosyasi)
python src/dashboard.py                           # http://localhost:8787 (config.yaml'daki defteri gosterir)
```

Kimlik bilgileri `~/.okx/config.toml`'da, proje dışında. Bu repoda **hiçbir key yok.**
`dry_run: true` ile emir gönderilmeden çalıştırılabilir.

## 5. Kanıt

- **Demo:** `logs/journal.jsonl` — 17:29'dan itibaren; 17:36 öncesi 16 kayıt yalnızca bekleme/red
  (karantina sonrası, emir yok). Öncesi `logs/archive/`, bkz. §7.
- **Canlı:** `logs/journal.live.jsonl` — 18:29–18:30 iki gözetimli tur (4 emir, 5 red), 19:00'dan itibaren
  kesintisiz otonom. 19:00'da zaman stopu 4 pozisyonu kapattı; borsada 4 satış fill'i `agentx…` id'leriyle duruyor.
  Bağımsız doğrulama borsadan `spot_get_fills` / `account_get_balance` ile yapıldı; defter emir ID'si taşımıyor (§7).
  18:59'daki tek tur defterden çıkarıldı: ajan yanlışlıkla demo state dosyasını okumuştu (§8, hata 8).
- **Metrikler:** `METRICS.md` (`python src/metrics.py` ile üretilir)
- **Süreç günlüğü:** `PROGRESS.md` — günün tüm kararları, hataları ve düzeltmeleri, saat saat

## 6. ATK MCP entegrasyonu

Ajan bir CLI sarmalayıcı değil, **MCP istemcisi**: `src/mcp.py` ATK'nın stdio sunucusuyla JSON-RPC
konuşur, kalıcı oturum tutar, ölürse yeniden başlatır. Kullanılan araçlar:
`market_get_indicator` · `market_get_ticker` · `market_get_instruments` · `account_get_balance` ·
`smartmoney_get_signal_overview_by_filter` · `news_get_coin_sentiment` · `spot_place_order` ·
`spot_get_algo_orders` · `spot_cancel_algo_order`.
Kalıcı oturum sayesinde tur süresi CLI'a göre 31 → 18 sn.

Ayrıca `.agents/skills/` altında 10 OKX skill'i Claude Code'a yüklü; `skills-lock.json` sürüm kilidi.

## 7. Bilinen sınırlar — dürüst liste

- **"Türkçe hedef → kural" özelliği yok.** Planlanmıştı; `claude -p` tabanlı LLM katmanı
  (`src/llm.py`) zaman kutusunu aştı ve terk edildi (`enabled: false`). Hedefler `config.yaml`'dan girilir.
- **Teknik tanık hiçbir alıma katılmadı.** Demo'daki alımların tamamında teknik tanık "wait" dedi; alımı veren
  7 günlük akıllı para ile haber duygusu oldu. İkisi de saatler boyunca neredeyse sabit. Yani 8 dakikalık
  pozisyonlar günlük ölçekli sinyalle açılıp zaman stopuyla kapanıyor; bu bir çalkalama riskidir, karar kalitesi
  değil. Teknik tanığın tek ve konsensüs mimarisinin gerçek katkısı bugünkü veriyle kanıtlanmış değil.
- **Kâr-al/zarar-kes'in fiyatla tetiklenmesi bugün gözlemlenmedi.** Emirler borsada `live` duruyor;
  test penceresinde fiyat bantlara girmedi. Pozisyonları kapatan her seferinde zaman stopu oldu (sayı `METRICS.md`).
- **Günlük kayıp kuralı gerçek kayıpla hiç tetiklenmedi.** Demo'da yapısal olarak tetiklenemez: sermaye tavanı
  yüzünden ölçülen özkaynak hep 30'a eşit. Defterdeki "Safe Mode" kayıtları 6 numaralı hatadan. Gerçekleşmemiş
  zarar da sayılmıyor; kural yalnızca kapanan pozisyonların kaybını görür.
- **Defter borsa emir ID'si taşımıyor.** Alım ve satış kayıtlarında `clOrdId` var, `ordId`/fill fiyatı yok.
  Doğrulama borsadan `clOrdId` eşleştirerek yapılıyor; ideali her kayda borsanın cevabını yazmak.
- **Defterin ilk sürümü kirliydi.** 17:30'a kadar borsanın reddettiği emirler "yapıldı" diye yazıldı
  (`sCode` okunmuyordu). %32 hayalet. Karantina: `logs/archive/NEDEN.md`. Metrikler 17:36 sonrası.
- **Canlıda istihbarat/işlem key ayrımı kalktı.** CLI tek profil adı dayattığı için salt-okunur profil
  işlem key'iyle ezildi. Davranış değişmedi, garanti zayıfladı.
- **Sermaye tavanı sabit.** Kâr bileşiklenmez; gerçek kullanımda tavan bakiyeyi izlemeli.
- **`~/.okx/config.toml` düz metin.** Üretimde key kasası gerekir.
- **`src/okx.py` kullanılmıyor.** İlk sürümün CLI sarmalayıcısı; MCP'ye geçince yedek yol olarak planlandı ama
  hiçbir çağıran ona düşmüyor. Yalnızca `load_config` oradan kullanılıyor.
- **OKB ve ORDI demo'da koruma emri oluşturmuyor** (canlıda oluşturuyor). Ajan bunu tespit edip
  pozisyonu geri alıyor; demo'da o iki parite fiilen kapalı.

## 8. Bugün yaşanan ve düzeltilen 9 hata

İlk altısı demo'da yakalandı; 7 ve 8 canlıya geçerken ortaya çıktı, gerçek parayla ama zararsız. Detay `PROGRESS.md`'de.

| # | Hata | Düzeltme |
|---|---|---|
| 1 | Bantlar geniş, slotlar doldu, ajan 57 dk dondu | Config her turda okunur, bantlar daraltıldı, zaman stopu |
| 2 | Demo'da sermaye hep 30 okunuyor, dağıtılan düşülmüyordu | `tavan − dağıtılan` |
| 3 | Yerel durumla borsa ayrıştı, aynı parite her turda alındı | Borsaya sor: canlı OCO'su olan pariteye girme |
| 4 | **Borsanın reddettiği emirler deftere "yapıldı" yazıldı** | Her cevapta `sCode` doğrulanır |
| 5 | Koruma emri sessizce oluşmuyor, pozisyon korumasız | Emirden sonra doğrula; yoksa geri al, pariteyi kapat |
| 6 | **OKX 6 dk kesildi; ajan bakiyeyi 0 sanıp Safe Mode'a girdi** | Okunamayan bakiye = bilinmezlik, kayıp değil |
| 7 | **Kapatma miktarı elde olandan fazlaydı** (komisyon base coin'den kesiliyor); demo hesabı dolu olduğu için maskeliydi | Satış miktarı borsadan (OCO `sz` / cüzdan); başarısız kapatma deftere yazılır, pozisyon düşürülmez |
| 8 | Demo ve canlı aynı state dosyasını paylaştı; canlı ajan demo pozisyonlarını okuyup sahte Safe Mode'a girdi | `logging.state` config'e alındı, `--config` bayrağı |
| 9 | Teknik tanık bozuk veriye (RSI 0.0, EMA 400 / fiyat 1140) "aşırı satım" dedi | Aralık dışı gösterge = `unknown` |

6 numaralı olay planlanmamış bir saha testiydi: kesinti boyunca ajan tek işlem yapmadı, çökmedi,
ağ gelince toparladı — ve bir hatasını ortaya çıkardı. Loglarda duruyor.

## 9. Dosyalar

```
src/agent.py       ana dongu            src/witnesses.py  uc tanik
src/risk.py        risk kapisi          src/mcp.py        MCP istemcisi
src/state.py       kalici durum         src/journal.py    iki defter (jsonl + md)
src/dashboard.py   arayuz               src/metrics.py    METRICS.md uretici
src/okx.py         config yukleyici     src/llm.py        terk edilen LLM katmani (kapali)
                   (+ kullanilmayan CLI sarmalayici)
config.yaml        tum ayarlar          logs/             defterler, durum, karantina
```
