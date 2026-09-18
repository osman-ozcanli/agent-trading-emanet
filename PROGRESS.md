# PROGRESS — Agentic Trading Hackathon (12.09.2026)

## ŞU ANKİ DURUM (18.09, hedef değişti: hackathon bitti, sıradaki amaç para kazanma)

Yarışma teslimi 12.09'da tamamlandı (bkz. altındaki tarihçe). 13.09 sabahından bugüne kod
**dondu** — hiçbir dosya değişmedi, sadece karar aşamasındayız. Şu an sistem tamamen kapalı:
süreç yok, borsada bekleyen emir yok. Bu bölüm 13.09–18.09 arası konuşulan ve KARARA
BAĞLANMAMIŞ her şeyi topluyor; kod tarafında hiçbiri henüz uygulanmadı.

**Yeni hedef (Osman, 16.09):** artık yarışma amaçlı "hesap veren ajan" değil, gerçek para
kazanma amaçlı otonom sistem. Mimari (risk kapısı, borsa tarafı stop, defter, ağ kesintisi
davranışı) olduğu gibi kalacak — bunlar zaten sağlam. Değişecek olan tek şey **karar mantığı**
(`witnesses.py` + `config.yaml` eşikleri), döngü değil.

### Bekleyen karar 1 — Backtest (`src/backtest.py`, henüz yazılmadı)
Ajana dokunmadan ayrı dosya. Kapsam: 8 parite × 90 gün 15dk mum + günlük akıllı para serisi
(ikisi de MCP'de mevcut, sınandı — `market_get_candles` 2021'e kadar gidiyor,
`smartmoney_get_signal_trend_by_filter` 90 gün günlük kova veriyor). Haber tanığı için geçmiş
oran yok, iki senaryo denenecek: yok say / makale sayısından yaklaşık oran. Mevcut kural aynen
uygulanacak (2/3 onay, sıfır karşı oy, +%0,8/−%0,5, 8dk zaman stopu, %0,1 komisyon her yön).
Çıktı: işlem sayısı, net getiri, kazanma oranı, eşik taraması (akıllı para 0,60→0,90,
RSI 35/65→25/75). Tahmini süre 2 saat. **Beklenti: mevcut eşiklerle negatif/sıfıra yakın** —
90 günlük akıllı para verisi ETH için incelendi, `weightedLongRatio` neredeyse hep 0,60 üstü
çıktı; yani ≥0,60 eşiği bu tanığı fiilen "hep al" yapıyor, gerçek ayrım gücü yok. Bu backtest
için hâlâ Osman'ın "hadi" demesi gerekiyor.

### Bekleyen karar 2 — Yol haritası (para kazanma), 6 adım, sıralı
1. Backtest (yukarıda) — kural değişmeden mevcut sinyallerin gerçekten bir kenarı var mı ölç.
2. Strateji revizyonu — tanıkların zaman ölçeğini eşitle (şu an teknik 15dk, akıllı para günlük,
   uyumsuz), eşikleri backtest'le tara, pozisyon boyutunu riske göre hesapla (şu an sabit %10,
   olması gereken: stop mesafesine göre değişken boyut, işlem başı risk sermayenin ~%1'i).
   Geçiş şartı: backtest'te komisyon sonrası pozitif VE maks. düşüş <%10.
3. Demo'da 2 hafta ileriye dönük test, dokunmadan izle.
4. 7/24 altyapı (aşağıda, ayrı karar).
5. LLM katmanı canlandırılır — SADECE üç rolde, emir kararında ASLA (aşağıda detay).
6. Küçük canlı (100–200 USDT), adım 3'teki kurallarla; aylık sonuç tutarlıysa sermaye artar.

### Bekleyen karar 3 — LLM'in yeri (`llm.py` şu an `enabled: false`, hiç çağrılmıyor)
Emir kararında LLM YOK ve olmayacak — 7/24 gerçek para gönderen yerde halüsinasyon kabul
edilemez. Üç meşru rol, hiçbiri emir veremez:
- **4. tanık**: haber/makro takvimi okuyup oy verir, veto edebilir (örn. "bugün FOMC var, bekle").
- **Rejim tespiti**: günde bir kez piyasayı sınıflandırır (trend/yatay/panik), config'teki HAZIR
  parametre setlerinden birini seçer — sayı uydurmaz, seçenek listesinden seçer.
