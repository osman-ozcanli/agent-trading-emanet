# EMANET — 3 dakikalık sunum metni

Konuşan: Osman. Ekranda: `localhost:8787` paneli açık, yan sekmede `tr.okx.com` canlı hesap.
Her bölümün başında süre. Toplam 3:00. Fazlası kesilir.

---

## 0:00 — Açılış (20 sn)

> Ben kripto bilmiyorum. Bugün buraya bunu bilerek geldim.
> Tam da bu yüzden bir programa para emanet etmeden önce ondan tek bir şey istedim:
> **hesap ver.** Ürünün adı EMANET. İşlem yapan değil, hesap veren otonom ajan.

## 0:20 — Problem (25 sn)

> Otonom bir ajana paranızı veriyorsunuz. Sabah hesabınız değişmiş. Ne oldu? Neden?
> Kurallarına uydu mu? Bugün yazılan ajanların hemen hepsi işlem yapar;
> neredeyse hiçbiri **yapmadığı** işlemi açıklayamaz. Ben tersini yaptım.

## 0:45 — Nasıl karar veriyor (35 sn) — *panelde bir karar kartını göster*

> Üç Tanık Kuralı. Her parite için üç bağımsız kaynak oy verir — hepsi OKX Agent Trade Kit'in
> MCP araçları: teknik göstergeler, akıllı para yani kârlı traderların ne yaptığı, ve haber duygusu.
> En az ikisi aynı yönü göstermeli ve **hiçbiri karşı çıkmamalı.** Tek karşı oy işlemi öldürür.
> Sonra öneri risk kapısına gider. Kapı "hayır" derse emir gitmez ve **sebep deftere yazılır.**
> Karar yolunda LLM yok. Halüsinasyon görebilecek tek bir halka bile yok.

## 1:20 — Reddetme kaydı (30 sn) — *"Hangi kural kaç kez devreye girdi" bölümünü göster*

> İşte ürünün kendisi. Bugün ajanım demo'da 90 fırsat gördü, **76'sını reddetti** — yüzde 84.
> Her red bir kural, her kural sayılı: aynı pariteye ikinci giriş, minimum emir tutarı,
> pozisyon limiti, zaman stopu. Size "güvenin" demiyorum. Defteri veriyorum.

## 1:50 — Risk borsada (25 sn) — *OKX sekmesine geç, algo emirlerini göster*

> Her alım emri, kâr-al ve zarar-kes ile birlikte gider. Bunlar **borsanın içinde** durur.
> Bilgisayarım kapansa, internet gitse, ajan çökse — stop borsada kalır.
> Ve ajan emirden sonra koruma emrinin gerçekten oluştuğunu doğrular. Oluşmadıysa pozisyonu
> anında geri alır. Bugün bunu iki paritede kendisi yaptı.

## 2:15 — Bugün ne oldu — dürüst kısım (30 sn)

> Bugün altı ciddi hata buldum. Hepsini demo'da, gerçek paraya dokunmadan.
> Bir tanesini anlatayım: saat altıda OKX'in API'si altı dakika kesildi.
> Ajanım tek işlem yapmadı — veri yoksa işlem yok. Ağ gelince kendi kendine devam etti.
> Ama bir hata da yaptı: bakiyeyi okuyamayınca sıfır sanıp kendini kapattı.
> Onu da düzelttim: ölçemediğin şey kayıp değildir, bilinmezliktir. Logda duruyor.

## 2:45 — Canlı ve kapanış (15 sn) — *canlı bakiyeyi göster: 30 → 20,40*

> Saat 18:29'da canlıya geçtim. İki gözetimli tur, dört gerçek emir, dördü de OCO ile korunmuş,
> bakiye kuruşuna kadar tutuyor. Sonra durdurdum — gözetimsiz canlı ajan bırakmam.
> EMANET: bildiğini iddia etmeyen birinin, parasını emanet edebileceği ajan. Teşekkürler.

---

## Soru gelirse — hazır cevaplar

**"Stop-loss tetiklendiğini gördün mü?"**
> Hayır. Emirler borsada canlı duruyor ama bugünkü pencerede fiyat bantlara girmedi.
> Ajanın kendi zaman stopu 14 kez tetiklendi ve pozisyon kapattı, gerçekleşmeleri var.

**"Neden LLM yok? Bu agentic hackathon."**
> Denedim, zaman kutusunu aştı, terk ettim — bunu saklamıyorum. Ama sonuç bilinçli bir tasarım
> oldu: karar yolunda halüsinasyon görebilecek bileşen yok. MCP entegrasyonu LLM'siz de derin —
> ajan doğrudan MCP istemcisi, 168 araca konuşuyor.

**"Kâr ettin mi?"**
> Bu yarışmada kâr puanlanmıyor ve ben de iddia etmiyorum. 30 dolarla bir günde alfa bulmak
> kumardır. Ölçtüğüm şey karar kalitesi ve hesap verebilirlik.

**"Defterin ilk sürümü kirliydi dedin, neden?"**
> Borsanın reddettiği emirleri "yapıldı" diye yazıyordum — cevabın içindeki hata kodunu
> okumuyordum. Yüzde 32 hayalet. Buldum, karantinaya aldım, sebebini dosyaya yazdım,
> temiz defterle devam ettim. Hata da kayıttır.

**"Kripto bilmemen dezavantaj değil mi?"**
> Bir uzman "RSI 35 altı al" der ve geçer. Ben soramadığım için sistemin bana kanıt sunmasını
> şart koştum. O ihtiyaç, uzmanın yapmayacağı bir şey doğurdu: reddetme kaydı.

## Demo akışı — ekranda sıra

1. Panel: üst rozet `● canli`, beş sayı, özellikle **reddedilen** ve **red oranı**
2. Panel: "Hangi kural kaç kez" bölümü
3. Panel: bir veto kartı — üç tanık + sarı kutuda sebep
4. OKX sekmesi: `Emir Merkezi → Algo` — 4 OCO `live`
5. OKX sekmesi: bakiye 20,40 USDT + dört varlık `frozen`
6. Terminal: `python src/metrics.py` çıktısı (isteğe bağlı)

**Terminalde key görünmesin. `okx config show` ASLA.**
