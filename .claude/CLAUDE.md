# CLAUDE.md — Shared Memory Kuralları (Claude Code + Hermes ortak)

Bu repo, masaüstündeki Claude Code ile VPS'teki Hermes Agent'in **aynı shared memory'yi**
kullandığı ortak çalışma sistemidir. Amaç: **aynı işi iki tarafın yapmaması**.

## KRİTİK KURAL: Her görevde şu sıra uygulanır

```
1. KONTROL ET (görev başı)  → memctl search — "bu iş yapılmış mı / yapılıyor mu?"
2. İŞİ YAP
3. KAYDET (görev sonu)      → memctl write — "ne yaptım" (önemli sonuçlar)
```

### 1. Görev başı — KONTROL (ZORUNLU)

```bash
python3 scripts/memctl.py search "<görev özeti>" --limit 5
# veya proje belli ise:
python3 scripts/memctl.py search "<görev özeti>" --project <proje_id> --limit 5
```

- **Aynı iş zaten yapılmışsa** (benzer kayıt bulunursa): işi tekrar YAPMA.
  Kullanıcıya söyle: *"Bu iş daha önce yapılmış: <özet> (tarih). Devam etmek ister misin?"*
- **Devam eden iş varsa** (in-progress kaydı): onu tamamla, baştan başlama.
- Sonuç yoksa → işe başla.

### 2. Görev sonu — KAYDET (ZORUNLU, önemli işlerde)

```bash
python3 scripts/memctl.py write \
  --project <proje_id> \
  --domain <alan> \
  --type <tip> \
  --content "Ne yapıldı, sonuç, kararlar" \
  --summary "Kısa özet" \
  --agent claude-code
```

- Kalıcı karar / değişiklik / bug / çözüm / deployment → MUTLAKA yaz
- Geçici/önemsiz → yazma
- **SECRET ASLA YAZMA** (şifre, token, API key)

### 3. Proje tespiti

Proje bilinmiyorsa: `python3 scripts/memctl.py projects` ile listele,
cwd/git remote ile eşleştir. Bilinmiyorsa `--project general` KULLANMA — kullanıcıya sor.

## Ortam değişkenleri

```bash
export MEMORY_API_URL="https://memory-serve.tailc29799.ts.net"
export MEMORY_API_KEY="<MEMORY_API_KEY>"   # .env'den al, repo'ya yazma
```

## Sık kullanılan komutlar

| Amaç | Komut |
|---|---|
| Sağlık | `python3 scripts/memctl.py health` |
| Ara | `python3 scripts/memctl.py search "..." --project x --limit 5` |
| Yaz | `python3 scripts/memctl.py write --project x --content "..."` |
| Projeler | `python3 scripts/memctl.py projects` |
| Olaylar | `python3 scripts/memctl.py events --limit 10` |

## Önemli

- **Claude Code native memory'si ile karıştırma** — bu Shared Memory iki ajan arası
  köprü, her ikisi de aynı yere yazar/okur.
- Emin değilsen YAZMAKTANSA SOR — yanlış projeye kayıt, hiç kayıt olmamasından kötüdür.
- Tailscale kapalıysa `MEMORY_API_URL` erişilemez → işe devam et ama kullanıcıya
  "shared memory erişilemedi" de, sonra senkronize et.

## KARAR (2026-08-15): UserPromptSubmit hook EKLENMEDİ

`settings.example.json`'daki UserPromptSubmit örneği (her prompt'ta memory search)
**iki taraf için de kullanılmayacak**. Gerekçe:
1. SessionStart zaten son kayıtları otomatik yükler — her prompt'ta tekrar arama gereksiz.
2. Her prompt'ta API çağrısı: gecikme + Tailscale kapalıyken timeout riski.
3. Embedding hash-tabanlı; kısa promptlarla ("devam", "bakalım") anlamsız sonuç → gürültü.
4. "Bu iş yapılmış mı?" kontrolü hook zorunluluğu değil **model muhakemesi** işidir:
   görev yinelenen/önemli görünüyorsa agent kendisi `memctl search` çağırır.

**Uygulanan desen (iki taraf için aynı):** SessionStart (otomatik okuma) +
SessionEnd (otomatik yazma) + gerekince manuel `memctl search`.
Claude Code tarafı: `memory_hook.py` canlı. Hermes tarafı: eşdeğerini
SessionStart/End ile sınırlı tutmalı, prompt-başı hook eklememeli.

## GÜNCELLEMELERDEN HABERDAR OLMA (her iki taraf)

Diğer tarafın güncellemesini öğrenmenin tek yolu pasif bekleme değil — **session açılışında otomatik kontrol**:

1. **Memory tarafı:** SessionStart search'ünde karşı tarafın kayıtları önceliklidir
   (Claude Code → `source=hermes` filtrele; Hermes → `source=claude-code` filtrele).
2. **Repo tarafı:** Session açılışında `git fetch origin && git log HEAD..origin/main` —
   yeni commit varsa karşı taraf bir şey eklemiş/güncellemiş demektir; modele
   "çekilmemiş commit var" uyarısı inject edilir, model isterse pull eder.

Hermes'te eşdeğer mekanizma: görev başlangıcında (a) son `source=claude-code`
memory kayıtlarını ara, (b) `git fetch` + yeni commit kontrolü yap. İki taraf da
bunu yaptığı sürece hiçbir güncelleme sessiz kalmaz.

## HERMES 7/24 ÇALIŞIR — iş dağıtımı

**Hermes (VPS) PC kapalı olsa da çalışır** (Telegram + cron + bot ekibi).
Detay: `docs/HERMES-SYSTEM.md` — okumadan uzun/önemli görevde Hermes'i tercih et.

**Dağıtım kuralı:**
- Kod/repo/masaüstü → Claude Code (PC açıkken)
- Araştırma/içerik/finans/izleme/uzun görev → Hermes'e bırak (kesintisiz)
- Görev yarıda kalırsa Hermes devralabilir (shared memory'den okur)
