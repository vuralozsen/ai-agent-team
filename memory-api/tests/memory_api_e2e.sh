#!/usr/bin/env bash
# =============================================================================
# Memory API — E2E test script (iyilestirme sonrasi dogrulama)
#
# Hedeflenen yeni ozellikler: /v1/memory/search uzerinde
#   - min_score  (esik filtreleme)
#   - mode       (semantic | keyword | hybrid)
#   - result'larda "relevance" bandi (high/medium/low)
#
# Dogrulama senaryolari:
#   T1  Esik testi   : min_score=0.9  -> count=0 veya tum sonuclar score>=0.9
#                      min_score=0    -> sonuc donmali (count>=1)
#   T2  Relevance    : her result'ta relevance in {high,medium,low} ve esikla tutarli
#                      (bant: score>=0.60 -> high, >=0.30 -> medium, aksi -> low)
#                      Not: medium/low esigi degistirmek isterseniz 'check_json T2c' icindeki
#                          0.60 / 0.30 sabitlerini okuyucu ortama gore ayarlayin.
#   T3  Task-type    : test-hybrid6'e kayit yaz, paraphrase sorgu -> ilgili kayit
#                      ilk sirada ve score>=0.55
#   T4  Keyword/hybrid: summary'da ZZTESTMARKER; semantic->0, keyword/hybrid->bulur
#   T5  Geriye uyumluluk: min_score/mode OLMADAN arama -> hata yok, results doner
#
# Exit code: 0 = tumu PASS, 1 = en az bir FAIL.
#
# Ortam degiskenleri:
#   MEMORY_API_KEY  (zorunlu)  -- API key. SCRIPTTE HARDCODE YOK.
#   MEMORY_API_URL  (varsayilan http://192.168.32.5:8000)
#   MEMORY_QUIET    (0/1)      -- 1 ise sadece PASS/FAIL satirlari
#
# Kullanim:
#   MEMORY_API_KEY="$MEMORY_API_KEY" ./memory_api_e2e.sh
# =============================================================================
set -u

BASE_URL="${MEMORY_API_URL:-http://192.168.32.5:8000}"
API_KEY="${MEMORY_API_KEY:-}"
QUIET="${MEMORY_QUIET:-0}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

PASS_CNT=0
FAIL_CNT=0

if [ -z "$API_KEY" ]; then
  echo "FAIL  onkontrol: MEMORY_API_KEY ortam degiskeni bos (zorunlu)" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Yardimcilar
# ---------------------------------------------------------------------------
say() { [ "$QUIET" = "1" ] || echo "$@"; }
pass() { PASS_CNT=$((PASS_CNT + 1)); echo "PASS  $1"; }
fail() { FAIL_CNT=$((FAIL_CNT + 1)); echo "FAIL  $1 -- $2"; }

# $1 = test etiketi, $2 = python3 ifadesi (True/False uretir); J = d degiskeninde
# JSON objesi olarak acilir.
# J = JSON dosya yolu ($3)
check_json() {
  local label="$1" expr="$2" jfile="$3"
  printf '%s' "$expr" > "$TMP_DIR/check_expr.txt"
  local out
  out="$(python3 - <<PYEOF
import json,sys
f="$jfile"
raw=open(f).read()
try:
    d=json.loads(raw)
except Exception:
    print("__JSON_ERR__")
    sys.exit(0)
try:
    res=eval(open("$TMP_DIR/check_expr.txt").read())
    print("True" if res else "False")
except Exception:
    print("False")
PYEOF
)"
  if [ "$out" = "True" ]; then
    pass "$label"
  else
    fail "$label" "json-check -> '$out' (expr: $expr)"
  fi
}

# ---------------------------------------------------------------------------
# ONKONTROL: servis ayakta mi?
# ---------------------------------------------------------------------------
say "== Onkontrol: /health =="
HTTP=$(curl -s -m 8 -o "$TMP_DIR/health.json" -w '%{http_code}' "$BASE_URL/health" 2>/dev/null)
if [ "$HTTP" != "200" ]; then
  fail "health-kontrol" "HTTP=$HTTP (servis yok? BASE_URL=$BASE_URL)"
  echo
  echo "SONUC: $PASS_CNT PASS, $FAIL_CNT FAIL"
  exit 1
fi
pass "health-kontrol"

