#!/usr/bin/env bash
# indoor_merge_all_sensors.sh — zjednodušená, mawk-kompatibilní verze
# Rozhodnutí formátu jen z POSLEDNÍHO datového řádku:
#  1) interpretace, která dává TODAY, je správná
#  2) záloha: pojistka >12 na posledním řádku
#  3) jinak FAIL
# Nově: řádky s OBOU null tokeny (temp i rh) se PŘESKAKUJÍ a na konci souboru se vypíše:
#   "Location <LOC> nemeri, zkontrolujte baterie"

set -euo pipefail

INPUT_GLOB="./latest/ThermoProSensor_export_*.csv"
OUTPUT="./gdrive/all_sensors_merged.csv"

# --- Konfig ---
SAMPLE_N="${SAMPLE_N:-5}"                         # kolik ukázek vstupu/výstupu vytisknout
TZ="${TZ:-Europe/Prague}"
TODAY="${TODAY:-$(TZ="$TZ" date +%Y-%m-%d)}"      # dnešní datum (YYYY-MM-DD)

# Null tokeny v měřeních
#  - řádky s OBOU null tokeny se přeskočí vždy (nové chování)
#  - řádky s JEDNÍM null tokenem se ponechají (NULL v CSV)
NULL_TOKEN_SAMPLE_N="${NULL_TOKEN_SAMPLE_N:-25}"  # kolik ukázek „null“ řádků vypsat (do logu)
NULL_TOKEN_DUMP="${NULL_TOKEN_DUMP:-0}"           # 1 = vypiš úplně všechny „null“ řádky

mkdir -p "$(dirname "$OUTPUT")"

shopt -s nullglob
files=( $INPUT_GLOB )
if [ ${#files[@]} -eq 0 ]; then
  echo "ℹ️ Žádné nové vstupy: $INPUT_GLOB"
  echo "Datetime,Temperature_Celsius,Relative_Humidity(%),Location" > "$OUTPUT"
  echo "Vytvořen prázdný výstup s hlavičkou"
  exit 0
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
    function epoch(y,m,d){ return mktime(sprintf("%04d %02d %02d 00 00 00", y,m,d)) }

    NR>2 {
      d=$1; t=$2; gsub(/^\xEF\xBB\xBF/,"",d)
      if (d ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/) {
        lastd=d; lastt=t
        p1=substr(d,1,2)+0; p2=substr(d,4,2)+0
        # sbíráme JEDNOZNAČNÝ důkaz pro fallback
        if (p1>12 && p2<=12) fmt_hint="DMY"
        else if (p2>12 && p1<=12) fmt_hint="MDY"
      }
    }
    END {
      if (lastd=="") { print "UNKNOWN"; exit }

      y=substr(lastd,7,4)+0
      p1=substr(lastd,1,2)+0
      p2=substr(lastd,4,2)+0

      yT=substr(TODAY,1,4)+0; mT=substr(TODAY,6,2)+0; dT=substr(TODAY,9,2)+0
      today_epoch = epoch(yT,mT,dT)
      week_start  = today_epoch - 6*86400
      day_end     = today_epoch + 86400 - 1

      mdv=valid(p2,p1); dmv=valid(p1,p2)
      md_y=y; md_m=p1; md_d=p2
      dm_y=y; dm_m=p2; dm_d=p1

      mdyn = mdv? ymd_num(md_y,md_m,md_d) : -1
      dmyn = dmv? ymd_num(dm_y,dm_m,dm_d) : -1

      md_ep = mdv? epoch(md_y,md_m,md_d) : -1
      dm_ep = dmv? epoch(dm_y,dm_m,dm_d) : -1

      printf("   Poslední řádek (raw): %s %s\n", lastd, lastt) > "/dev/stderr"
      if (mdv) printf("     • MDY → %04d-%02d-%02d %s (==TODAY? %s; in_last_week? %s)\n",
                      md_y,md_m,md_d,lastt, (mdyn==ymd_num(yT,mT,dT)?"ANO":"ne"),
                      (md_ep>=week_start && md_ep<=day_end ? "ANO":"ne")) > "/dev/stderr"
      else     printf("     • MDY → neplatné datum\n") > "/dev/stderr"
      if (dmv) printf("     • DMY → %04d-%02d-%02d %s (==TODAY? %s; in_last_week? %s)\n",
                      dm_y,dm_m,dm_d,lastt, (dmyn==ymd_num(yT,mT,dT)?"ANO":"ne"),
                      (dm_ep>=week_start && dm_ep<=day_end ? "ANO":"ne")) > "/dev/stderr"
      else     printf("     • DMY → neplatné datum\n") > "/dev/stderr"

      # 1) preferuj TODAY rozhodnutí
      if (mdyn==ymd_num(yT,mT,dT) && dmyn!=ymd_num(yT,mT,dT)) { print "MDY"; exit }
      if (dmyn==ymd_num(yT,mT,dT) && mdyn!=ymd_num(yT,mT,dT)) { print "DMY"; exit }

      # 2) pokud přesně jedna interpretace je v posledním týdnu (včetně dneška)
      inw_mdy = (md_ep>=week_start && md_ep<=day_end)
      inw_dmy = (dm_ep>=week_start && dm_ep<=day_end)
      if (inw_mdy && !inw_dmy) { print "MDY"; exit }
      if (inw_dmy && !inw_mdy) { print "DMY"; exit }

      # 3) fallback: jednoznačný důkaz z jiného řádku
      if (fmt_hint!="") { print fmt_hint; exit }

      # 4) ultimate fallback: lokální default (EU → DMY)
      printf("     • Fallback: žádný rozhodující signál, volím DMY (lokální default)\n") > "/dev/stderr"
      print "DMY"
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
        if (DUMP==1 || shown < '"$NULL_TOKEN_SAMPLE_N"') {
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
