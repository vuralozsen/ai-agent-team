# Hermes Agent (VPS) — Sistem Bilgisi

Bu dosya, Claude Code'un Hermes Agent'i doğru kullanabilmesi için gereken bilgileri içerir.

## HERMES 7/24 ÇALIŞIR (PC kapalı olsa bile)

Hermes Agent, **VPS'te (Dokploy container'ında) sürekli çalışır**:
- **PC kapalı olsa da** Telegram üzerinden görev alır, cron görevlerini yürütür, botları yönetir.
- Masaüstündeki Claude Code **sadece PC açıkken** çalışır. Hermes buna bağımlı değildir.
- İkisi farklı ortamlarda: Claude Code = masaüstü, Hermes = bulut (7/24).

## İŞ DAĞILIMI ÖNERİSİ

Kullanıcı (Vural) görev verdiğinde, iş türüne göre dağıtım yapılır:

| İş türü | Hangi taraf |
|---|---|
| **Kod yazma / repo değişikliği / masaüstü dosyaları** | Claude Code (masaüstü) |
| **Araştırma / pazar / rakip analizi** | Hermes (arastirmaci botu) |
| **İçerik üretimi (TR prime saatler)** | Hermes (icerik botu) |
| **Finans / veri analizi / NocoDB / Dokploy** | Hermes (analist botu) |
| **7/24 izleme, cron, otomasyon, Telegram** | Hermes (her zaman) |
| **Uzun süreli görevler** | Hermes (PC kapanması işi kesmez) |

## KRİTİK: PC KAPANIRSA

- Hermes **etkilenmez** — VPS'te çalışmaya devam eder.
- Claude Code'un yarım kalan işi varsa, Hermes devralabilir (shared memory'den durumu okur).
- **Bu yüzden**: Uzun/önemli görevlerde **Hermes'i tercih et** (kesintisiz).
- Hızlı/etkileşimli kod işlerinde Claude Code (masaüstü açıkken) daha uygun.

## İLETİŞİM

- Hermes'e görev vermek için: Telegram (Vural → Hermes yazar).
- Hermes → Claude Code: shared memory + repo (ai-agent-team) üzerinden.
- Claude Code → Hermes: memory'ye yazar (`memctl write --agent claude-code`), Hermes görür.

## OTONOM BOT EKİBİ (Hermes altında)

Hermes, VPS'te 3 yardımcı bot yönetir (profiller):
- **arastirmaci** — web/pazar/rakip araştırması
- **icerik** — içerik üretimi (TR prime 19-23)
- **analist** — finans/pazar/veri analizi

Bunlar da 7/24 hazır bekler; görev verilince çalışır. Claude Code bu botlara doğrudan
ulaşamaz, ama Hermes'e görev verirse Hermes dağıtır.
