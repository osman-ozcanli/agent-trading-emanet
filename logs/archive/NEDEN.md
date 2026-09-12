# Karantina — 12.09.2026 17:36

Bu klasordeki defter **guvenilmez** ve teslim metriklerine dahil EDILMEZ.

## Sebep
17:30'a kadar `mcp.py` sarmalayici, OKX'in emri reddettigi cevaplari basari sayiyordu.
OKX rededilen emri HTTP 200 icinde `sCode` alaniyla bildiriyor (orn. 51155 =
"bu paritede islem yapamazsiniz"). Kod bu alani hic okumuyordu.

Sonuc: borsanin hic gerceklestirmedigi emirler deftere "alim yapildi" diye yazildi.

## Olcum
- 47 "islem" kaydinin **15'i hayalet** (%32) — OKB-USDT ve ORDI-USDT
- hayalet hacim: **38,31 USDT**
- gercek hacim: 91,71 USDT (ETH / SOL / XRP)

## Duzeltme (17:30)
1. Her MCP cevabinda `sCode` kontrol ediliyor; sifir degilse hata firlatiliyor
2. Emirden sonra koruma emrinin (TP/SL) borsada gercekten olustugu dogrulaniyor;
   olusmadiysa pozisyon geri alinip parite oturum boyunca kapatiliyor
3. Defter 17:36'da sifirlandi — teslim metrikleri **yalnizca bu saatten sonrasini** kapsar

Bu dosya silinmedi cunku hatanin kendisi de kayittir.
