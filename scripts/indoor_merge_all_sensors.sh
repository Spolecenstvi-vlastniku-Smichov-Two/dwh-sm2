#!/usr/bin/env bash
# indoor_merge_all_sensors.sh — zjednodušená, mawk-kompatibilní verze
# Rozhodnutí formátu jen z POSLEDNÍHO datového řádku:
#  1) interpretace, která dává TODAY, je správná
#  2) záloha: pojistka >12 na posledním řádku
#  3) jinak FAIL
# Loguje head/tail vstupu, diagnostiku posledního řádku, ukázky null-token řádků a head/tail výstupu.

set -euo pipefail

INPUT_GLOB="./latest/ThermoProSensor_export_*.csv"
OUTPUT="./gdrive/all_sensors_merged.csv"

# --- Konfig ---
SAMPLE_N="${SAMPLE_N:-5}"                         # kolik ukázek vstupu/výstupu vytisknout
TZ="${TZ:-Europe/Prague}"
TODAY="${TODAY:-$(TZ="$TZ" date +%Y-%m-%d)}"      # dnešní datum (YYYY-MM-DD)

# Null tokeny v měřeních
ALLOW_NULL_TOKENS="${ALLOW_NULL_TOKENS:-0}"       # 0 = fail-fast na '-', 'NA', 'N/A', 'NULL'
NULL_TOKEN_SAMPLE_N="${NULL_TOKEN_SAMPLE_N:-25}"  # kolik ukázek „null“ řádků vypsat
NULL_TOKEN_DUMP="${NULL_TOKEN_DUMP:-0}"           # 1 = vypiš úplně všechny „null“ řádky

mkdir -p "$(dirname "$OUTPUT")"

