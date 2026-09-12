# EMANET — sunum kılavuzu (12.09.2026, 20:00)

**Görsel sunum (10 slayt):** https://gamma.app/docs/1zabr2jij4vsjru
Ekranda: sunum tam ekran · yan sekmede `localhost:8787` paneli · yan sekmede `tr.okx.com` canlı hesap.
Aşağıdaki metin slayt sırasını takip eder. Toplam 3:00. Fazlası kesilir.
Slayttaki sayılar 19:10 anına ait; ajan çalışmaya devam ediyor, güncel sayıyı panelden oku.

---

## Slayt 1 — Kapak (10 sn)

> EMANET. İşlem yapan değil, hesap veren otonom ajan.
> Emanet: birine güvenilerek bırakılan, olduğu gibi geri verilmesi gereken şey.

## Slayt 2 — Ben kripto bilmiyorum (25 sn)

> Bugün buraya bunu bilerek geldim. Tam da bu yüzden bir programa para emanet etmeden önce
> ondan tek bir şey istedim: hesap ver.
> Otonom ajana paranızı veriyorsunuz, sabah hesap değişmiş. Ne oldu, neden, kurallarına uydu mu?
> Bugün yazılan ajanların hepsi işlem yapar; neredeyse hiçbiri yapmadığı işlemi açıklayamaz.
> Ben tersini yaptım.

## Slayt 3 — Üç Tanık Kuralı, LLM yok (35 sn)

> Her parite için üç bağımsız kaynak oy verir, üçü de OKX Agent Trade Kit'in MCP araçları:
> teknik gösterge, akıllı para yani kârlı traderların ne yaptığı, ve haber duygusu.
> En az ikisi aynı yönü göstermeli ve hiçbiri karşı çıkmamalı. Tek karşı oy işlemi öldürür.
> Karar yolunda LLM yok; halüsinasyon görebilecek tek halka yok.
> Ajan CLI çağırmıyor, MCP sunucusuyla doğrudan konuşan kendi istemcisi var.

## Slayt 4 — Risk kapısı (20 sn)

> Öneri risk kapısına gider. Kapı saf fonksiyon, ağa hiç çıkmaz, "API yavaşladı" diye atlanamaz.
> Pozisyon boyutu, nakit tamponu, pozisyon limiti, zorunlu stop-loss, zaman stopu, günlük kayıp.
> Kapı hayır derse emir gitmez ve sebep deftere yazılır.

## Slayt 5 — Reddetme kaydı (25 sn) — *panele geç, "Hangi kural kaç kez" bölümü*

> İşte ürünün kendisi. Panelin merkezinde işlemler değil, reddedilenler var.
> Demo'da fırsatların yüzde 87'sini reddetti. Her red bir kural, her kural sayılı.
> Size "güvenin" demiyorum. Defteri veriyorum.

## Slayt 6 — Risk borsada (20 sn) — *OKX sekmesi, Algo emirleri*

> Her alım kâr-al ve zarar-kes ile gider, bunlar borsanın içinde durur.
> Bilgisayar kapansa, ajan çökse stop borsada kalır.
> Ajan emirden sonra koruma emrinin gerçekten oluştuğunu doğrular; oluşmadıysa geri alır.
> Bugün iki paritede bunu kendisi yaptı.

## Slayt 7 — Canlı hesap (20 sn) — *OKX bakiye ve fill'ler*

> 18:29'da canlıya geçtim, 19:00'dan beri gerçek parayla kesintisiz otonom çalışıyor.
> Zaman stopu pozisyonları kendisi kapatıyor, satış fill'leri borsada, raporunu kendisi yazıyor.
> Kâr iddiası yok; ölçtüğüm şey karar kalitesi ve hesap verebilirlik.

## Slayt 8 — Dokuz hata (25 sn)

> Bugün dokuz ciddi hata buldum. Altısı demo'da, ikisi canlıda gerçek parayla ama zararsız.
> En önemlisi: borsanın reddettiği emirleri "yapıldı" diye yazıyordum. Yüzde 32 hayalet.
> Buldum, karantinaya aldım, sebebini dosyaya yazdım. Hata da kayıttır.

## Slayt 9 — 17:58 kesintisi (20 sn)