- **Açıklama ve alarm**: deftere Türkçe özet, Telegram'a gün sonu raporu, anormallik uyarısı.
  (`.env.example`'da `TELEGRAM_BOT_TOKEN` yeri zaten var, kullanılmadı.)

### Bekleyen karar 4 — 7/24 altyapı: sunucu ŞİMDİ gerekli değil
Osman'ın kararı (16.09): ücretli sunucu şu an istemiyor. Ara çözüm — kod değişikliği
GEREKMİYOR, çünkü ajan zaten "kaldığı yerden devam edecek" şekilde yazılı (state dosyadan
okunuyor, açılışta borsayla mutabakat ediliyor, zaman stopu gerçek saate göre çalışıyor —
dün gece bunu kanıtladık, ajan kapalıyken 3 pozisyon borsanın kendi OCO'suyla kapandı).
Eksik olan TEK şey: laptop açılınca ajanın OTOMATİK başlaması. Çözüm: Windows Görev
Zamanlayıcısı'na "oturum açılınca `python src/agent.py` çalıştır" kaydı — bedava, ~10 dk,
kod değişikliği yok. **Henüz kurulmadı, Osman onay verirse kurulacak.**
Gerçek dezavantajı tespit edildi: 8dk'lık zaman stopu gerçek saate göre çalıştığı için laptop
kapalıyken açık kalan pozisyon yalnızca borsanın geniş bandıyla (%0,8/−%0,5) korunur, tasarlanan
hızlı devir bozulur — güvenlik sorunu değil, strateji sapması (en kötü senaryo: 4 pozisyon ×
%0,5 ≈ sermayenin %2'si).
İleride sunucu gerekirse tek gerçek "süresiz bedava" seçenek: **Oracle Cloud Always Free**
(AWS/GCP'nin ücretsiz katmanı 12 ay sonra ücretli olur, bu değil; Railway/Render sürekli
arka plan sürecini bedava katmanda uyutur, bize uymaz).

### Diğer küçük notlar (13–16.09)
- README ve METRICS.md düzeltmeleri yapıldı: yanlış iddialar ("unknown veto eder", "CLI yedek
  yolu", "elle sayı yok") kaldırıldı, gerçek davranışla değiştirildi (bkz. git log, commit'ler
  `5f97cfc`, `c699299`).
- `config.yaml` artık CANLI (eski `config.live.yaml`), demo `config.demo.yaml` oldu ve pasif.
  `agent.py --config <dosya>` bayrağı eklendi.
- Kapatma miktarı borsadan okunuyor (Hata 7), ayrı state dosyaları (Hata 8), teknik tanık
  bozuk veriyi (RSI 0, EMA fiyattan kopuk) artık "unknown" sayıyor (Hata 9) — hepsi kod'da,
  commit `5f97cfc`.
- Sunum Gamma ile hazırlandı, PPTX/PDF dışa aktarıldı, `src/sunum_guncelle.py` ile sayı
  otomatik tazeleniyor (ajanın turuna bağlandı, sonra "artık çalışmasın" denince ajanla
  birlikte durdu).
- `~/.okx/`, `~/.claude.json`, npm global paketler taranıp proje dışı hiçbir sızıntı
  bulunmadı; iki gereksiz `.bak` dosyası tespit edildi (silinmesi Osman'a bırakıldı).
- Görsel açıklayıcı artifact yayınlandı: "Bağlanmanın Anatomisi"
  (repo/paket/API/MCP/skill mekaniği), https://claude.ai/artifact/Agomg8HrjeQoDn9YgY51X6

## ŞU ANKİ DURUM (13.09 11:10, tarihçe)
Sunum yapıldı. Süreçler 12.09 19:58'de durduruldu; gece OCO stopları borsada kendisi çalıştı (XRP/SOL/ETH), kayıp 0,19 USDT.
**Demo kapandı:** `config.yaml` artık canlı, demo `config.demo.yaml` (pasif). Panel ve ajan varsayılan canlı okur.
Şu an çalışan süreç yok, borsada bekleyen emir yok, USDT 29,81.

## ŞU ANKİ DURUM (12.09 18:12, tarihçe)
**Adım 1-6 ✅ · 8 ✅ · 9 ✅ · 10 kısmi ✅ · Adım 7 (LLM) ⛔ terk edildi**

Agent arka planda çalışıyor — 3 dakikada bir tur, baştan sona MCP üzerinden, demo hesaba
gerçek emir gönderiyor, risk kapısı **4 farklı gerekçeyle** emir reddediyor, her karar
deftere yazılıyor. Panel `localhost:8787`'de canlı. **Canlı $30'a dokunulmadı.**

**Bugün 6 ciddi hata bulundu ve düzeltildi:**
donma · sermaye hesabı · sahte hacim · **defterin olmayan işlemleri kaydetmesi** ·
korumasız pozisyon · **ağ kesintisini iflas sanıp kendini kapatma**.
Altısı da demo'da yakalandı — canlıya erken geçilseydi gerçek parayla öğrenilecekti.

**17:58–18:04 arası gerçek bir OKX kesintisi yaşandı** (planlanmamış saha testi).
Ajan körlemesine işlem yapmadı, çökmedi, ağ gelince toparladı — ama sahte Safe Mode'a girdi.
Düzeltildi. Detay: "GERÇEK AĞ KESİNTİSİ" bölümü.

⚠️ **Defter 17:36'da sıfırlandı.** Eski kayıtların %32'si hayaletti (borsa reddetmiş ama
deftere yazılmış). Karantina: `logs/archive/` + `NEDEN.md`. Teslim metrikleri yalnızca
17:36 sonrasını kapsar.

## CANLI AJAN SÜREKLİ ÇALIŞIYOR (19:01) — ve 3 düzeltme

`python -u src/agent.py --config config.live.yaml` arka planda, çıktı `logs/agent.live.out`.
Demo ajan ve panel aynen çalışmaya devam ediyor.

**Hata 7 — kapatma miktarı yanlıştı (canlıda yakalandı, demo maskeliyordu).** Spot komisyonu base coin'den
kesiliyor; ajan `size/px` kadar satmaya kalkınca elindekinden fazla satar, borsa reddeder, OCO ise çoktan iptal
edilmiş olur. Düzeltme: satış miktarı borsadaki OCO satırından (`sz`) alınır, yoksa cüzdan bakiyesi lot'a
yuvarlanır (`_held`). Kapatma başarısızsa deftere yazılır, pozisyon düşürülmez, sonraki tur yeniden denenir.
Kanıt: 19:00:49–54, 31–32 dk açık 4 canlı pozisyon tek turda kapandı, bakiye 29,97 USDT.

**Hata 8 — demo ve canlı aynı state dosyasını paylaşıyordu.** İlk canlı başlatmada (18:59) ajan demo'nun
`logs/state.json`'ını okudu, yanlış hesapla Safe Mode kilitledi. Ajan öldürüldü, `logging.state` config'e
eklendi (`state.json` / `state.live.json`), yanlış kilit kaldırıldı, o turun 8 kaydı canlı defterden çıkarıldı
(gerekçe: ajanın canlı pozisyonlar hakkında verdiği kararlar değildi).

**Hata 9 — teknik tanık bozuk veriye "alış" diyordu** (ZEC: RSI 0.0, EMA 400, fiyat 1140). Artık
`0<RSI<100` ve EMA/fiyat oranı 0,5–2 dışında "unknown".

**Hata 8'in artçısı (19:00–19:27, demo).** 18:59'daki yanlış Safe Mode kilidi 19:00'da kaldırıldı ama demo ajan
o sırada turun ortasındaydı ve tur sonunda eski durumu geri yazdı. Demo 27 dakika "Safe Mode aktif" diye reddetti;
bu kayıtlar gerçek kayıp değil, hata 8'in kalıntısı. 19:28'de kilit yeniden kaldırıldı, kayıtlar silinmedi.

`agent.py --config` bayrağı eklendi; demo ve canlı yan yana kendi dosyalarından çalışır.

## KALAN İŞ — 18:38 itibarıyla
| # | İş | Durum |
|---|---|---|
| ✅ | README.md | yazıldı |
| ✅ | METRICS.md (`python src/metrics.py`, elle sayı yok) | üretildi |
| ✅ | SUNUM.md — 3 dk metin + hazır cevaplar + demo akışı | yazıldı |
| ✅ | Canlıda gözetimli 2 tur, 4 gerçek emir, borsadan doğrulandı | 18:29–18:30 |
| ⏳ | **Video/GIF** — Osman ekran kaydı alacak (SUNUM.md "Demo akışı" sırası) | 5 dk |
| ⏳ | **Git repo + push** — Osman çalıştırır, komutlar aşağıda | 5 dk |
| ⏳ | Son kontrol: panel açık, ajan canlı, key hiçbir yerde görünmüyor | 2 dk |

Kilide **52 dk**.

## TESLİM ✅ (18:45)
**Repo:** https://github.com/osman-ozcanli/agent-trading-emanet — public, dışarıdan doğrulandı:
kökte README · METRICS · SUNUM · PROGRESS · config · src/ · logs/ · skills-lock; `.env` yok, key yok.

## SIRADAKİ AKSİYON
1. Ekran kaydı — `SUNUM.md` "Demo akışı" sırasıyla, terminal göstermeden
2. 19:20 civarı son sicil: `git add logs` → commit → push (ajan yazmaya devam ediyor)
3. Teslim formuna repo linki + video
4. 20:00 sunum — `SUNUM.md`; panel ve OKX sekmesi açık

## CANLI ÇALIŞAN SÜREÇLER
- `python -u src/agent.py` — otonom döngü, 3 dk'da bir tur
- `python -u src/dashboard.py` — **http://localhost:8787**

## GÜVENLİK TAAHHÜDÜ
Tüm geliştirme **demo hesapta**. CLI'da `live` profili YOK — canlı $30'a emir gitmesi
teknik olarak imkansiz. Canliya gecis ayri bir adim olacak ve Osman'in acik onayi olmadan yapilmayacak.

## SÜRE
Başlangıç 09:00 · **Dosya kilidi 19:30** · Sunumlar 20:00 · Ödül töreni 22:15
Son güncelleme **18:12** → **1 saat 18 dk kaldı.**

---

# 1. BENDEN NE İSTENİYOR?

**Etkinlik:** Agentic Trading Hackathon — Komünite × OKX TR, Vadistanbul.
**Katılım:** Bireysel. **Ödül:** $2.500 / $1.500 / $1.000

**Görev:** OKX TR üzerinde **otonom çalışan bir trading agent** kurmak.

- Tüm işlemler **agent tarafından otonom** alınmalı — el ile girilen işlem değerlendirilmez
- Sermaye: OKX TR'nin verdiği işlem kredisi, **izole sub-account**, bana özel API key (~$30)
- Kütüphane/dil kısıtı **yok** — "açık kaynak kütüphaneleri ve kendi araçlarınızı kullanmanız serbesttir"

**Teslim (19:30):** README + kısa video/GIF + performans metrikleri + çalışan agent + 3 dk sunum

**Yasaklar:** El ile işlem, önceden hazırlanmış sistemi "sıfırdan yapıldı" diye sunmak, telif / KVKK ihlali

## Değerlendirme kriterleri

*(Osman tarafından 13:30'da resmî yönergeden teyit edildi.)*

| Kriter | Orijinal ad | Ağırlık |
|---|---|---|
| İşlevsel Fayda / Değer | Functional Utility & Value | **%30** |
| Kullanıcı Deneyimi / Etkileşim | User Experience & Interaction | **%30** |
| ATK MCP Entegrasyon Derinliği | ATK MCP Integration Depth | **%20** |
| Sistem Güvenilirliği | System Reliability | %10 |
| **İnovasyon & Özgünlük** | Innovation & Uniqueness | %10 |

> **Hesap performansı (getiri / drawdown) puanlanmıyor.** Bu bir para kazanma yarışı değil, **ürün** yarışı.
>
> **Not:** 5. kriter "Sunum/Demo" değil, **İnovasyon & Özgünlük**. Yani cilalı sunum tek başına puan getirmiyor;
> puanı getiren şey **kimsenin yapmadığı bir şey yapmak.** Bu, "Üç Tanık Kuralı" + `smartmoney`/`sentiment`
> kullanımı kararını doğruluyor — rakiplerin çoğu sadece `market` + `trade` kullanacak.
> Sunum yine de yapılacak (teslim şartı) ama kendi başına puanlanmıyor.

---

# 2. DOĞRU ANLADIK MI? — Üç büyük düzeltme yaşandı

### Düzeltme 1 — Değerlendirme kriterleri yanlış biliniyordu
CLI'daki ilk oturum kriterleri "performans %35 / mimari %25 / risk %20" diye vermişti. **Yanlıştı.**
Sayfa yeniden çekilince gerçek liste çıktı. Doğrulayan ipucu: listedeki **"ATK" = Agent Trade Kit**.

**Sonucu:** Tüm strateji değişti. "Az işlem, düşük drawdown ile para kazan" planı çöpe gitti.
Yeni hedef: **faydalı + kullanımı keyifli + ATK'yı derinlemesine kullanan bir ürün.**

### Düzeltme 2 — Bu bir "Python botu yaz" işi değil
OKX'in **Agent Trade Kit**'i var: hazır MCP server + 10 skill paketi.
`ccxt` ile kendi bağlantımı yazmak ATK'yı baypas etmek olurdu → **%20'lik kriteri sıfırlardı.**

**Sonucu:** `ccxt` planı iptal, ATK üzerine inşa ediyoruz.
Teknik göstergeleri (RSI / MACD / EMA / Bollinger + 70 tanesi) elle yazmaya da gerek yok — `okx-cex-market` içinde hazır.

### Düzeltme 3 — "Agent = Claude" değil
Otonom çalışacak olan **ayrı bir program**. Claude Code onu yazan araç.
Programı ben başlatırım, izlerim, gerekirse durdururum — ama **kararları program verir.**

**Sonuç: Evet, artık doğru anlıyoruz.**
[Kesin] ATK'nın varlığı ve yapısı doğrulandı (repo klonlandı, CLI kuruldu, bağlantı test edildi).
[Kesin] Kriter listesi 13:30'da Osman tarafından resmî yönergeden teyit edildi. Düzeltme: 5. kriter
"Sunum/Demo" değil **İnovasyon & Özgünlük** — özgünlük artık doğrudan puanlı, bu "Üç Tanık Kuralı" kararını güçlendirdi.

---

# 3. MİMARİ (kurulacak yapı)

*(16:50 — koda birebir uyan hali. Eski şemadaki "karar anında LLM" ve `PreToolUse` hook
kaldırıldı: LLM terk edildi, MCP asıl yol oldu.)*

```
┌─────────────────────────────────────────────┐
│  ARAYUZ  (Kullanici Deneyimi %30)           │  karar kartlari + reddetme kaydi
└────────────────┬────────────────────────────┘
┌────────────────▼────────────────────────────┐
│  AGENT CEKIRDEGI — agent.py                 │  Sense -> Reason -> Act -> Evaluate
│  UC TANIK KURALI (deterministik)            │  2 onay + sifir karsi oy
└────────────────┬────────────────────────────┘
┌────────────────▼────────────────────────────┐
│  ⛔ RISK KAPISI — risk.py                    │  saf fonksiyon, aga cikmaz, VETO yetkili
└────────────────┬────────────────────────────┘
┌────────────────▼────────────────────────────┐
│  MCP ISTEMCISI — mcp.py (130 satir)         │  JSON-RPC stdio, 168 tool
└────────────────┬────────────────────────────┘
┌────────────────▼────────────────────────────┐
│  OKX ATK MCP SERVER  (derinlik %20)         │  demo: emir · prod: istihbarat (read-only)
└────────────────┬────────────────────────────┘
┌────────────────▼────────────────────────────┐
│  BORSA — OCO emirleri (TP/SL)               │  agent olse de calisir
└─────────────────────────────────────────────┘
```

**Üç mimari fikir — jüriye anlatılacak olan:**

1. **Risk kapısı her şeyi ezer.** Sinyal ne derse desin, kural ihlaliyse emir gitmez.
   Ağa çıkmayan saf fonksiyon — API yavaşladı diye atlanamaz.
2. **Risk borsada, agent'ta değil.** TP/SL emirle birlikte gidiyor (`oco`, `state: live`).
   Agent çökse, laptop kapansa, elektrik gitse stop çalışır.
3. **Karar yolunda LLM yok — bilinçli.** Zincirin hiçbir halkasında halüsinasyon görebilecek
   bileşen yok. (Not: bu karar 16:05'te, LLM denemesi başarısız olduktan sonra alındı — bkz. Adım 7.)

---

# 3.5 ÜRÜN KARARI (Adım 3) ✅

## Tek cümle — jüriye söylenecek olan
> **"Kripto bilmeyen birinin, bildiğini iddia etmeden, parasını emanet edebileceği bir vekil."**

## Vaat (İşlevsel Fayda %30)

> ⚠️ **17:12 DÜZELTME — bu vaadin yarısı GERÇEKLEŞMEDİ.**
> Aşağıdaki "kullanıcı hedefini Türkçe yazar, agent kurallara çevirir" kısmı **yapılmadı**:
> LLM katmanı denendi, başarısız oldu, terk edildi (bkz. Adım 7).
> **Jüriye bu özellik varmış gibi anlatılmayacak.** Hedefler şu an `config.yaml`'dan elle giriliyor.
>
> **Gerçekleşen kısım:** agent her kararını — özellikle de *yapmadığı* işlemleri — jargonsuz
> Türkçe gerekçesiyle kaydediyor ve panelde gösteriyor. Ürünün tezi bu ayakta duruyor.

*(Orijinal vaat, kayıt için:)*
Kullanıcı hedefini **normal Türkçe** yazar:
*"1456 liram var, %5'ten fazla kaybetmek istemiyorum, yavaş büyüsün."*
Agent bunu kurallara çevirir, otonom uygular ve her adımı **jargonsuz** anlatır.

**Kimin derdi:** Kripto bilmediği için ya hiç girmeyen ya da rastgele girip yanan kitle.
**Neden özgün:** Yarışmacıların çoğu kripto bilen; kendileri gibi insanlar için araç yapacaklar.
Asıl büyük kitle bilmeyenler. Osman'ın alan bilgisi olmaması burada dezavantaj değil, ürünün kaynağı.

## Mekanizma — "Üç Tanık Kuralı" (ATK derinliği %20)
Agent **tek sinyale asla güvenmez.** İşlem için üç bağımsız kaynağın aynı yönü göstermesi şart:

| Tanık | Kaynak (ATK skill) | Ne söyler |
|---|---|---|
| 1. Teknik | `okx-cex-market` (RSI/MACD/EMA...) | Fiyat hareketi ne diyor |
| 2. Akıllı para | `okx-cex-smartmoney` | Başarılı traderlar ne yapıyor |
| 3. Duygu | `okx-sentiment-tracker` | Haber ve sosyal hava nasıl |

Üçü anlaşmazsa **işlem yapmaz** — ve **neden beklediğini yazar.** Bekleme kararı da bir çıktıdır.
Emir `okx-cex-trade`, bakiye `okx-cex-portfolio` üzerinden → **5 skill derinlemesine kullanılıyor.**

## Neden bu ikisi birlikte
- Tek başına "vekil" (C): güzel arayüz ama içi boş görünme riski
- Tek başına "üç tanık" (A): teknik olarak sağlam ama kime faydası olduğu soluk
- **Birlikte:** hem vaat hem kanıt. Jüri "nasıl güveneyim?" diye sorduğunda cevap hazır.

## Sonraki adımlara etkisi
- **Adım 4:** Döngü üç tanığı deterministik toplar; LLM sadece "bu üçünü nasıl yorumlarım + kullanıcıya nasıl anlatırım" için çağrılır
- **Adım 5:** Risk kapısı kullanıcının Türkçe hedefinden üretilir ("%5'ten fazla kaybetme" → `daily_loss_limit_pct: 5`)
- **Adım 7:** Arayüzün ana öğesi **karar kartı** — üç tanığın ne dediği + sade Türkçe gerekçe
- **Parite seçimi:** BTC min emri (375,6 TRY) çok büyük → **XRP / DOGE / SOL** ile çalışılacak, granülarite iyi

## Zaman kalırsa (opsiyonel, çekirdek değil)
"Boşta Para Çalışmaz" (B): fırsat yokken parayı `okx-cex-earn` ile faize park etme.

---

# 3.6 DIŞ REHBERDEN ALINANLAR (13:40)

Osman bir hazırlık rehberi paylaştı. **Uyarı: o rehber eski/yanlış kriter tablosuna dayanıyor**
("%35 performans, %25 mimari"). Stratejik tavsiyeleri bu yüzden ters teper — ama iki teknik kazanım var.

## ✅ Alınanlar (mimariye girdi)

**1. Emirle birlikte TP/SL — risk borsada, agent'ta değil** ⭐ en büyük kazanım
```bash
okx spot place --instId XRP-TRY --side buy --ordType market --sz 3 \
  --tpTriggerPx <hedef> --tpOrdPx=-1 \
  --slTriggerPx <stop>  --slOrdPx=-1 \
  --clOrdId agent-20260912-001
```
Stop-loss agent'ın içinde değil borsanın içinde durur. Laptop kapansa, wifi gitse,
agent çökse bile **stop çalışır.** → Sistem Güvenilirliği %10'un tam karşılığı.
**Mentor cevabı:** *"Ajan çökerse ne olur?" → "Hiçbir şey. Riskim agent'a değil borsaya emanet."*

**2. `--clOrdId` (idempotency)** — ağ hatasında aynı emir iki kez gitmez.

**3. "Evaluate" fazı** — döngümüzde yoktu. Artık var: her tur, bir önceki kararın sonucunu değerlendirir.
`Sense → Reason → Act → Evaluate` (sunum sözlüğü olarak da kullanılacak).

**4. İnsan-okur karar defteri** — `logs/decisions.md`. `journal.jsonl` makine için, bu insan için.
Arayüzün (%30 UX) ham maddesi.

**5. Somut başlangıç sayıları** — `config.yaml`'a işlendi:
max pozisyon %15 · max 2 açık pozisyon · günlük kayıp %3 → Safe Mode · RSI 35/65 · EMA20 · 15m · döngü 180 sn

## ❌ Reddedilenler (gerekçeli)

| Tavsiye | Neden reddedildi |
|---|---|
| "3-4 skill yeterli, smartmoney/sentiment opsiyonel" | Yanlış kriterden doğmuş. Derinlik %20 + özgünlük %10 = **%30 puan yakar** |
| LangChain / LiteLLM kur | Gereksiz katman, ~1 saat yakar. Claude Code + skills + CLI zaten çalışıyor |
| BTC/USDT, ETH/USDT odağı | BTC min emri 375,6 TRY = sermayenin %26'sı. Ölçüldü (Adım 2) |
| SL %0.8 gibi dar stop | Gidiş-dönüş komisyon %0.18 → zarar bütçesinin %22'si komisyona gider. **SL %1.2'ye çekildi** |
| 3 dk döngüde işlem | Tarama 3 dk olabilir ama **işlem** seyrek olmalı. Üç Tanık kuralı bunu zaten sağlıyor |

## ⚠️ Çözülmemiş çelişki
Rehber "%35 performans / %25 mimari" diyor ve Komünite'yi kaynak gösteriyor.
Osman yönergeden "%30/%30/%20/%10/%10" teyit etti. **İkisi aynı anda doğru olamaz.**
Osman'ın teyidi esas alındı. Mentor turunda 30 saniyede sorulmalı.

---

# 4. YOL HARİTASI

| # | Adım | Durum | Süre |
|---|---|---|---|
| 1 | ATK kurulumu + kimlik doğrulama | ✅ | 45 dk |
| 2 | Envanter: pariteler, min emir, komisyon, tool listesi | ✅ | 15 dk |
| 3 | **Ürün kararı** (İşlevsel Fayda %30) | ✅ | 20 dk |
| 4 | Agent çekirdeği — otonom döngü | ✅ | 50 dk |
| 5 | Risk kapısı + Safe Mode + eşik kalibrasyonu | ✅ | 30 dk |
| 6 | Demo emir testi | ✅ | 20 dk |
| 7 | ~~LLM katmanı~~ | ⛔ **terk edildi** | 50 dk yakıldı |
| 8 | Arayüz — merkezinde reddetme kaydı | ⏳ **ŞİMDİ** | 60 dk |
| 9 | MCP üzerinden ATK erişimi (%20'lik kriter) | ✅ | 30 dk |
| 10 | Sürekli döngü + canlıya geçiş (1-2 emir) | ⬜ | 20 dk |
| 11 | README + metrik + video + sunum | ⬜ | 60 dk |

> Adım 7-11, Adım 1-6'yı **revize etmiyor** — hiçbir kod geri alınmıyor.
> Eski plandaki "Adım 7 Arayüz" ikiye bölündü (LLM + arayüz), MCP opsiyonelden gerçek adıma terfi etti.
> LLM bir **ekleme**: çökse bile agent deterministik olarak çalışmaya devam eder.

---

# 5. YAPILAN İŞ (detay)

## Adım 1 — Kurulum ✅

| | İş | Sonuç |
|---|---|---|
| 1a | `npm i -g @okx_ai/okx-trade-cli` | v1.4.6 |
| 1b | `npx skills add okx/agent-skills` | 10 skill → `.agents/skills/` + Claude Code symlink |
| 1c | `claude mcp add ... okx-agent-trade-kit` | `~/.claude.json`'a kayıtlı |
| 1d | `okx config init` | profil `okx-demo`, site **tr.okx.com**, demo modu |
| 1e | Proje iskeleti | `.gitignore`, `.env`, `.env.example`, `config.yaml`, `src/`, `logs/` |

**Bağlantı kanıtı** — `okx account balance`:
`Environment: demo (simulated trading)` → TRY 200.000 · USDT 5.000 · BTC 1 · ETH 1 · OKB 100

**Kurulu skill'ler:** okx-cex-auth · okx-cex-market · okx-cex-trade · okx-cex-portfolio ·
okx-cex-bot · okx-cex-earn · okx-cex-smartmoney · okx-sentiment-tracker · okx-cex-skill-mp · earn-hunter

> `earn-hunter` = OKX'in kendi referans agent'ı. Config + scheduler + bildirim kanalları +
> mesaj şablonları içeriyor. Bizim agent'ı aynı iskelette kurmak ATK derinliği puanını taşıyor.

## Adım 2 — Envanter ✅ (salt-okunur, emir gönderilmedi)

- **166 tool / 18 modül** (`okx list-tools`) — "160+ MCP tool" ifadesi doğrulandı
- Spot: **1416 parite** (TRY bazlı **129**, USDT bazlı 404)
- Komisyon Lv1: maker **%0.08** · taker **%0.10** → gidiş-dönüş ~**%0.18**
- Kur: USDT-TRY **48,541** → **$30 = 1456 TRY**

**Minimum emir eşikleri (13:10 ölçümü):**

| Parite | minSz | Fiyat (TRY) | Min tutar |
|---|---|---|---|
| BTC-TRY | 0.0001 | 3.756.442 | **375,6 TRY** |
| ETH-TRY | 0.001 | 122.833 | 122,8 TRY |
| OKB-TRY | 0.01 | 5.537 | 55,4 TRY |
| SOL-TRY | 0.01 | 4.953,9 | 49,5 TRY |
| DOGE-TRY | 10 | 4,119 | 41,2 TRY |
| XRP-TRY | 0.1 | 66,5 | **6,7 TRY** |

## Adım 3 — Ürün kararı ✅ (bkz. Bölüm 3.5)

## Adım 4 — Agent çekirdeği ✅ (14:30)

### Yol boyunca çıkan 3 ölçüm — tasarımı değiştirdiler

**1. TRY pariteleri kullanılamaz.** (14:00)
- `okx market indicator rsi XRP-TRY` → **boş döner**. `XRP-USDT` → RSI 70.36 ✅
- TRY pariteleri sığ: XRP-TRY 15dk hacimleri 0 / 3.49 / 21.49
- Min emir: BTC-TRY **$7,70** vs BTC-USDT **$0,77**
→ Evren **USDT paritelerine** çevrildi. *(Dış rehber bu konuda haklıymış, ben yanlış reddetmiştim.)*

**2. İki tanık demo modda çalışmıyor.** (14:20)
- `news` → *"News features are not available in demo/simulated trading mode."*
- `smartmoney signal-overview` → demo'da boş liste
→ Çözüm: ana hesapta **salt-okunur canlı API key** (`okx-prod`). İşlem yetkisi YOK, çekim yetkisi YOK.
→ Ortaya güzel bir mimari çıktı: **istihbarat canlı piyasadan, icra demo hesapta.**
→ ⚠️ `okx config init` default profili canlıya kaydırdı, elle `okx-demo`'ya geri alındı.

**3. Canlı bakiye doğrulandı.** (14:35) — salt-okunur key ile, sıfır risk:
`USDT 30 · equity 30 · available 30 · frozen 0` — **işlem hesabında**, fonlama hesabında değil (transfer gerekmiyor).
→ Sanal tavan `30` doğru. Artık [Varsayım] değil **[Kesin]**.

### Sermaye matematiği
```
Demo gercek bakiye : 5.000 USDT (sahte)
  -> sanal tavan     :    30 USDT  (canlidaki gercek rakam)
  -> pozisyon %15    :   4,5 USDT
  -> max 2 pozisyon  :     9 USDT riskte, 21 USDT bosta
```
Min emirler (BTC $0,77 · ETH $0,25 · SOL $1,02 · XRP $1,37 · DOGE $0,85) → 4,5 USDT hepsini geçiyor.
**Adım 2'deki "BTC kullanılamaz" riski kapandı.**

### Yazılan dosyalar
| Dosya | Ne yapar |
|---|---|
| `src/okx.py` | ATK CLI sarmalayıcı. Profil yönlendirmesi tek yerde |
| `src/witnesses.py` | Üç tanık. Ulaşılamayan tanık `unknown` döner — çökmez, ama işlemi de engeller |
| `src/risk.py` | Risk kapısı (saf fonksiyon, ağa çıkmaz) + borsa-tarafı TP/SL hesabı |
| `src/journal.py` | İki defter: `journal.jsonl` (makine) + `decisions.md` (insan) |
| `src/agent.py` | Sense → Reason → Act → Evaluate döngüsü |

### İlk çalışma çıktısı
```
Agent basladi - profil=okx-demo · KURU CALISMA
[14:27:40] bakiye=30.00 USDT
  BTC-USDT   -> wait  (2/3 tanik)
  ETH-USDT   -> wait  (1/3 tanik)
  SOL-USDT   -> wait  (1/3 tanik)
  XRP-USDT   -> wait  (1/3 tanik)
  DOGE-USDT  -> wait  (1/3 tanik)
```

### Karar kartı örneği (arayüzün ham maddesi)
> **⏸️ 14:27:43 — ETH-USDT — BEKLEDİ**
> - **teknik** ⏸️: RSI 64.0 nötr bölgede, fiyat EMA20'in üstünde.
> - **akıllı para** 🟢: Başarılı traderların %95'i alış yönünde (21 alıcı / 7 satıcı).
> - **duygu** 🟢: Haber akışı olumlu (pozitif 0.47 / negatif 0.12, 761 haber).

## Adım 5 — Risk kapısı + uzlaşı kalibrasyonu ✅ (15:08)

### Ölçüm: sayılar keyfi miydi? Evet — düzeltildi
Osman "neden 5 parite, neden 3 dakika?" diye sordu. Dürüst cevap: dış rehberden alınmış, ölçülmemişti.
Ölçünce **gerçek sınır** çıktı:

| Ölçüm | Sonuç |
|---|---|
| `smartmoney` kapsamı | 20 enstrüman — ama 12'si hisse token'ı (XAU, ORCL, MU, SOXL...) |
| Spot-USDT olarak işlem görebilenler | **8** → BTC, ETH, SOL, XRP, DOGE, ZEC, OKB, ORDI |
| Tur süresi | 5 parite 14 sn · 20 parite 49 sn · 160 parite **381 sn** (döngüden uzun) |
| LLM maliyeti | **Sıfır** — sistem şu an tamamen deterministik script |

→ **Evren 5'ten 8'e çıkarıldı.** Üst sınır bizim tercihimiz değil, `smartmoney` kapsamının dayattığı sınır:
9. bir parite eklense o paritede 2. tanık hep `unknown` döner, uzlaşı hiç sağlanamaz.
→ **Döngü 3 dk kaldı**, ama gerekçesi düzeltildi: 15dk mumla çalışıyoruz, her 3 dk'da yeni teknik sinyal
YOK. 3 dk'nın gerekçesi açık pozisyon takibi + haber akışı.

### Uzlaşı kuralı gevşetildi
3/3 oybirliği ölçüldü ve **hiç tetiklenmedi** (en iyi uyum 2/3) → agent hiç işlem yapmıyordu.
Yeni kural: **en az 2 onay + hiçbir tanık karşı çıkmasın.** Veto hakkı korunuyor — tek karşı oy işlemi öldürür.
`wait` nötr, `unknown` kayda geçer ama engellemez (`block_on_unknown` ile açılabilir).

### Bulunan ve düzeltilen hata
İlk çalıştırmada **5 emir birden hazırlandı** — limit 2 olmasına rağmen. Sebep: `open_positions`
sayacı tur içinde artmıyordu, limit sadece turlar arasında işliyordu. Canlıda 5 pozisyon açardı.
→ `src/state.py` eklendi: agent'ın kendi açtığı pozisyonlar `logs/state.json`'da tutuluyor,
emir verilir verilmez sayaç artıyor.
> Neden bakiyeden saymıyoruz: demo hesap BTC/ETH/OKB ile önceden dolu — agent hiçbir şey yapmadan
> 3 pozisyon görünürdü.

### Safe Mode
Günlük kayıp limiti (%3) aşılırsa `safe_mode` **kalıcı olarak** açılıyor (`state.json`), yeniden başlatma
onu sıfırlamıyor. Sadece insan eliyle temizlenebilir.
**Karar:** Safe Mode = *yeni işlem açma*, mevcut pozisyonları kapatma. Zararda kapatmak zararı kalıcı yapar;
borsa tarafındaki stop-loss zaten görevini yapar.

### Doğrulanmış çalışma (15:06)
```
[15:06:30] bakiye=30.00 USDT · acik=0 · gunluk=+0.00%
ETH-USDT   buy   emir 4.5 USDT
SOL-USDT   buy   emir 4.5 USDT
XRP-USDT   veto  Ayni anda en fazla 2 acik pozisyon olabilir (su an 2).
ZEC-USDT   veto  Ayni anda en fazla 2 acik pozisyon olabilir (su an 2).
OKB-USDT   veto  Ayni anda en fazla 2 acik pozisyon olabilir (su an 2).
ORDI-USDT  veto  Ayni anda en fazla 2 acik pozisyon olabilir (su an 2).
```
Ayrıca ZEC-USDT bir önceki turda min emir tutarı yüzünden veto edilmişti
(*"4.50 < 11.50"*) — kapının ikinci kuralı da sahada doğrulandı.

## Adım 6 — Demo hesapta gerçek emir ✅ (15:18)

`dry_run: false` → agent demo borsaya **gerçek emir** gönderdi. Canlı $30'a dokunulmadı.

### İki hata bulundu ve düzeltildi

**1. `shell=True` → cmd.exe argümanları bozuyordu.**
`cmd.exe` `=` karakterini ayraç sayıyor; `--tpOrdPx=-1` parçalanıyordu.
→ `shell=False` + `shutil.which("okx")` ile çözüldü.

**2. Teşhis körlüğü: hata mesajı görünmüyordu.**
Sarmalayıcı sadece `stderr` okuyordu, ama CLI hatayı `stdout`'a yazıyor. İlk hata
"exit 1: " diye boş göründü. → stdout da yakalanıyor. **Bu düzeltme asıl hatayı ortaya çıkardı:**

**3. `clOrdId` içinde tire kabul edilmiyor.**
`agent-1789215275` → `sCode 51000 "Parameter clOrdId error"`.
Dokümantasyon `-` ve `_` serbest diyor; **OKX TR pratikte reddediyor.** Doküman ile gerçek uyuşmuyor.
→ Sadece harf-rakam: `agent1789215275`.

### Sonuç — borsada doğrulandı
```
algoId               instId    type  side  sz        tpTrigger  slTrigger  state
3916237560309260288  SOL-USDT  oco   sell  0.044003  104.19     100.92     live
3916237404549586944  ETH-USDT  oco   sell  0.001774  2584.09    2503.02    live
```
**`oco` = One-Cancels-Other, `state: live`** — kâr-al ve zarar-kes emirleri borsanın içinde bekliyor.
Agent kapansa, laptop kapansa, elektrik gitse bile çalışırlar.
→ Mimarinin en kritik iddiası (**risk borsada, agent'ta değil**) sahada kanıtlandı.

Bakiye değişimi: USDT 5000 → 4977,51 · ETH 1 → 1,007094 · SOL 0 → 0,044004
(ETH ve SOL'un bir kısmı `frozen` — algo emirleri tutuyor.)

## Adım 7 — LLM katmanı ⛔ TERK EDİLDİ (16:05) — **50 dakika boşa gitti**

Dürüst kayıt: bu adım başarısız oldu ve **hiçbir kazanım üretmedi.**

### Ne denendi
`claude -p` başsız modda LLM olarak kullanılacaktı (ayrı API key gerekmiyor, mevcut abonelik).
İki iş verilecekti: (1) Türkçe hedefi `config.yaml` değerlerine çevirmek, (2) kararları insan diline çevirmek.
`src/llm.py` yazıldı — **kod duruyor, `enabled: false`.**

### Neden battı — üst üste 4 tuzak
| Tuzak | Bulgu |
|---|---|
| 16 MCP server her çağrıda yükleniyordu | 91 sn → `--strict-mcp-config` + boş config ile 5 sn |
| Proje klasöründe çalışınca **kod asistanı** gibi davranıyor | `CLAUDE.md` ve `agent.py`'yi okuyup benim koduma denetim yazdı, prompt'u cevaplamadı. 105 sn, alakasız cevap |
| Uzun/şablonlu prompt modeli uzun düşündürüyor | 45 sn zaman aşımına takılıyordu |
| **Bir `sed` düzeltmesi sessizce uygulanmadı** | Eski prompt ve eski zaman aşımı dosyada kaldı; ben düzelttim sanıp test ettim. **Asıl körlük buydu.** |

### Gerçek hata — benim hatam
Yanlış varsayımla başladım: *"agentic hackathon → LLM şart."*
**Rubrikte LLM geçmiyor.** Kriterlerin hiçbiri LLM istemiyor; %20'lik kriter **MCP** diyor.
Bunu 50 dakika sonra fark ettim. O 50 dakika MCP'ye gitmeliydi.

### Ortaya çıkan olumlu taraf
Terk etme kararı sunumda savunulabilir bir pozisyona dönüştü:
> *"Karar yoluna bilerek LLM koymadım. Üç tanık deterministik, risk kapısı deterministik,
> stop-loss borsada. Sistemin hiçbir yerinde halüsinasyon görebilecek bileşen yok."*

Bu, **Sistem Güvenilirliği** kriterinde artı. Ama bu bir telafi, planlanmış bir tasarım değil — kayda böyle geçsin.

---

## Adım 9 — MCP entegrasyonu ✅ (16:48) — %20'lik kriterin karşılığı

Agent artık **CLI sarmalayıcı değil, MCP istemcisi.** Tüm ATK erişimi MCP tool çağrısı.

### Kurulum yolunda çıkanlar
| Engel | Çözüm |
|---|---|
| `okx setup --client claude-code` patladı (`spawnSync claude ENOENT`) | `claude mcp add` komutu elle çalıştırıldı |
| `okx-trade-mcp` ikilisi yok | Ayrı paket: `npm i -g @okx_ai/okx-trade-mcp` |
| HTTP server OAuth istiyordu | **Gerek kalmadı** — yerel stdio server kendi API key profillerimizi kullanıyor |

### Kurulan yapı
```
okx-trade-mcp-demo   --profile okx-demo --modules all   -> emir, bakiye
okx-trade-mcp-intel  --profile okx-prod --modules all   -> akilli para, haber (salt-okunur)
```
`src/mcp.py` — **130 satır, sıfır bağımlılık**, JSON-RPC over stdio. Kalıcı oturum, ölürse yeniden başlatır.

### Ölçülen değerler
| Ölçüm | Sonuç |
|---|---|
| MCP tool sayısı | **168** |
| 3 kaynak tek seferde (bakiye + gösterge + haber) | **2,4 sn** |
| Tur süresi CLI ile | 31 sn |
| **Tur süresi MCP ile** | **18 sn** — %42 hızlanma |
| Sebep | CLI her çağrıda yeni süreç açıyordu; MCP oturumu kalıcı |

### Kullanılan tool'lar
`market_get_indicator` · `market_get_ticker` · `market_get_instruments` ·
`account_get_balance` · `smartmoney_get_signal_overview_by_filter` ·
`news_get_coin_sentiment` · `spot_place_order`

### Doğrulama — MCP ile verilen emirler borsada
```
3916298328056700929  SOL-USDT  oco  sell  0.043964  tp=104.27   sl=101      live
3916298243499532288  ETH-USDT  oco  sell  0.001773  tp=2585.38  sl=2504.27  live
```

## Adım 8 — Arayüz ✅ (16:35)

`src/dashboard.py` → **http://localhost:8787** · sadece Python standart kütüphanesi,
sıfır bağımlılık, build yok. Agent'ın yazdığı `journal.jsonl`'i okur — kopyası değil, aslı.

### Merkezde ne var
"Yapılan işlemler" değil, **"reddedilen işlemler ve sebepleri"**. Ürünün tezi bu.

### Yol boyunca bulunan kusur — reddetme kaydı tekdüzeydi
Osman işaret etti: 14 reddin 14'ü de aynı cümleydi (*"en fazla 2 açık pozisyon"*).
Bu 14 ayrı yargı değil, **tek kuralın 14 tekrarı**. Jüri "ajan düşünüyor" değil "ajan tıkanmış" görür.
3 saatlik çalışmada ~500 satır aynı cümle olurdu.

**İki düzeltme:**
1. **Panel redleri sebebe göre gruplar.** "Hangi kural kaç kez devreye girdi" bölümü +
   `devreye giren kural` sayacı. Bir kuralın 200 kez ateşlenmesi 200 yargı değildir.
2. **Pozisyon küçültüldü, sayı artırıldı** — daha çok parite aynı anda çalışsın diye:

| | Önce | Sonra |
|---|---|---|
| Pozisyon | %15 = 4,5 USDT | **%10 = 3 USDT** |
| Max açık pozisyon | 2 | **4** |
| Aynı anda çalışan parite | 2/8 | **4/8** |

> Not: bu değişiklik **puan için değil, çeşitlilik için**. Performans puanlanmıyor.
> Yan fayda: ZEC'in min emri 11,50 USDT — 3 USDT'lik pozisyonla artık *farklı bir sebeple*
> reddedilecek. Reddetme kaydı böylece gerçekten çeşitlenir.

### Ayrıca eklenen: pozisyon mutabakatı
Agent açtığı pozisyonu hiç kapatmıyordu — TP/SL borsada gerçekleşse bile `state.json`'da
"açık" kalıyordu. Saatlerce çalışacak döngüde ölümcül: limit dolunca sonsuza kadar veto ederdi.
→ `_reconcile()` her turda `spot_get_algo_orders` ile borsayı sorguluyor, kapanmış pozisyonu düşüyor.
Sorgu başarısız olursa **hiçbir şey değiştirmiyor** — bir pozisyonun kapandığını asla tahmin etmiyor.

## 🔴 DONMA — bulundu ve çözüldü (16:44)

Osman fark etti: *"En son 15:46'da işlem yapılmış, saat 16:43!"* **Haklıydı — ajan 57 dakika donmuştu.**

### Teşhis — üç ayrı hata üst üste
| # | Hata | Etki |
|---|---|---|
| 1 | **Config sadece başlangıçta okunuyordu** | %10/4-pozisyon ayarı hiç uygulanmadı. Çalışan süreç hâlâ %15/2 kullanıyordu — "9 USDT'yi 12 yaptım" dediğim şey **hiç olmadı** |
| 2 | **Kâr-al/zarar-kes çok genişti** (+%2 / −%1,2) | 15 dakikalık mumda 57 dakika boyunca hiç tetiklenmedi → pozisyonlar hiç kapanmadı |
| 3 | **Slot boşalmayınca ajan tıkandı** | 2 pozisyon doldu, sonraki her tur sadece aynı reddi üretti. 32 reddin 32'si aynı cümle |

### Çözüm — üç düzeltme
1. **Config her turda yeniden okunuyor** — `config.yaml` düzenlemesi çalışan ajana anında geçiyor
2. **Bantlar daraltıldı:** TP +%0,8 / SL −%0,5 (komisyon %0,18 düşünce net +%0,62 / −%0,68)
3. **Zaman stopu eklendi** (`max_position_minutes: 20`) — bant tetiklenmezse ajan pozisyonu
   **kendisi kapatır**: algo emrini iptal eder, piyasa fiyatından satar, deftere yazar.
   Donma artık yapısal olarak imkansız.

### Sonuç — ölçülmüş
| | 16:43 (donmuş) | 16:45 (düzeltilmiş) |
|---|---|---|
| İşlem | 2 | **6** |
| Hacim | 9,00 USDT | **21,00 USDT** |
| Açık pozisyon | 2 (57 dk kıpırdamadı) | **4** |
| **Farklı red sebebi** | **1** | **3** |

Reddetme kaydı artık tekdüze değil:
```
41x  Ayni anda en fazla 2 acik pozisyon olabilir      <- donma donemi
 1x  Pozisyon buyuklugu (3.00) minimum emrin (11.55) altinda   <- ZEC
 1x  Ayni anda en fazla 4 acik pozisyon olabilir       <- yeni limit
```

## 🔴 SERMAYE HESABI HATASI — bulundu ve çözüldü (16:58)

Osman bir dış rehber paylaştı; içindeki *"toplam harcama 30 USDT'yi aşarsa yeni alımı engelle"*
kontrolü **gerçek bir hatayı** ortaya çıkardı.

**Hata:** Ajan kullanılabilir sermayeyi `min(gercek_bakiye, 30)` diye hesaplıyordu.
Demo hesapta gerçek bakiye ~4900 USDT olduğu için sonuç **her zaman 30** çıkıyordu — 12 USDT
zaten dağıtılmış olsa bile. Canlıda ise bakiye gerçekten düşer (30 → 18) ve pozisyon boyutu
küçülür. **Yani demo ile canlı farklı davranıyordu** — sanal tavanın tek amacı buydu ve delikti.

**Çözüm:** `min(gercek_bakiye, tavan − dagitilmis)`. Doğrulama:
```
bakiye=21.00 USDT · dagitilmis=9.00 · acik=3     -> 21 + 9 = 30 ✓
```
Artık sermaye azaldıkça pozisyon da küçülüyor (3,00 → 2,29 USDT) — canlıdaki davranışın aynısı.

## 🔴 SAHTE HACİM — bulundu ve çözüldü (17:07)

Osman "38 işlem" sayısından şüphelendi. **Haklıydı: işlemlerin çoğu gerçek karar değil, döngüydü.**

**Teşhis:** Aynı 4 parite her turda yeniden alınıyordu —
`16:58 ETH,SOL,XRP,OKB` → `17:00 ETH,SOL,XRP,OKB` → `17:04 ETH,SOL,XRP,OKB`.
Yerel `state.json` ile borsa arasında sapma vardı; ajan pozisyonu "kapandı" sanıp yeniden alıyordu.
Borsada **27 açık OCO emri** birikmişti, sadece 3 paritede.

**Çözüm:** Yerel dosyaya güvenme — **borsaya sor.** Her turda `spot_get_algo_orders` ile
canlı emri olan pariteler okunuyor; o paritelere ikinci kez girilmiyor.
> Yerel durum dosyası kayabilir (çökme, yarış, elle çalıştırma). Borsa kayamaz.

**Sonuç — tek turda 4 farklı red sebebi:**
```
ETH-USDT   veto  borsada zaten acik pozisyon var, ikinci kez girilmez
SOL-USDT   veto  borsada zaten acik pozisyon var
XRP-USDT   veto  borsada zaten acik pozisyon var
ZEC-USDT   veto  pozisyon buyuklugu (2.29) minimum emrin (11.52) altinda
ORDI-USDT  veto  ayni anda en fazla 4 acik pozisyon
OKB-USDT   buy   emir 2.29 USDT
```

## Dış rehber değerlendirmesi (17:00) — ölçümle, iddiayla değil

| Rehberin iddiası | Verdict |
|---|---|
| "Sermaye sınırı kontrolü koy" | ✅ **HAKLI** — gerçek hata yakalandı (yukarıda) |
| "Min emir çoğu paritede 5-10 USDT, 3 USDT'lik emir hata verir" | ❌ **YANLIŞ** — ölçüldü: ETH 0,25 · ORDI 0,41 · BTC 0,77 · DOGE 0,85 · SOL 1,02 · OKB 1,14 · XRP 1,37 · ZEC 11,52. 3 USDT'lik emirler borsada `filled` |
| "İşlem başına 12 USDT, max 2 pozisyon" | ❌ Yanlış min-emir varsayımına dayanıyor |
| `okx config set --env production` | ❌ **Böyle bir komut yok.** `okx config set` var, `--env` bayrağı yok |
| "Ana hesabın key'ini ajana verme" | ✅ Zaten öyle — işlem key'i sub-account'ta, ana hesaptaki salt-okunur |
| "1.000.000 dakika hatası" | 🟡 Hata değil, zaman damgasız eski kayıtlar için işaret değeriydi. Yine de ekranda bozuk göründüğü için düzeltildi |
| IP kısıtlaması ekle | 🟡 Bilinçli takas: etkinlik ağında IP değişirse key ölür |

## 🔴🔴 EN CİDDİ HATA — defter olmayan işlemleri kaydediyordu (17:30)

Osman bir dış analiz paylaştı: *"OKB sürekli alınıyor, pozisyon sayacı deliniyor."*
Sonuç doğruydu, **sebep tamamen başkaydı** — ve kovalarken çok daha kötü bir şey çıktı.

### Ne oldu
`mcp.py` sarmalayıcı, OKX'in **reddettiği** emirleri başarı sayıyordu.
OKX reddi HTTP 200 içinde `sCode` alanıyla bildiriyor:
```
sCode 51155 — "You can't trade this pair due to local compliance restrictions"
```
Kod bu alanı **hiç okumuyordu**. Borsa emri reddediyor, defter "alım yapıldı" yazıyordu.

**Ürünün tek iddiası "defterime güvenin" — ve defter uyduruyordu.** Günün en tehlikeli hatası,
çünkü sessizdi: hiçbir şey patlamıyor, hiçbir hata mesajı çıkmıyordu.

### Ölçülen kirlilik
| | |
|---|---|
| Toplam "işlem" kaydı | 47 |
| **Hayalet (borsa reddetti)** | **15 — %32** |
| Hayalet hacim | 38,31 USDT |
| Gerçek hacim | 91,71 USDT (ETH / SOL / XRP) |

### İkinci bulgu: koruma emri sessizce oluşmuyor
OKB ve ORDI'de OKX emri **kabul ediyor** ama kâr-al/zarar-kes emrini oluşturmuyor.
Koruma emri olmayınca ajan "pozisyon kapanmış" sanıp yeniden alıyordu — döngünün asıl sebebi buydu.
Ve o pozisyonlar **stop-loss'suz** duruyordu: `require_stop_loss: true` kuralı sessizce deliniyordu.

### Üç düzeltme
1. **Her MCP cevabında `sCode` doğrulanıyor.** Sıfır değilse hata; deftere borsanın kendi
   mesajıyla "reddedildi" olarak yazılıyor.
2. **Emirden sonra koruma emri doğrulanıyor.** Borsada canlı algo emri yoksa pozisyon
   **anında geri alınıyor** ve parite oturum boyunca kapatılıyor.
   Gözlenen çıktı: `OKB-USDT KORUMASIZ — geri alindi, parite kapatildi`
3. **Defter karantinaya alındı** → `logs/archive/` + `NEDEN.md`.
   Teslim metrikleri **yalnızca 17:36 sonrasını** kapsar. Eski defter silinmedi — hata da kayıttır.

### Sunum için kazanç
> *"Ajanım bir pozisyon açtı, borsanın koruma emrini oluşturmadığını fark etti, pozisyonu
> kendi kendine geri aldı ve o pariteyi kapattı. Stop-loss'suz pozisyon yasak — ve bu yasağı
> ajan kendisi uyguladı."*

**Not — ZEC listede kalıyor.** Dış analiz "çıkar" dedi; katılmıyorum: her turda
*"minimum emir tutarının altında"* diye reddedilmesi kuralın çalıştığının kanıtı. Gösterilecek şey.

## 🌐 GERÇEK AĞ KESİNTİSİ — planlanmamış saha testi (17:58–18:04)

Osman etkinlikten çıktı, ağ koptu. **OKX API'si 6 dakika erişilemez kaldı.**
Bu, senaryo değil — gerçekten yaşanmış bir dayanıklılık testi ve iki şey ortaya çıkardı.

### ✅ Doğru çalışan
| Davranış | Kanıt |
|---|---|
| Körlemesine işlem yapmadı | 6 dakika boyunca her parite `BEKLEDI`, üç tanık da `?` |
| Çökmedi | Döngü kesintisiz devam etti, ağ gelince normale döndü |
| Kesintiyi bile kaydetti | Her başarısız tur, borsanın kendi hata mesajıyla deftere yazıldı |
| Kesinti sonrası toparladı | Kapatılamayan pozisyonlar 18–25 dk'ya uzadı, ağ gelir gelmez zaman stopu üçünü de kapattı |

Ayrıca 17:39'da **OKX'ten HTTP 502** geldi — ajan onu da atlattı.

### 🔴 Hatalı çalışan — canlıda felaket olurdu
```
⛔ Safe Mode aktif — gunluk kayip limiti asilmisti, yeni islem yok.
```
**Ama hiçbir kayıp yaşanmamıştı.** Bakiye okunamayınca kod bunu `0.0` saydı →
30 → 0 = **%100 kayıp** hesapladı → günlük %3 limiti aştı → Safe Mode **kalıcı** kilitlendi.

**Ajan, ağ kesintisini iflas sanıp kendini kapattı.**
Canlıda bu, ilk ağ hıçkırığında ajanın günün geri kalanında ölmesi demekti.

### Düzeltme — tek cümlelik kural: *ölçemediğin şeyi kayıp sayma*
| Önce | Sonra |
|---|---|
| Bakiye okunamazsa `0.0` döner | `None` döner — **bilinmiyor**, sıfır değil |
| `0.0` → %100 kayıp → Safe Mode kilitlenir | Bilinmiyorsa Safe Mode **hiç değerlendirilmez** |
| Risk kapısı sıfır bakiyeyle boyutlandırır | Yeni red gerekçesi: *"Bakiye okunamadı (ağ/API sorunu). Ölçülemeyen bakiyeyle işlem yapılmaz — bu bir kayıp değil, bilinmezliktir."* |

Sahte Safe Mode `state.json`'dan temizlendi, ajan 18:10'da yeniden başlatıldı.

### Sunum değeri
Bu, anlatılacak en iyi hikâye — **çünkü uydurma değil, logda duruyor:**
> *"OKX API'si altı dakika kesildi. Ajanım tek işlem yapmadı: üç tanık da veri döndüremiyordu
> ve kuralım 'veri yoksa işlem yok' diyor. Ağ gelince kendi kendine devam etti. Ama bir hata
> da yaptı — bakiyeyi okuyamayınca sıfır sanıp kendini kapattı. Onu da düzelttim."*

## 🟢 CANLIYA GEÇİŞ ✅ — gözetimli, 2 tur (18:29–18:30)

Osman'ın açık onayıyla. Sürekli döngü DEĞİL — iki tek tur, her turdan sonra borsadan doğrulama.

### Hazırlık
- Sub-account'ta Okuma+Al-Sat izinli yeni key (Para Çekme yok, IP kısıtı yok, 9 kripto: USDT + 8 parite)
- CLI tek profil adı dayattığı için `okx-prod` (salt-okunur) **üzerine yazıldı** → istihbarat/işlem ayrımı
  garantisi canlıda kalktı. Davranış değişmedi (istihbarat çağrıları zaten salt-okuma). Kayda geçti.
- `okx config init` default'u yine canlıya kaydırdı → `okx-demo`'ya geri alındı (3. kez, artık refleks)
- Demo durumu arşivlendi, canlı için temiz `state.json`, **ayrı defter**: `logs/journal.live.jsonl`

### Tur 1 — 18:29 — 4 gerçek emir
```
ETH-USDT  buy  2.4 USDT  tp=2561.43  sl=2528.40
SOL-USDT  buy  2.4 USDT  tp=102.88   sl=101.55
XRP-USDT  buy  2.4 USDT  tp=1.3823   sl=1.3645
OKB-USDT  buy  2.4 USDT  tp=115.27   sl=113.78
ORDI-USDT veto "en fazla 4 acik pozisyon"
```
Boyut 2,4 = 30 × %80 (nakit tamponu) × %10. **Demo ile birebir aynı matematik.**

### Borsadan üç bağımsız doğrulama (deftere değil, borsaya inandık)
| Kanıt | Sonuç |
|---|---|
| `spot algo orders` | **4 OCO `live`** — OKB dahil (canlıda bracket oluşuyor, demo'da oluşmuyordu) |
| `spot fills` | 4 alım, 18:29:09–18:29:22, komisyon kesilmiş |
| `account balance` | USDT **20,40** = 30 − 4×2,4 kuruşuna kadar; 4 varlık `frozen` (OCO tutuyor) |

### Dördüncü doğrulama — OKX'in kendi web arayüzü (18:35, Osman'ın ekran görüntüsü)
`tr.okx.com → Emir Merkezi → Emir Geçmişi`: ETH/SOL/XRP/OKB, Satın Al, Piyasa, 2,4 USDT, 18:29:09–18:29:22,
komisyonlar düşülmüş. Ajanın defteri ≡ MCP cevabı ≡ CLI ≡ borsa web sitesi. **Dört kaynak, tek gerçek.**

### Tur 2 — 18:30 — sıfır emir, 5 red (canlı deftere red kaydı girsin diye)
4× *"borsada zaten açık pozisyon var"* + 1× *"en fazla 4 açık pozisyon"*. Hiç yeni emir gitmedi.

### Durum
- Canlı döngü **durduruldu**. Gözetimsiz canlı ajan yok.
- 4 canlı pozisyon **açık bırakıldı**, borsadaki OCO'larıyla korunuyor. Riskte 9,6 USDT;
  zarar-kes'lerin hepsi tetiklense kayıp ≈ **0,05 USDT**. Jüri 20:00'de canlı hesapta OCO'ları görebilir.
- Config ve state demo'ya geri alındı; demo ajanı 18:31'de yeniden başlatıldı, panel demo defterini gösteriyor.
- Canlı artefaktlar: `journal.live.jsonl` · `decisions.live.md` · `state.live.json` · `config.live.yaml`

## Adım 10 (kısmi) — Sürekli döngü ✅ (16:27, 18:10'da düzeltilmiş haliyle yeniden başlatıldı)

`python -u src/agent.py` arka planda, **3 dakikada bir tur**, kesintisiz.
Otonomi artık iddia değil, çalışan süreç. Çıktı `logs/agent.out`.

---

# 6. ALINAN KARARLAR

| Karar | Gerekçe |
|---|---|
| **ATK üzerine inşa**, ccxt yok | %20'lik ATK kriteri; ayrıca az kod, az bakım |
| **API key**, OAuth değil | OAuth ana hesaba bağlanır; API key sub-account'a kilitli |
| **İki profil: `demo` → `live`** | Kod değişmez, sadece `OKX_PROFILE`. Canlı para riske girmeden uçtan uca test |
| **USDT pariteleri**, TRY değil | TRY'de gösterge verisi yok + likidite sığ + min emir 10x büyük (ölçüldü 14:00) |
| **Sanal sermaye tavanı 30 USDT** | Demo'da 5000 USDT sahte para var. Tavan kâr için değil, **canlıdaki kırılma noktalarını bugün bulmak için**: 5000'de min emir kuralı hiç devreye girmez, 30'da girer |
| **İki profil: istihbarat canlı, icra demo** | `news` ve `smartmoney` demo'da kapalı. Salt-okunur canlı key ile açıldı — işlem yetkisi yok |
| **Tarama deterministik, LLM karar anında** | OKX'in önerisi; sıfır token + LLM çökse bile ayakta |
| **Risk kapısı `PreToolUse` hook** | LLM'i veto edebilen tek nokta; az kod, güçlü anlatı |
| **ML/DL modeli eğitilmeyecek** | Veri yok, backtest zamanı yok, ayrıca puanlanmıyor |
| **MCP, CLI'ın yerini aldı** | %20'lik kriter MCP diyor. Ayrıca %42 daha hızlı (kalıcı oturum) |
| **Karar yolunda LLM YOK** | Rubrikte LLM geçmiyor. Deterministik zincir = halüsinasyon riski sıfır |
| **MCP yerel stdio, OAuth değil** | Kendi API key profillerimizi kullanıyor, tarayıcı onayı gerekmiyor |

---

# 7. AÇIK RİSKLER

| Risk | Durum |
|---|---|
| 🔴 **AÇIK: 3/3 uzlaşma kuralı hiç tetiklenmiyor** | En iyi uyum 2/3. Agent bugün hiç işlem yapmayabilir → performans metrikleri boş kalır. **Adım 5'in ilk işi.** Öneri: "hiçbir tanık aksini söylemesin + en az 2 onaylasın" |
| ~~BTC-TRY min emri > pozisyon boyutu~~ | ✅ **KAPANDI** 14:35 — USDT paritelerine geçildi. 4,5 USDT pozisyon, tüm min emirleri (max $1,37) geçiyor |
| ~~Haber/akıllı para demo'da engelli~~ | ✅ **KAPANDI** 14:20 — salt-okunur canlı profil (`okx-prod`) eklendi |
| ~~Canlı bakiye doğrulanmadı~~ | ✅ **KAPANDI** 14:35 — 30 USDT, işlem hesabında, transfer gerekmiyor |
| MCP server OAuth ile **hangi hesabı** görüyor? | Henüz bağlanmadı. Şu an ATK'ya CLI üzerinden erişiyoruz (166 tool), MCP ayrıca bağlanacak |
| ⚠️ `okx config init` default profili kaydırıyor | İkinci profil eklenince default canlıya kaydı, elle geri alındı. **Her `config init` sonrası kontrol edilecek** |
| Demo API key'i sohbete düz metin sızdı | Demo key, gerçek risk yok. **Kural: `okx config show --json` canlı profille asla çalıştırılmayacak** |
| Etkinlik ağında IP değişirse key kırılır | Demo key'de IP kısıtlaması kaldırıldı ✅. Canlı key'de kontrol edilmeli |
| ~~Kriter listesi resmî PDF ile teyit edilmedi~~ | ✅ **KAPANDI** 13:30 — Osman resmî yönergeden teyit etti. 5. kriter "Sunum/Demo" değil **İnovasyon & Özgünlük** çıktı |
| Windows'ta `crontab` ve `jq` yok | Zamanlama Task Scheduler ya da Node/Python döngüsü ile yapılacak |

---

# 8. PROJE DOSYALARI

```
12.09.2026_Hackathon/
├── .agents/skills/     10 OKX skill (kurulu)
├── src/
│   ├── mcp.py          MCP istemcisi (168 tool) — ASIL YOL
│   ├── llm.py          LLM katmani — enabled: false, terk edildi
│   ├── state.py        acik pozisyon + Safe Mode kalicilig
│   ├── dashboard.py    arayuz (localhost:8787, sifir bagimlilik)
│   ├── okx.py          ATK CLI sarmalayici (yedek yol)
│   ├── witnesses.py    uc tanik
│   ├── risk.py         risk kapisi (veto yetkisi)
│   ├── journal.py      iki defter
│   └── agent.py        ana dongu
├── logs/
│   ├── journal.jsonl   makine okur
│   └── decisions.md    insan okur (UX ham maddesi)
├── config.yaml         sermaye tavanı, risk kuralları, döngü aralığı
├── .env / .env.example OKX_PROFILE + Telegram anahtarları
├── .gitignore          .env, logs/, node_modules
├── skills-lock.json    skill sürüm kilidi
└── PROGRESS.md         bu dosya
```

**Git:** Henüz repo değil. `git init` Adım 4'ten sonra yapılacak — git komutlarını ben (Osman) çalıştırıyorum, adım adım verilecek.
