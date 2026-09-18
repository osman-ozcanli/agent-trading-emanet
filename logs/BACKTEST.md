# EMANET — backtest raporu (vade taramasi)

Uretildi: 18.09.2026 15:10 · `python src/backtest.py --days 90 --horizon-sweep` · **config.yaml degismedi, ajana dokunulmadi.**

## Neden bu kosu var

18.09 sabahi uc varyant (mevcut / C / C+tampon) denendi, ucu de negatif cikti ve her seferinde **tanik mantigi** degistirildi. Islem bazli ayristirma sebebin tanik olmadigini gosterdi: zaman-stopuyla kapanan 114 islemin komisyon oncesi kenari **%+0,064**, gidis-donus komisyon **%0,20** — sinyal yanlis degil, **3,1 kat zayif**. Bu bir esik sorunu degil vade sorunu oldugu icin bu kosuda tanik sabit tutulup **vade tarandi**.

## Kapsam

- Pencere: **99.9 gun** (10.06.2026 - 18.09.2026 UTC), 8 parite, 1H simulasyon mumu.
- Sinyal: EMA20 **4H** + **1D** rejim anahtari (Secenek C), tampon %0.0.
- Tanik kurgusu: **tech**. Akilli para **devre disi**: gecmisi ~100 saatle sinirli (gunluk uc nokta HTTP 500, saatlik limit>100 reddediyor) ve veri varken oylarin %75'i 'buy' cikiyor — yani neredeyse sabit. Onu sart kosmak pencereyi 90 gunden 4 gune dusurup karsiliginda cok az bilgi veriyordu. Duygu tanigi her iki kurguda da test edilmez: OKX'te gecmise donuk oran yok, uydurulmaz.
- Komisyon: gidis-donus **%0.20** (%0.10 her yon, OKX spot taker).
- Short: **kapali** — spot nakit hesapta short acilamaz. Onceki kosuda 34 short islem sayilmisti; ajan bunlari hicbir zaman uygulayamazdi.
- Kar-al/zarar-kes seviyeleri **`risk.brackets()`** ile, yani canli ajanin kendi fonksiyonuyla hesaplanir. Onceki surum her iki yon icin de alis mantigi kullaniyordu (`sell take_profit -0.0240` satirlari bunun iziydi).
- Geriye donuk bakis yok: 4H/1G EMA bir 1H barina ancak o bar kapandiktan sonra gorunur; akilli para okumasi barin kapanis zamanindan sonrasini gormez.
- Bir barin icinde iki seviye de tetiklenebiliyorsa **zarar-kes once** sayilir. Uzun vadede bantlar (%2-8) 1H bar menzilinden cok genis oldugu icin bu varsayim artik belirleyici degil; 0,8/0,5 kurgusunda belirleyiciydi.

## Olcut: ayni pencerede hicbir sey yapmamak

Bir stratejinin %5 getirdigi pencerede sadece tutmak %60 getiriyorsa o strateji kenar bulmus degil, **ralliyi kacirmanin bir yolunu** bulmustur. Uzun tarafli her kural yukselen piyasada yetenekli gorunur; bu olcut o yanilgiyi kesiyor.

| Parite | Al-tut getirisi |
|---|---|
| ZEC-USDT | +230.77% |
| SOL-USDT | +62.47% |
| OKB-USDT | +59.54% |
| ETH-USDT | +51.86% |
| ORDI-USDT | +38.17% |
| BTC-USDT | +25.58% |
| XRP-USDT | +17.13% |
| DOGE-USDT | +0.90% |
| **8 parite esit agirlikli** | **+60.80%** |

Yani bu 100 gunluk pencere guclu bir **boga piyasasi**. Asagidaki hicbir satir bu sayiya yaklasmiyor.

## Vade taramasi — tek degisken vade, sinyal sabit

### Momentum — kural yazildigi gibi

Kural yazildigi gibi: fiyat iki EMA'nin da **ustundeyse** al (momentum).

| Tutma | Kar-al | Zarar-kes | Islem | Ort. tutma | Net getiri | Kazanma | Maks dusus | Brut/islem | Net/islem | t |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 sa | %0.8 | %0.5 | 5299 | 1.0 sa | **-66.24%** | %26.9 | %66.35 | -0.017% | -0.217% ±0.006 | -36.97 |
| 4 sa | %2.0 | %1.5 | 1711 | 3.4 sa | **-22.15%** | %38.5 | %23.11 | +0.005% | -0.195% ±0.026 | -7.37 |
| 8 sa | %3.0 | %2.0 | 949 | 6.5 sa | **-12.01%** | %40.4 | %13.62 | +0.007% | -0.193% ±0.052 | -3.73 |
| 1 gun | %4.0 | %2.5 | 438 | 15.0 sa | **-3.89%** | %42.2 | %6.97 | +0.052% | -0.148% ±0.120 | -1.24 |
| 2 gun | %6.0 | %3.5 | 230 | 30.2 sa | **-0.41%** | %42.2 | %4.00 | +0.147% | -0.053% ±0.241 | -0.22 |
| 4 gun | %8.0 | %5.0 | 127 | 60.5 sa | **+1.22%** | %46.5 | %4.01 | +0.331% | +0.131% ±0.446 | +0.29 |

