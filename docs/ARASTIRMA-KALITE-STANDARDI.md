# Araştırma Kalite Standardı (Vural — Tüm Araştırma Görevleri)

Bu standart, **her araştırma raporu için geçerlidir** — Karf&Scoot veya gelecekteki tüm
araştırma görevleri. Rapor bu maddeleri karşılamadan teslim edilmez.

Kaynak: Vural'ın 2026-08-15 Karf&Scoot raporu incelemesi (13 eksiklik tespiti).

## K1. DOĞRULAMA (hallüsinasyon önleme)
- Her aday firma: web sitesi canlı mı (HTTP), iletişim bilgileri doğrulanmış mı, kaynak URL + erişim tarihi.
- Doğrulanamayan → "DOĞRULANAMADI" etiketi, ayrı bölüm.

## K2. KARAR VERİCİ ANALİZİ
- Firma büyüklüğüne göre karar verici modeli (küçük: sahibi, orta: satış direktörü, büyük: iş geliştirme/satın alma).
- Her firma için "kiminle iletişime geçilmeli" rolü.

## K3. KİŞİSEL KONTAK ZORUNLULUĞU
- info@/sales@ → GENEL etiketi, kabul edilmez.
- Kişisel kontak kaynakları: LinkedIn, team sayfası, basın bülteni, fuar listeleri, ticaret sicili.
- **Kontak veritabanları (Apollo.io, PDL, Hunter.io, Lusha):** doğrulanmış kişi (ad+unvan+direkt email+telefon) bul; maske-doğrulanmış (i***@domain) da kabul, etiketle.
- Unvan bazlı hedefleme: gerçek çalışan listesinden (LinkedIn/Apollo/team) eşleştir; varsayımdan unvan uydurma.
- Bulunamadıysa: "bulunamadı" + en yakın alternatif (asla uydurma).
- LinkedIn engelliyse: alternatifler (Apollo/PDL/team/basın/fuar); yoksa DIŞ KISIT + ne zaman denenebilir.

## K3b. KİŞİSEL TELEFON (yüksek değerli görevlerde)
- Apollo/PDL mobil, fuar katalogları, basın imza blokları, sicil iletişim kayıtları.
- Bulunamazsa: "kişisel cep yayınlanmıyor" + şirket hattı + alternatif.

## K4. TİCARET SİCİLİ DOĞRULAMASI
- Ülkeye göre resmi sicil (KRS/ONRC/CIPC/MCA/CR/CNPJ/Handelsregister...).
- Sicil no, kuruluş yılı, aktif durum, faaliyet alanı.
- Bot-korumalıysa: aynalar (Zauba/Tofler/D&B/Kompass/Orbis), site footer/tüzel ad, ticaret odası. Yoksa DOĞRULANAMADI + gerekçe. Top-3 ülke firmaları tüzel doğrulanamıyorsa rapor açıkça belirtir.

## K4b. ÜNVAN BAZLI ÇALIŞAN TARAMASI
- Karar vericileri gerçek çalışan listesinden çıkar (LinkedIn/team/Apollo/PDL). Varsayımdan unvan uydurma.

## K5. ÜRÜN-BAYİ EŞLEŞME MATRİSİ
- Hangi ürün kategorisi hangi bayiye gidecek + portföy uyumu.

## K6. İŞ DEĞERİ SIRALAMASI
- TAM/SAM/SOM, ilk yıl satış hacmi ($), 3 yıllık potansiyel, "para kazandıracak" sıralama.

## K7. FİYATLANDIRMA / MARJ ANALİZİ
- Sektör distribütör iskontosu (gaz/alev: tipik %20-35), örnek marj hesabı.

## K8. ELEME LOGU
- Elenen her firma + gerekçe (üretici, ölü site, doğrulanamadı, segment, coğrafya, ölçek).

## K9. ÜRETİCİ KURALI
- Üretim yapan firma distribütör adayı OLAMAZ (GAZEX, Atest Gaz gibi) → ÜRETİCİ etiketi + eleme.
- **Rakip marka distribütörü de aday OLAMAZ** (MSA/Honeywell/Draeger/Crowcon distribütörü) → RAKİP DISTRIBÜTÖRÜ etiketi + eleme (marka çakışması). Aday tablosunda asla görünmez, sadece eleme logunda.

## K10. LOJİSTİK OBJEKTİFLİĞİ
- Objektif ölçütler: mesafe, direkt uçuş, gümrük anlaşması, sevkiyat süresi, maliyet.
- Merkez ülke (Türkiye) baz alınır; uzak ülke düşük puan + gerekçe.

## K11. ÜLKE DERİNLİĞİ (çek listesi yasak)
- Havuz max 8-10 ülke, hepsi derinleştirilir; derinleştirilemeyen çıkarılır + gerekçe.
- **EKOSİSTEM > İTHALAT RAKAMI (K11b):** ithalat küçük diye eleme; önce distribütör ekosistemi (aday sayısı, doğrulanmış kontaklar, fuarlar). Ekosistem zenginse ülke kalır (örn. Romanya: küçük ithalat, 10+ distribütör + kontaklar).

## K12. MEVCUT BAYİ FESİH ANALİZİ
- Sözleşme bitiş tarihi, fesih bedeli tahmini, geçiş süresi, hazır alternatif, riskler.

## K13. ÇİFT KAYNAK ZORUNLULUĞU
- Kritik verilerde en az 2 bağımsız kaynak; tek kaynak → "TEK KAYNAK" uyarısı.

## K14. VERİ TARİHİ / TAZELİĞİ
- Her veri için kaynak tarihi + erişim tarihi; 2+ yaş → "ESKİ" uyarısı.

## KALİTE STANDARDI UYUM TABLOSU (rapor sonunda ZORUNLU)
```
| # | Standart | Durum | Gerekçe |
|---|----------|-------|---------|
| K1 | Doğrulama | ✅/⚠️/❌ | ... |
```