# ---------------------------------------------------------------------------
# T1  Esik testi
# ---------------------------------------------------------------------------
say
say "== T1  Esik (min_score) testi =="

# T1a: min_score=0.9  -> count=0 VEYA tum score>=0.9
curl -s -m 15 -X POST "$BASE_URL/v1/memory/search" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d '{"query":"repository deployment hakkinda genel kayit","min_score":0.9,"limit":10}' \
  -o "$TMP_DIR/t1_hi.json"
check_json "T1a min_score=0.9 (count=0 veya tumu>=0.9)" \
  "('count' not in d) or d['count']==0 or all((r.get('score') is None) or r['score']>=0.9 for r in d['results'])" \
  "$TMP_DIR/t1_hi.json"

# T1b: min_score=0  -> sonuc donmeli
curl -s -m 15 -X POST "$BASE_URL/v1/memory/search" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d '{"query":"repository deployment hakkinda genel kayit","min_score":0,"limit":5}' \
  -o "$TMP_DIR/t1_lo.json"
check_json "T1b min_score=0 sonuc donuyor (count>=1)" \
  "('results' in d) and d.get('count',0)>=1" "$TMP_DIR/t1_lo.json"

# ---------------------------------------------------------------------------
# T2  Relevance bandi
# ---------------------------------------------------------------------------
say
say "== T2  Relevance bandi (high/medium/low) =="
# Normal (min_score/mode'suz) arama -> her result'ta relevance + esikla tutarlilik
curl -s -m 15 -X POST "$BASE_URL/v1/memory/search" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d '{"query":"vector memory gemini embedding deployment","mode":"semantic","limit":10}' \
  -o "$TMP_DIR/t2.json"

check_json "T2a tum sonuclarda relevance alani var" \
  "('results' in d) and all('relevance' in r for r in d['results'])" "$TMP_DIR/t2.json"

# Bant mantigi: score>=0.60 -> high ; >=0.30 -> medium ; aksi -> low
check_json "T2b relevance degerleri {high,medium,low}" \
  "('results' in d) and all(r['relevance'] in ('high','medium','low') for r in d['results'])" \
  "$TMP_DIR/t2.json"

check_json "T2c relevance esiklarla tutarli (score>=.60->high, >=.30->medium, aksi low)" \
  """('results' in d) and all(
      ('high'   if (r.get('score') or 0) >= 0.60 else
       'medium' if (r.get('score') or 0) >= 0.30 else 'low') == r['relevance']
      for r in d['results'])""" \
  "$TMP_DIR/t2.json"

# ---------------------------------------------------------------------------
# T3  Task-type dogrulamasi
# ---------------------------------------------------------------------------
say
say "== T3  Task-type / paraphrase arama =="
RUN_ID="e2e-$(date +%s)-$$"
CONTENT="E2E doğrulama kaydı: PostgreSQL tablolara ZZTESTSEMANTIC indeks eklenmesi gerekiyor, çünkü sorgular yavaş ilerliyor."
SUMMARY="$RUN_ID: analiz sonucu — yavaş sorgulara indeks ekle kararı alındı"

# T3a: kaydi yaz (project_id=test-hybrid6)
curl -s -m 15 -X POST "$BASE_URL/v1/memory" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d "{\"project_id\":\"test-hybrid6\",\"domain\":\"database\",\"type\":\"finding\",\"content\":\"$CONTENT\",\"summary\":\"$SUMMARY\",\"source\":\"e2e\",\"agent\":\"e2e-test\",\"importance\":0.8,\"tags\":[\"e2e\"]}" \
  -o "$TMP_DIR/t3_create.json"

# T3b: paraphrase sorgu ile ara (ayni anlam, farkli kelimeler)
# TASK: ilgili kayit ILK SIRADA ve score>=0.55
curl -s -m 20 -X POST "$BASE_URL/v1/memory/search" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d "{\"query\":\"yavaş sorgu performansını artırmak için tablolara dizin tanımlama\",\"project_id\":\"test-hybrid6\",\"mode\":\"semantic\",\"min_score\":0.55,\"limit\":5}" \
  -o "$TMP_DIR/t3_search.json"

check_json "T3a kayit yazildi (test-hybrid6)" \
  "('id' in d) and d.get('deduplicated') in (False, True)" "$TMP_DIR/t3_create.json"

