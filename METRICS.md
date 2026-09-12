# EMANET — performans metrikleri

Üretildi: 12.09.2026 18:34 · `python src/metrics.py` · elle yazılmış sayı yok.

> Hesap getirisi bu yarışmada puanlanmıyor ve burada iddia edilmiyor. Ölçülen şey ajanın
> **karar kalitesi ve hesap verebilirliği**: kaç fırsat gördü, kaçını hangi kuralla reddetti,
> neyi kendisi kapattı. Kirli ilk defter karantinada (`logs/archive/NEDEN.md`); demo metrikleri karantina sonrası temiz defterden.

## Canlı hesap — OKX TR sub-account, 30 USDT, 2 gözetimli tur

Kayıt aralığı **18:29:06 – 18:30:39** (2 dk) · kaynak `journal`

| Metrik | Değer |
|---|---|
| Karar | **16** |
| Fırsat (al/sat sinyali üretilen) | 10 |
| Gönderilen emir | **4** — 9.60 USDT |
| Risk kapısı reddi | **6** (fırsatların %60'i) |
| Ajanın kendi kapattığı pozisyon | 0 |
| Bekleme kararı | 6 |
| Ulaşılamayan tanık okuması | 0 |

### Hangi kural kaç kez devreye girdi

| Kural | Kez |
|---|---|
| Ayni paritede zaten acik pozisyon var | 4 |
| Acik pozisyon limiti dolu | 2 |

### Emirler

| Saat | Parite | USDT | Kâr-al | Zarar-kes |
|---|---|---|---|---|
| 18:29:10 | ETH-USDT | 2.4 | 2561.43888 | 2528.40445 |
| 18:29:14 | SOL-USDT | 2.4 | 102.88656 | 101.55965 |
| 18:29:18 | XRP-USDT | 2.4 | 1.382371 | 1.364543 |
| 18:29:24 | OKB-USDT | 2.4 | 115.27488 | 113.7882 |

Borsadan bağımsız doğrulama (18:30): 4 OCO emri `live`, 4 gerçekleşme, USDT bakiyesi 30,00 → 20,40 (= 30 − 4 × 2,4). Riskteki para 9,6 USDT; tüm zarar-kes'ler tetiklense kayıp ≈ 0,05 USDT.

## Demo hesap — karantina sonrası temiz defter

Kayıt aralığı **17:29:46 – 18:31:34** (62 dk) · kaynak `journal`

| Metrik | Değer |
|---|---|
| Karar | **182** |
| Fırsat (al/sat sinyali üretilen) | 90 |
| Gönderilen emir | **14** — 34.96 USDT |
| Risk kapısı reddi | **76** (fırsatların %84'i) |
| Ajanın kendi kapattığı pozisyon | 14 |
| Bekleme kararı | 78 |
| Ulaşılamayan tanık okuması | 145 |

### Hangi kural kaç kez devreye girdi

| Kural | Kez |
|---|---|
| Borsa koruma emri olusturmuyor — pozisyon geri alindi, parite kapali | 29 |
| Ayni paritede zaten acik pozisyon var | 28 |
| Borsanin minimum emir tutarinin altinda | 15 |
| Zaman stopu — ajan pozisyonu kendisi kapatti | 14 |
| Safe Mode aktif | 4 |

### Emirler

| Saat | Parite | USDT | Kâr-al | Zarar-kes |
|---|---|---|---|---|
| 17:39:36 | SOL-USDT | 2.7 | 102.87648 | 101.5497 |
| 17:39:39 | XRP-USDT | 2.7 | 1.381867 | 1.364046 |
| 17:42:55 | ETH-USDT | 2.46 | 2561.60016 | 2528.56365 |
| 17:49:28 | SOL-USDT | 2.75 | 102.87648 | 101.5497 |
| 17:49:32 | XRP-USDT | 2.75 | 1.380859 | 1.36305 |
| 18:10:57 | ETH-USDT | 2.4 | 2558.76768 | 2525.7677 |
| 18:11:01 | SOL-USDT | 2.4 | 102.82608 | 101.49995 |
| 18:11:05 | XRP-USDT | 2.4 | 1.38096 | 1.36315 |
| 18:20:49 | ETH-USDT | 2.4 | 2561.40864 | 2528.3746 |
| 18:20:53 | SOL-USDT | 2.4 | 102.8664 | 101.53975 |
| 18:20:57 | XRP-USDT | 2.4 | 1.381162 | 1.363349 |
| 18:31:20 | ETH-USDT | 2.4 | 2560.55184 | 2527.52885 |
| 18:31:24 | SOL-USDT | 2.4 | 102.87648 | 101.5497 |
| 18:31:28 | XRP-USDT | 2.4 | 1.382069 | 1.364245 |
