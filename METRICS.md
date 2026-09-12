# EMANET — performans metrikleri

Üretildi: 12.09.2026 19:23 · ajan her turun sonunda kendisi yeniler (`src/metrics.py`) · tablolar defterden üretilir.

> Hesap getirisi bu yarışmada puanlanmıyor ve burada iddia edilmiyor. Ölçülen şey ajanın
> **karar kalitesi ve hesap verebilirliği**: kaç fırsat gördü, kaçını hangi kuralla reddetti,
> neyi kendisi kapattı. Kirli ilk defter karantinada (`logs/archive/NEDEN.md`); demo metrikleri karantina sonrası temiz defterden.

## Canlı hesap — OKX TR sub-account, 30 USDT (18:29 iki gözetimli tur, 19:00'dan itibaren otonom)

Kayıt aralığı **18:29:06 – 19:23:16** (54 dk) · kaynak `journal`

| Metrik | Değer |
|---|---|
| Karar | **84** |
| Fırsat (al/sat sinyali üretilen) | 45 |
| Gönderilen emir | **16** — 38.40 USDT |
| Risk kapısı reddi | **29** (fırsatların %64'i) |
| Ajanın kendi kapattığı pozisyon | 12 |
| Bekleme kararı | 27 |
| Ulaşılamayan tanık okuması | 0 |

### Hangi kural kaç kez devreye girdi

| Kural | Kez |
|---|---|
| Ayni paritede zaten acik pozisyon var | 20 |
| Zaman stopu — ajan pozisyonu kendisi kapatti | 12 |
| Acik pozisyon limiti dolu | 9 |

### Emirler

| Saat | Parite | USDT | Kâr-al | Zarar-kes |
|---|---|---|---|---|
| 18:29:10 | ETH-USDT | 2.4 | 2561.43888 | 2528.40445 |
| 18:29:14 | SOL-USDT | 2.4 | 102.88656 | 101.55965 |
| 18:29:18 | XRP-USDT | 2.4 | 1.382371 | 1.364543 |
| 18:29:24 | OKB-USDT | 2.4 | 115.27488 | 113.7882 |
| 19:01:01 | ETH-USDT | 2.4 | 2555.39088 | 2522.43445 |
| 19:01:05 | SOL-USDT | 2.4 | 102.88656 | 101.55965 |
| 19:01:09 | XRP-USDT | 2.4 | 1.383682 | 1.365837 |
| 19:01:15 | OKB-USDT | 2.4 | 114.99264 | 113.5096 |
| 19:09:41 | ETH-USDT | 2.4 | 2553.90912 | 2520.9718 |
| 19:09:45 | SOL-USDT | 2.4 | 102.83616 | 101.5099 |
| 19:09:49 | XRP-USDT | 2.4 | 1.382371 | 1.364543 |
| 19:09:56 | OKB-USDT | 2.4 | 114.7104 | 113.231 |
| 19:19:43 | ETH-USDT | 2.4 | 2554.70544 | 2521.75785 |
| 19:19:47 | SOL-USDT | 2.4 | 102.82608 | 101.49995 |
| 19:19:51 | XRP-USDT | 2.4 | 1.38217 | 1.364344 |
| 19:19:57 | OKB-USDT | 2.4 | 114.62976 | 113.1514 |

_Elle yazılmış tek not (18:30, borsadan `spot_get_algo_orders` / `account_get_balance` ile):_ 4 OCO `live`, 4 gerçekleşme, USDT 30,00 → 20,40. 19:00'da zaman stopu dördünü kapattı (`spot_get_fills`: 4 satış).

## Demo hesap — karantina sonrası temiz defter

Kayıt aralığı **17:29:46 – 19:20:35** (111 dk) · kaynak `journal`

| Metrik | Değer |
|---|---|
| Karar | **311** |
| Fırsat (al/sat sinyali üretilen) | 180 |
| Gönderilen emir | **20** — 49.36 USDT |
| Risk kapısı reddi | **160** (fırsatların %89'i) |
| Ajanın kendi kapattığı pozisyon | 23 |
| Bekleme kararı | 108 |
| Ulaşılamayan tanık okuması | 160 |

### Hangi kural kaç kez devreye girdi

| Kural | Kez |
|---|---|
| Borsa koruma emri olusturmuyor — pozisyon geri alindi, parite kapali | 59 |
| Ayni paritede zaten acik pozisyon var | 46 |
| Safe Mode aktif | 32 |
| Borsanin minimum emir tutarinin altinda | 23 |
| Zaman stopu — ajan pozisyonu kendisi kapatti | 23 |

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
| 18:41:11 | ETH-USDT | 2.4 | 2555.01792 | 2522.0663 |
| 18:41:15 | SOL-USDT | 2.4 | 102.84624 | 101.51985 |
| 18:41:18 | XRP-USDT | 2.4 | 1.381464 | 1.363648 |
| 18:51:00 | ETH-USDT | 2.4 | 2553.50592 | 2520.5738 |
| 18:51:04 | SOL-USDT | 2.4 | 102.80592 | 101.48005 |
| 18:51:08 | XRP-USDT | 2.4 | 1.38348 | 1.365638 |