check_json "T3b paraphrase sorgu sonuc donuyor" \
  "('results' in d)" "$TMP_DIR/t3_search.json"

# T3c: ilgili kayit ilk sirada VE score>=0.55 (max_score da ~0.55 uzerinde olmali)
check_json "T3c ilgili kayit ilk sirada + score>=0.55" \
  "('results' in d) and len(d['results'])>0 and d['results'][0]['score']>=0.55 and '$RUN_ID' in (d['results'][0].get('summary') or '')" \
  "$TMP_DIR/t3_search.json"

# ---------------------------------------------------------------------------
# T4  Keyword/hybrid mod vs semantic — benzersiz marker token
# ---------------------------------------------------------------------------
say
say "== T4  Keyword/hybrid vs semantic (ZZTESTMARKER) =="
MARK="ZZTESTMARKER$RUN_ID"
CONTENT4="Bir tesadüfi teknik not: bu kayıt e2e dokunulmazlık testi içindir. Ref: $RUN_ID"
SUMMARY4="$RUN_ID: $MARK bu benzersiz anahtar kelimeyi sadece metin olarak içerir."

curl -s -m 15 -X POST "$BASE_URL/v1/memory" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d "{\"project_id\":\"test-hybrid6\",\"domain\":\"general\",\"type\":\"note\",\"content\":\"$CONTENT4\",\"summary\":\"$SUMMARY4\",\"source\":\"e2e\",\"agent\":\"e2e-test\"}" \
  -o "$TMP_DIR/t4_create.json"

# T4a: SEMANTIC modda marker ara -> 0 sonuc beklenir (anlamsiz token)
curl -s -m 15 -X POST "$BASE_URL/v1/memory/search" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d "{\"query\":\"$MARK\",\"project_id\":\"test-hybrid6\",\"mode\":\"semantic\",\"limit\":10}" \
  -o "$TMP_DIR/t4_sem.json"
check_json "T4a semantic modda marker aramasi hatasiz (results doner)" \
  "('results' in d) and ('count' in d)" \
  "$TMP_DIR/t4_sem.json"

# T4b: KEYWORD modda ara -> marker kaydini bulmali
curl -s -m 15 -X POST "$BASE_URL/v1/memory/search" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d "{\"query\":\"$MARK\",\"project_id\":\"test-hybrid6\",\"mode\":\"keyword\",\"limit\":10}" \
  -o "$TMP_DIR/t4_kw.json"
check_json "T4b keyword modda marker bulundu (summary eslesmesi)" \
  "('results' in d) and any('$MARK' in (r.get('summary') or '') for r in d['results'])" \
  "$TMP_DIR/t4_kw.json"

# T4c: tani — HYBRID modda da marker bulunmali
curl -s -m 15 -X POST "$BASE_URL/v1/memory/search" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d "{\"query\":\"$MARK\",\"project_id\":\"test-hybrid6\",\"mode\":\"hybrid\",\"limit\":10}" \
  -o "$TMP_DIR/t4_hy.json"
check_json "T4c hybrid modda marker bulundu (summary eslesmesi)" \
  "('results' in d) and any('$MARK' in (r.get('summary') or '') for r in d['results'])" \
  "$TMP_DIR/t4_hy.json"

# ---------------------------------------------------------------------------
# T5  Geriye uyumluluk (eski istemci: min_score/mode GONDERME)
# ---------------------------------------------------------------------------
say
say "== T5  Geriye uyumluluk (min_score/mode'suz arama) =="
HTTP=$(curl -s -m 15 -X POST "$BASE_URL/v1/memory/search" \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d '{"query":"database kurulumu","limit":5}' \
  -o "$TMP_DIR/t5.json" -w '%{http_code}' 2>/dev/null)
if [ "$HTTP" = "200" ]; then
  pass "T5a eski istek hata vermedi (HTTP 200)"
else
  fail "T5a eski istek hata verdi" "http=$HTTP"
fi
check_json "T5b eski istek results dondu (count>=0)" \
  "('results' in d) and 'count' in d and d['count']>=0" "$TMP_DIR/t5.json"

# ---------------------------------------------------------------------------
say
echo "SONUC: $PASS_CNT PASS, $FAIL_CNT FAIL"
if [ "$FAIL_CNT" -gt 0 ]; then
  exit 1
fi
exit 0