### Ters cevrilmis — ortalamaya donus (teshis)

**Teshis amacli** ters cevrilmis hali: fiyat iki EMA'nin da **altindaysa** al (ortalamaya donus). Bu bir strateji onerisi degil, sinyalde bilgi olup olmadigini anlama testidir.

| Tutma | Kar-al | Zarar-kes | Islem | Ort. tutma | Net getiri | Kazanma | Maks dusus | Brut/islem | Net/islem | t |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 sa | %0.8 | %0.5 | 4399 | 1.0 sa | **-55.76%** | %27.3 | %55.80 | -0.002% | -0.202% ±0.006 | -33.94 |
| 4 sa | %2.0 | %1.5 | 1290 | 3.7 sa | **-13.30%** | %38.0 | %14.82 | +0.051% | -0.149% ±0.026 | -5.79 |
| 8 sa | %3.0 | %2.0 | 695 | 7.3 sa | **-3.46%** | %46.3 | %5.17 | +0.134% | -0.066% ±0.050 | -1.31 |
| 1 gun | %4.0 | %2.5 | 301 | 18.8 sa | **+2.14%** | %48.5 | %2.95 | +0.306% | +0.106% ±0.130 | +0.81 |
| 2 gun | %6.0 | %3.5 | 163 | 37.2 sa | **+4.57%** | %51.5 | %3.74 | +0.643% | +0.443% ±0.263 | +1.68 |
| 4 gun | %8.0 | %5.0 | 87 | 76.3 sa | **+4.89%** | %49.4 | %2.98 | +1.055% | +0.855% ±0.470 | +1.82 |


**Brut/islem** = komisyon oncesi kenar, islem basi ortalama. Basabas icin bunun %0.20'yi gecmesi gerekir. **Net/islem** = komisyon sonrasi, yanindaki ± standart hata. **t** = net/islem'in sifirdan kac standart hata uzakta oldugu; kabaca |t| > 2 olmadan 'kenar var' denemez.

> Uyari: pozisyonlar ust uste biniyor (ayni anda 4 tane, birbiriyle korelasyonlu pariteler), yani etkin orneklem islem sayisindan kucuk ve buradaki t degerleri **iyimser**. Isaretin degil, **egilimin** okunmasi daha guvenli: brut kenarin vade ile monotonik degismesi tek bir satirin pozitif cikmasindan daha guclu bir kanittir.

Adim 2'nin gecis sarti (PROGRESS.md): komisyon sonrasi pozitif **VE** maks. dusus < %10.

## Okuma

1. **Teshis dogrulandi.** 1 saatlik vadede brut kenar ~%0,00 ve net kayip istatistiksel olarak ezici (t ≈ -37). Yani canli config'in kaybi sinyal kalitesinden degil, tamamen komisyondan geliyordu. 18.09 sabahi uc kez tanik mantigi degistirilmesi bu yuzden sonuc vermedi.
2. **Vade dogru degiskendi.** Brut kenar vade uzadikca **monotonik** artiyor ve maksimum dusus %66'dan %4'e iniyor. Monotonluk, tek bir pozitif satirdan daha guclu bir kanit.
3. **Ama kenar hala gosterilemedi.** En iyi satirda bile |t| < 2; yani pozitif getiri gurultuden ayirt edilemiyor. Ayrica 2 yon x 6 vade = **12 kombinasyon** denendi, en iyisinin t≈1,8 cikmasi sansla beklenen seydir. Bu bir bulgu degil.
4. **Olcut hepsini gecti.** Ayni pencerede al-tut **+60.80%**. Hicbir varyant buna yaklasmiyor. Ters cevrilmis kuralin daha iyi gorunmesinin en olasi aciklamasi da bu: yukselen piyasada 'dususte al' her zaman iyi gorunur. Bu, ortalamaya donus kenari degil, **uzun tarafli olmanin** getirisi.

**Sonuc: bu pencerede kanitlanmis bir kenar yok.** Vade duzeltmesi gerekli bir adimdi ve yapildi (kayip %-66'dan %+1'e, dusus %66'dan %4'e), ama yeterli degil. Bir sonraki dogru soru 'hangi esik' degil: **bu sinyal ayi/yatay piyasada ne yapiyor?** 100 gunun tamami boga oldugu icin bu pencere o soruyu cevaplayamaz — daha uzun ya da farkli rejimli bir pencere gerekiyor.

## Karar

Bu rapor bir kazanc iddiasi degil. Osman sayiyi gorup onaylamadan `config.yaml` ve `src/witnesses.py` degistirilmez; ajan dondurulmus halde kalir (PROGRESS.md, 18.09 karari).
