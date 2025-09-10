#!/usr/bin/env bash
# indoor_merge_all_sensors.sh — robustní sloučení CSV z ThermoPro + autodetekce formátu datumu
# -----------------------------------------------------------------------------
# Funkce:
#  - Detekce MDY/DMY z POSLEDNÍHO řádku s datem + „poslední týden“ (včetně dneška)
#  - Doplňkově: počítá jednoznačné důkazy z CELÉHO souboru (p1>12 → DMY, p2>12 → MDY)
#  - Kontrola monotónnosti časové řady pro obě interpretace (počet „zlomů“)
#  - Přepínač STRICT (default 1 = fail‑fast). STRICT=0 → další heuristiky + fallback na FMT_DEFAULT
#  - Volitelný FORCE_FMT=DMY|MDY přebije autodetekci (pro všechny soubory)
#  - Řádky, kde TEMPERATURA i VLHKOST jsou NULL tokeny, se přeskočí + vypíše se hláška „Location X neměří“.
#  - Ukázky prvních/posledních řádků (SAMPLE_N)
#
# Požadavky: bash, awk, coreutils `date` (pro výpočet „posledního týdne“)
#
# Příklady:
#   STRICT=1 ./scripts/indoor_merge_all_sensors.sh
#   STRICT=0 FMT_DEFAULT=DMY ./scripts/indoor_merge_all_sensors.sh
#   FORCE_FMT=DMY ./scripts/indoor_merge_all_sensors.sh
#
# Kódy chyb:
#   0  OK
#   3  Nepodařilo se bezpečně určit formát (STRICT režim)
#   4  Ve výstupu se objevil měsíc > 12 (bezpečnostní check)
#   6  Načtena nečíselná hodnota temp/rh (vstupní chyba)
set -euo pipefail

# --- Konfig / ENV ---
INPUT_GLOB="${INPUT_GLOB:-./latest/ThermoProSensor_export_*.csv}"
OUTPUT="${OUTPUT:-./gdrive/all_sensors_merged.csv}"

SAMPLE_N="${SAMPLE_N:-5}"                         # kolik ukázek prvních/posledních řádků tisknout
TZ="${TZ:-Europe/Prague}"
TODAY="${TODAY:-$(TZ="$TZ" date +%Y-%m-%d)}"      # dnešní datum (YYYY-MM-DD)
STRICT="${STRICT:-1}"                              # 1 = fail-fast (nejbezpečnější), 0 = pokus o rozřešení + fallback
FMT_DEFAULT="${FMT_DEFAULT:-DMY}"                  # použito JEN when STRICT=0 a heuristiky selžou
FORCE_FMT="${FORCE_FMT:-}"                         # pokud nastaveno na DMY/MDY, detekce se přeskočí a použije se toto

# Null tokeny v měřeních
# - řádky s OBOU null tokeny se přeskočí vždy (nové chování)
# - řádky s JEDNÍM null tokenem se ponechají (NULL v CSV)
NULL_TOKEN_SAMPLE_N="${NULL_TOKEN_SAMPLE_N:-25}"   # kolik ukázek „null“ řádků vypsat (stderr)
NULL_TOKEN_DUMP="${NULL_TOKEN_DUMP:-0}"            # 1 = dump všech „null“ řádků

mkdir -p "$(dirname "$OUTPUT")"

