# EMANET — performans metrikleri

Üretildi: 12.09.2026 19:55 · ajan her turun sonunda kendisi yeniler (`src/metrics.py`) · tablolar defterden üretilir.

> Hesap getirisi bu yarışmada puanlanmıyor ve burada iddia edilmiyor. Ölçülen şey ajanın
> **karar kalitesi ve hesap verebilirliği**: kaç fırsat gördü, kaçını hangi kuralla reddetti,
> neyi kendisi kapattı. Kirli ilk defter karantinada (`logs/archive/NEDEN.md`); demo metrikleri karantina sonrası temiz defterden.

## Canlı hesap — OKX TR sub-account, 30 USDT (18:29 iki gözetimli tur, 19:00'dan itibaren otonom)

Kayıt aralığı **18:29:06 – 19:55:18** (86 dk) · kaynak `journal`

| Metrik | Değer |
|---|---|
| Karar | **191** |
| Fırsat (al/sat sinyali üretilen) | 89 |
| Gönderilen emir | **22** — 51.57 USDT |
| Risk kapısı reddi | **67** (fırsatların %75'i) |
| Ajanın kendi kapattığı pozisyon | 19 |
| Bekleme kararı | 83 |
| Ulaşılamayan tanık okuması | 120 |

### Hangi kural kaç kez devreye girdi

| Kural | Kez |
|---|---|
| Ayni paritede zaten acik pozisyon var | 34 |
| Zaman stopu — ajan pozisyonu kendisi kapatti | 19 |
| KAPATMA BASARISIZ — pozisyon korumasiz olabilir, sonraki tur | 17 |
| Acik pozisyon limiti dolu | 12 |
| Safe Mode aktif | 4 |

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
| 19:26:41 | OKB-USDT | 1.68 | 114.21648 | 112.74345 |
| 19:29:57 | ETH-USDT | 2.23 | 2552.90112 | 2519.9768 |
| 19:30:01 | SOL-USDT | 2.23 | 102.8664 | 101.53975 |
| 19:30:05 | XRP-USDT | 2.23 | 1.381565 | 1.363747 |
| 19:51:42 | ETH-USDT | 2.4 | 2551.21776 | 2518.31515 |
| 19:51:46 | SOL-USDT | 2.4 | 102.84624 | 101.51985 |

_Elle yazılmış tek not (18:30, borsadan `spot_get_algo_orders` / `account_get_balance` ile):_ 4 OCO `live`, 4 gerçekleşme, USDT 30,00 → 20,40. 19:00'da zaman stopu dördünü kapattı (`spot_get_fills`: 4 satış).

## Demo hesap — karantina sonrası temiz defter

Kayıt aralığı **17:29:46 – 19:52:19** (143 dk) · kaynak `journal`

| Metrik | Değer |
|---|---|
| Karar | **394** |
| Fırsat (al/sat sinyali üretilen) | 210 |
| Gönderilen emir | **26** — 63.76 USDT |
| Risk kapısı reddi | **184** (fırsatların %88'i) |
| Ajanın kendi kapattığı pozisyon | 26 |
| Bekleme kararı | 158 |
| Ulaşılamayan tanık okuması | 285 |

### Hangi kural kaç kez devreye girdi

| Kural | Kez |
|---|---|
| Borsa koruma emri olusturmuyor — pozisyon geri alindi, parite kapali | 69 |
| Ayni paritede zaten acik pozisyon var | 49 |
| Safe Mode aktif | 40 |
| Borsanin minimum emir tutarinin altinda | 26 |
| Zaman stopu — ajan pozisyonu kendisi kapatti | 26 |

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
| 19:30:21 | ETH-USDT | 2.4 | 2553.23376 | 2520.30515 |
| 19:30:26 | SOL-USDT | 2.4 | 102.85632 | 101.5298 |
| 19:30:30 | XRP-USDT | 2.4 | 1.381565 | 1.363747 |
| 19:52:05 | ETH-USDT | 2.4 | 2551.38912 | 2518.4843 |
| 19:52:09 | SOL-USDT | 2.4 | 102.84624 | 101.51985 |
| 19:52:13 | XRP-USDT | 2.4 | 1.381162 | 1.363349 |