> OKX'in API'si altı dakika kesildi. Ajan tek işlem yapmadı, çökmedi, ağ gelince devam etti.
> Ama bakiyeyi okuyamayınca sıfır sanıp kendini kapattı. Düzeltme tek cümle:
> ölçemediğin şey kayıp değildir, bilinmezliktir.

## Slayt 10 — Kapanış (10 sn)

> Neyi iddia etmediğim de slaytta yazıyor. EMANET: bildiğini iddia etmeyen birinin,
> parasını emanet edebileceği ajan. Teşekkürler.

---

## Jürinin olası soruları ve cevaplar

Her cevabın iskeleti aynı: **"Evet, sınır bu. Yazdım. Sebebi şu."**

**"Kâr ettin mi?"**
> Hayır ve iddia etmiyorum. 30 dolarla bir günde alfa bulmak kumar. Bakiye 29,9; fark komisyon.

**"Teknik tanık hiç oy vermemişse Üç Tanık ne işe yaradı?"**
> Doğru tespit, README'de yazıyor. Bugünkü veriyle konsensüsün katkısı kanıtlanmadı.
> Mimarinin değeri veto hakkında: DOGE'de haber duygusu "sat" dediği için alım olmadı, defterde.
> Tanıkların zaman ölçeklerini eşitlemek ilk yapacağım iş.

**"Her 10 dakikada aynı coini alıp satmak strateji mi?"**
> Hayır, bugünkü parametrelerin sonucu. 8 dakikalık zaman stopu demo penceresinde devir görmek için.
> Gerçek kullanımda saatler olur. Ürün strateji değil, stratejinin hesap verme altyapısı.

**"Agentic hackathon'da LLM yok, bu agent mı?"**
> Otonom karar veren, insan müdahalesiz bir program var; bu agent. LLM'i karar yoluna koymadım,
> halüsinasyon gören halka istemedim. Denedim, zaman kutusunu aştı, bıraktım; saklamıyorum.

**"MCP entegrasyonu ne kadar derin?"**
> Kendi JSON-RPC/stdio istemcim var, kalıcı oturum. Market, smartmoney, news, account, spot order,
> algo order araçları. İki profil: işlem ve istihbarat.

**"Ajan çökerse ne olur?"**
> Stop borsada, bilgisayar kapansa da durur. Emirden sonra koruma emrini doğrular, yoksa geri alır.

**"Defterin bir kısmını sildin mi?"**
> Evet, iki kez, ikisi de yazılı. 17:36 karantinası arşivde, sebebi dosyada. 18:59'daki tek tur:
> ajan yanlışlıkla demo'nun durum dosyasını okudu, o kararlar canlı pozisyonlara ait değildi.

**"Safe Mode gerçek kayıpla çalışır mı?"**
> Test edilmedi. Demo'da yapısal olarak tetiklenemiyor, canlıda %3 kayıp olmadı. Kodda var, kanıtı yok.

**"Stop-loss tetiklendiğini gördün mü?"**
> Hayır, fiyat bantlara girmedi. Kapanışların hepsi zaman stopu; fill'leri borsada.

**"İstihbarat key'i salt-okunur mu?"**
> Hayır. CLI tek profil dayattığı için işlem key'iyle ezildi. Davranış değişmedi, garanti zayıfladı.

**"Bir haftan olsa?"**
> Tanık zaman ölçeklerini eşitle, her kayda borsa emir ID'si, Türkçe hedef girişi, Telegram, kâr bileşiklenmesi.

**"Neyi özgün buluyorsun?"**
> Reddetme kaydı. Herkes işlem listesi gösterir; ben "hangi kural kaç kez hayır dedi" gösteriyorum.
> Ve dokuz hatayı gizlemek yerine ürünün parçası yapmak.

---

## Demo akışı — ekranda sıra

1. Panel: rozet `● canli`, beş sayı, özellikle **reddedilen** ve **red oranı**
2. Panel: "Hangi kural kaç kez" bölümü
3. Panel: bir veto kartı, üç tanık + sarı kutuda sebep
4. OKX sekmesi: Emir Merkezi → Algo, OCO'lar `live`
5. OKX sekmesi: fill listesi, `agent…` alımlar ve `agentx…` satışlar
6. METRICS.md: üstteki zaman damgası, ajan kendisi yeniliyor

**Terminalde key görünmesin. `okx config show` ASLA.**