shopt -s nullglob
files=( $INPUT_GLOB )
if [ ${#files[@]} -eq 0 ]; then
  echo "ℹ️ Žádné nové vstupy: $INPUT_GLOB"
  echo "Datetime,Temperature_Celsius,Relative_Humidity(%),Location" > "$OUTPUT"
  echo "Vytvořen prázdný výstup s hlavičkou"
  exit 0
fi

# Vypočti hranice „posledního týdne“ (inclusive) jako YYYYMMDD celá čísla – monotónní, snadno porovnatelné
week_start="$(TZ="$TZ" date -d "$TODAY -6 days" +%Y-%m-%d)"
to_ymd_int () { # $1=YYYY-MM-DD → echo YYYYMMDD
  echo "$1" | awk -F- '{ printf("%04d%02d%02d\n",$1,$2,$3) }'
}
TODAY_YMD_INT="$(to_ymd_int "$TODAY")"
WEEK_START_YMD_INT="$(to_ymd_int "$week_start")"

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

# Detekce formátu z CELÉHO souboru s prioritami:
#  1) poslední řádek == TODAY (jediná interpretace)
#  2) poslední řádek ∈ [dnes-6, dnes] (jediná interpretace)
#  3) většina jednoznačných důkazů z celého souboru (p1>12 → DMY; p2>12 → MDY)
#  4) méně „zlomů“ monotónnosti pod danou interpretací (MDY/DMY)
#  5) STRICT=1 → UNKNOWN, STRICT=0 → FMT_DEFAULT
detect_fmt_from_file () {
  local f="$1" strict="$2" fmt_default="$3"
  awk -F, \
      -v TODAY_YMD="$TODAY_YMD_INT" \
      -v WEEK_START_YMD="$WEEK_START_YMD_INT" \
      -v STRICT="$strict" \
      -v FMT_DEFAULT="$fmt_default" \
  '
    function valid(d,m){ if(m<1||m>12||d<1||d>31) return 0; if((m==4||m==6||m==9||m==11)&&d>30) return 0; if(m==2&&d>29) return 0; return 1 }
    function ymd_num(y,m,d){ return y*10000+m*100+d }
    function ts_num(y,m,d,H,M,S){ return (ymd_num(y,m,d)*1000000 + H*10000 + M*100 + S) }

    NR>2 {
      date=$1; time=$2; gsub(/^\xEF\xBB\xBF/, "", date)
      if (date ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ && time ~ /^[0-9]{1,2}:[0-9]{2}(:[0-9]{2})?$/) {
        last_date = date; last_time = time
        p1=substr(date,1,2)+0; p2=substr(date,4,2)+0; y=substr(date,7,4)+0
        split(time,t,":"); H=t[1]+0; M=t[2]+0; S=(t[3]?t[3]+0:0)

        # Jednoznačné důkazy (p1>12 → DMY, p2>12 → MDY)
        if (p1>12 && p2<=12) hint_dmy++
        else if (p2>12 && p1<=12) hint_mdy++

        # Kandidátní parsování
        if (valid(p2,p1)) {
          ts_mdy = ts_num(y,p1,p2,H,M,S)
          if (prev_mdy>0 && ts_mdy<prev_mdy) breaks_mdy++
          prev_mdy = ts_mdy
          ymd_mdy = ymd_num(y,p1,p2)
          # Počítat i globální „v posledním týdnu“ by šlo, ale stačí nám poslední řádek
        }
        if (valid(p1,p2)) {
          ts_dmy = ts_num(y,p2,p1,H,M,S)
          if (prev_dmy>0 && ts_dmy<prev_dmy) breaks_dmy++
          prev_dmy = ts_dmy
          ymd_dmy = ymd_num(y,p2,p1)
        }
      }
    }
    END {
      if (last_date=="") { print "UNKNOWN"; exit } # žádná data

      y=substr(last_date,7,4)+0
      p1=substr(last_date,1,2)+0; p2=substr(last_date,4,2)+0
      split(last_time,t,":"); H=t[1]+0; M=t[2]+0; S=(t[3]?t[3]+0:0)

      mdv=valid(p2,p1); dmv=valid(p1,p2)
      md_last_ymd = (mdv? ymd_num(y,p1,p2): -1)
      dm_last_ymd = (dmv? ymd_num(y,p2,p1): -1)

      printf("   Poslední řádek (raw): %s %s\n", last_date, last_time) > "/dev/stderr"
      if (mdv) printf("     • MDY → %04d-%02d-%02d %s (==TODAY? %s; in_last_week? %s)\n",
                      y,p1,p2,last_time,
                      (md_last_ymd==TODAY_YMD?"ANO":"ne"),
                      (md_last_ymd>=WEEK_START_YMD && md_last_ymd<=TODAY_YMD ? "ANO":"ne")) > "/dev/stderr"
      else     printf("     • MDY → neplatné datum\n") > "/dev/stderr"
      if (dmv) printf("     • DMY → %04d-%02d-%02d %s (==TODAY? %s; in_last_week? %s)\n",
                      y,p2,p1,last_time,
                      (dm_last_ymd==TODAY_YMD?"ANO":"ne"),
                      (dm_last_ymd>=WEEK_START_YMD && dm_last_ymd<=TODAY_YMD ? "ANO":"ne")) > "/dev/stderr"
      else     printf("     • DMY → neplatné datum\n") > "/dev/stderr"

      printf("     • Evidence: hints DMY=%d, MDY=%d | breaks DMY=%d, MDY=%d\n",
             hint_dmy+0, hint_mdy+0, breaks_dmy+0, breaks_mdy+0) > "/dev/stderr"

      # 1) preferuj TODAY (poslední řádek)
      if (md_last_ymd==TODAY_YMD && dm_last_ymd!=TODAY_YMD) { print "MDY"; exit }
      if (dm_last_ymd==TODAY_YMD && md_last_ymd!=TODAY_YMD) { print "DMY"; exit }

      # 2) pokud právě jedna interpretace je v posledním týdnu (včetně dneška)
      inw_mdy = (md_last_ymd>=WEEK_START_YMD && md_last_ymd<=TODAY_YMD)
      inw_dmy = (dm_last_ymd>=WEEK_START_YMD && dm_last_ymd<=TODAY_YMD)
      if (inw_mdy && !inw_dmy) { print "MDY"; exit }
      if (inw_dmy && !inw_mdy) { print "DMY"; exit }

      # 3) většina jednoznačných důkazů z CELÉHO souboru
      if ((hint_dmy+0)>(hint_mdy+0)) { print "DMY"; exit }
      if ((hint_mdy+0)>(hint_dmy+0)) { print "MDY"; exit }

      # 4) méně zlomů monotónnosti
      if ((breaks_dmy+0)<(breaks_mdy+0)) { print "DMY"; exit }
      if ((breaks_mdy+0)<(breaks_dmy+0)) { print "MDY"; exit }

      # 5) Strictness
      if (STRICT+0==1) {
        printf("     • Fallback: nejednoznačné → STRICT=1 → vracím UNKNOWN (bezpečný fail)\n") > "/dev/stderr"
        print "UNKNOWN"; exit
      } else {
        printf("     • Fallback: nejednoznačné → STRICT=0 → volím FMT_DEFAULT=%s\n", FMT_DEFAULT) > "/dev/stderr"
        print FMT_DEFAULT; exit
      }
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

  # FORCE_FMT má absolutní prioritu
  if [ -n "$FORCE_FMT" ]; then
    fmt="$FORCE_FMT"
    echo "   => Přepsáno FORCE_FMT: $fmt"
  else
    fmt="$(detect_fmt_from_file "$file" "$STRICT" "$FMT_DEFAULT")"
    echo "   => Určený formát: $fmt"
  fi

  if [ "$fmt" = "UNKNOWN" ]; then
    echo "❌ Nelze spolehlivě určit formát (MDY/DMY). Končím (STRICT režim)."
    exit 3
  fi

  out_tmp="$tmpdir/out_$idx.csv"
  awk -v OFS="," \
      -v loc="$location" -v fmt="$fmt" -v SRC="$file" \
      -v SAMPLE="$NULL_TOKEN_SAMPLE_N" -v DUMP="$NULL_TOKEN_DUMP" '
    function trim(s){ sub(/^ +/,"",s); sub(/ +$/,"",s); return s }
    function is_num(s){ return (s ~ /^-?[0-9]+([.][0-9]+)?$/) }
    function is_null_tok(s,  u){ s=trim(s); u=toupper(s); return (s=="" || s=="-" || u=="NA" || u=="N/A" || u=="NULL") }

    BEGIN { FS=","; null_any=0; both_null=0; shown=0 }
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

      nt=is_null_tok(temp); nr=is_null_tok(rh)
      had_any = (nt || nr)
      had_both = (nt && nr)

      if (nt) temp=""
      if (nr) rh=""

      datetime = sprintf("%04d-%02d-%02d %s:%s:%s", year, month, day, hour, minute, second)

      if (had_any) {
        null_any++
        if (DUMP==1 || shown < '"${NULL_TOKEN_SAMPLE_N}"') {
          shown++
          printf("  == NULL TOKEN (file=%s line=%d)\n    input:  \"%s,%s,%s,%s\"\n", SRC, NR, $1,$2,raw_temp,raw_rh) > "/dev/stderr"
          printf("    output: \"%s,%s,%s,%s\"%s\n",
                 datetime, (temp==""?"":temp), (rh==""?"":rh), loc,
                 (had_both?"  [SKIP]":"")) > "/dev/stderr"
        }
      }

      # Pokud obě hodnoty chybí -> PŘESKOČIT
      if (had_both) { both_null++; next }

      # přísnost na jiné nečíselné řetězce (ponecháme základní kontrolu)
      if (temp!="" && !is_num(temp)) { printf("  !! non_numeric temp | file=%s | raw=\"%s,%s,%s,%s\"\n", SRC,$1,$2,raw_temp,raw_rh) > "/dev/stderr"; exit 6 }
      if (rh  !="" && !is_num(rh))   { printf("  !! non_numeric  rh | file=%s | raw=\"%s,%s,%s,%s\"\n", SRC,$1,$2,raw_temp,raw_rh) > "/dev/stderr"; exit 6 }

      print datetime, temp, rh, loc >> "'"$out_tmp"'"
    }

    END {
      if (both_null > 0) {
        # Žádaná hláška do terminálu (jednou za soubor/location)
        printf("Location %s nemeri, zkontrolujte baterie\n", loc) > "/dev/stderr"
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