shopt -s nullglob
files=( $INPUT_GLOB )
if [ ${#files[@]} -eq 0 ]; then
  echo "❗ Nenalezeny vstupní soubory: $INPUT_GLOB"
  exit 2
fi

# Head/Tail vstupu bez 'tac'
print_input_samples () {
  local f="$1"
  echo "   Vstup – první ${SAMPLE_N} datových řádků:"
  awk -v n="$SAMPLE_N" '
    NR>2 { gsub(/^\xEF\xBB\xBF/, "", $0); print; if (++c==n) exit }
  ' "$f" || true
  echo "   Vstup – posledních ${SAMPLE_N} datových řádků:"
  awk -v n="$SAMPLE_N" '
    NR>2 { gsub(/^\xEF\xBB\xBF/, "", $0); buf[++c]=$0 }
    END { if(!c) exit; s=(c>n?c-n+1:1); for(i=s;i<=c;i++) print buf[i] }
  ' "$f" || true
}

# Detekce formátu pouze z POSLEDNÍHO datového řádku
detect_fmt_from_last () {
  local f="$1"
  awk -F, -v TODAY="$TODAY" '
    function valid(d,m){ if(m<1||m>12||d<1||d>31) return 0; if((m==4||m==6||m==9||m==11)&&d>30) return 0; if(m==2&&d>29) return 0; return 1 }
    function ymd_num(y,m,d){ return y*10000+m*100+d }
    NR>2 {
      d=$1; t=$2; gsub(/^\xEF\xBB\xBF/,"",d)
      if (d ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/) { lastd=d; lastt=t }
    }
    END {
      if (lastd=="") { print "UNKNOWN"; exit }
      y=substr(lastd,7,4)+0
      p1=substr(lastd,1,2)+0  # první dvojice
      p2=substr(lastd,4,2)+0  # druhá dvojice
      # diagnostika
      yT=substr(TODAY,1,4)+0; mT=substr(TODAY,6,2)+0; dT=substr(TODAY,9,2)+0
      today=ymd_num(yT,mT,dT)
      mdv=valid(p2,p1); dmv=valid(p1,p2)
      mdyn = mdv? ymd_num(y,p1,p2) : -1
      dmyn = dmv? ymd_num(y,p2,p1) : -1

      # tisk do stderr
      printf("   Poslední řádek (raw): %s %s\n", lastd, lastt) > "/dev/stderr"
      if (mdv) printf("     • MDY → %04d-%02d-%02d %s (==TODAY? %s)\n", y,p1,p2,lastt, (mdyn==today?"ANO":"ne")) > "/dev/stderr"
      else     printf("     • MDY → neplatné datum\n") > "/dev/stderr"
      if (dmv) printf("     • DMY → %04d-%02d-%02d %s (==TODAY? %s)\n", y,p2,p1,lastt, (dmyn==today?"ANO":"ne")) > "/dev/stderr"
      else     printf("     • DMY → neplatné datum\n") > "/dev/stderr"

      # 1) shoda s TODAY
      if (mdyn==today && dmyn!=today) { print "MDY"; exit }
      if (dmyn==today && mdyn!=today) { print "DMY"; exit }

      # 2) pojistka >12 na posledním řádku
      if (p1>12 && p2<=12) { print "DMY"; exit }
      if (p2>12 && p1<=12) { print "MDY"; exit }

      print "UNKNOWN"
    }
  ' "$f"
}

# ==== hlavní běh ====
tmpdir="$(mktemp -d)"
rm -f "$OUTPUT"
first=1
total_lines=0
idx=0

for file in "${files[@]}"; do
  idx=$((idx+1))
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📄 [$idx/${#files[@]}] Zpracovávám: $file"
  location="$(basename "$file" | awk -F'_' '{print $3}')"
  echo "   Location: $location"

  print_input_samples "$file"

  fmt="$(detect_fmt_from_last "$file")"
  echo "   => Určený formát: $fmt"
  if [ "$fmt" = "UNKNOWN" ]; then
    echo "❌ Nelze spolehlivě určit formát (MDY/DMY) z posledního řádku. Končím."
    exit 3
  fi

  out_tmp="$tmpdir/out_$idx.csv"
  awk -v OFS="," \
      -v loc="$location" -v fmt="$fmt" -v SRC="$file" \
      -v SAMPLE="$NULL_TOKEN_SAMPLE_N" -v DUMP="$NULL_TOKEN_DUMP" -v ALLOW="$ALLOW_NULL_TOKENS" '
    function trim(s){ sub(/^ +/,"",s); sub(/ +$/,"",s); return s }
    function is_num(s){ return (s ~ /^-?[0-9]+([.][0-9]+)?$/) }
    function is_null_tok(s,  u){ s=trim(s); u=toupper(s); return (s=="" || s=="-" || u=="NA" || u=="N/A" || u=="NULL") }

    BEGIN { FS=","; null_hits=0; shown=0 }
    NR <= 2 { next }
    { gsub(/^\xEF\xBB\xBF/, "", $1) }

    $1 ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ && $2 ~ /^[0-9]{1,2}:[0-9]{2}(:[0-9]{2})?$/ {
      split($1, d, "/")
      day   = (fmt=="DMY" ? d[1]+0 : d[2]+0)
      month = (fmt=="DMY" ? d[2]+0 : d[1]+0)
      year  = d[3]+0

      split($2, t, ":")
      hour   = sprintf("%02d", t[1])
      minute = sprintf("%02d", t[2])
      second = (t[3] ? sprintf("%02d", t[3]) : "00")

      raw_temp=$3; raw_rh=$4
      temp=trim(raw_temp); rh=trim(raw_rh)

      had_null=0
      if (is_null_tok(temp)) { temp=""; had_null=1 }
      if (is_null_tok(rh))   { rh  =""; had_null=1 }

      datetime = sprintf("%04d-%02d-%02d %s:%s:%s", year, month, day, hour, minute, second)

      if (had_null) {
        null_hits++
        if (DUMP==1 || shown < SAMPLE) {
          shown++
          printf("  == NULL TOKEN (file=%s line=%d)\n    input:  \"%s,%s,%s,%s\"\n", SRC, NR, $1,$2,raw_temp,raw_rh) > "/dev/stderr"
          printf("    output: \"%s,%s,%s,%s\"\n", datetime, (temp==""?"":temp), (rh==""?"":rh), loc) > "/dev/stderr"
        }
      }

      if (temp!="" && !is_num(temp)) { printf("  !! non_numeric temp | file=%s | raw=\"%s,%s,%s,%s\"\n", SRC,$1,$2,raw_temp,raw_rh) > "/dev/stderr"; exit 6 }
      if (rh  !="" && !is_num(rh))   { printf("  !! non_numeric  rh | file=%s | raw=\"%s,%s,%s,%s\"\n", SRC,$1,$2,raw_temp,raw_rh) > "/dev/stderr"; exit 6 }

      print datetime, temp, rh, loc >> "'"$out_tmp"'"
    }

    END {
      if (null_hits > 0) {
        printf("   — Souhrn null tokenů v souboru: %d řádků.%s\n",
               null_hits, (ALLOW?" Pokračuji (ALLOW_NULL_TOKENS=1).":"")) > "/dev/stderr"
        if (!ALLOW) {
          printf("❌ Nalezeny null tokeny (\"-\", \"NA\", \"N/A\", \"NULL\"). Selhávám (ALLOW_NULL_TOKENS=0).\n") > "/dev/stderr"
          exit 5
        }
      }
    }
  ' "$file"

  lines=$(awk 'NR>2{c++} END{print c+0}' "$file")
  echo "   Přidáno řádků (vstupních): $lines"
  total_lines=$((total_lines + lines))
done

echo "Datetime,Temperature_Celsius,Relative_Humidity(%),Location" > "$OUTPUT"
cat "$tmpdir"/out_*.csv >> "$OUTPUT"

echo ""
echo "✅ Hotovo. Celkem sloučeno řádků: $total_lines"
echo "🗂️ Výstup – prvních ${SAMPLE_N} řádků:"
head -n $((SAMPLE_N+1)) "$OUTPUT" || true
echo "   Výstup – posledních ${SAMPLE_N} řádků:"
tail -n "$SAMPLE_N" "$OUTPUT" || true

# Bezpečnostní kontrola: v Datetime nesmí být měsíc > 12
badm=$(awk -F, 'NR>1{split($1,a,/[- :]/); if(a[2]>12) c++} END{print c+0}' "$OUTPUT")
if [ "$badm" -gt 0 ]; then
  echo "❗ Neočekávané: ve výstupu je $badm řádků s měsícem > 12. Selhávám."
  exit 4
fi

echo "🎉 Dokončeno bez chyb."
