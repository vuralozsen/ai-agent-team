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
