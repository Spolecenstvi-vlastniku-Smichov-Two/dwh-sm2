#!/usr/bin/env bash
# indoor_merge_all_sensors.sh — robustní detekce formátu datumu (MDY vs DMY)
# Pravidla:
#  0) Pojistka >12 (okamžité vyloučení)
#  1) Max datum == dnešní datum (preferovaná jistota)
#  2) Pomalost změny: pozice s menším počtem unikátů je měsíc
# Pokud je i tak výsledek neurčitý -> FAIL (raději skončit než zničit data).
#
# Loguje vzorky vstupu (head/tail) i výstupu a shrnutí detekce.

set -euo pipefail

INPUT_GLOB="./latest/ThermoProSensor_export_*.csv"
OUTPUT="./gdrive/all_sensors_merged.csv"

# --- Konfigurovatelné přes env ---
SAMPLE_N="${SAMPLE_N:-5}"                 # kolik ukázek (head/tail) ukázat na vstupu i výstupu
TZ="${TZ:-Europe/Prague}"                 # časová zóna
TODAY="${TODAY:-$(TZ="$TZ" date +%Y-%m-%d)}"   # dnešní datum (lze přepsat env TODAY=YYYY-MM-DD)

mkdir -p "$(dirname "$OUTPUT")"

# Rychlé selhání, pokud nejsou vstupy
shopt -s nullglob
files=( $INPUT_GLOB )
if [ ${#files[@]} -eq 0 ]; then
  echo "❗ Nenalezeny žádné vstupní soubory: $INPUT_GLOB"
  exit 2
fi

# ---- Funkce: vytiskni vzorek vstupu (po přeskočení 2 řádků popisu/hlavičky) ----
print_input_samples () {
  local f="$1"
  echo "   Vstup – první ${SAMPLE_N} datových řádků:"
  awk -v n="$SAMPLE_N" 'NR>2{print; if(++c==n) exit}' "$f" || true
  echo "   Vstup – posledních ${SAMPLE_N} datových řádků:"
  # pokud je soubor krátký, tail může vrátit i hlavičky, proto filtr NR>2:
  tac "$f" | awk 'NR>2 && $0!=""{buf[bufc++]=$0} END{for(i=bufc-1, c=0; i>=0 && c<ENVIRON["SAMPLE_N"]; i--, c++) print buf[i]}' || true
}

# ---- Funkce: počáteční rychlá „pojistka >12“ (DN/MD) ----
force_by_gt12 () {
  local f="$1"
  awk -F, '
    BEGIN{ d1gt=0; d2gt=0 }
    NR>2{
      d=$1; gsub(/^\xEF\xBB\xBF/,"",d)
      if (d ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/) {
        p1=substr(d,1,2)+0; p2=substr(d,4,2)+0
        if (p1>12) d1gt++
        if (p2>12) d2gt++
      }
    }
    END{
      if (d1gt>0 && d2gt==0) print "DMY";      # první pozice >12 => musí být den => DMY
      else if (d2gt>0 && d1gt==0) print "MDY"; # druhá pozice >12 => musí být den => MDY
      else print "UNKNOWN"
      # pro diagnostiku:
      # printf("DBG_GT12 p1>%s p2>%s\n", d1gt, d2gt) > "/dev/stderr"
    }
  ' "$f"
}

# ---- Funkce: rozhodnutí dle "max datum == TODAY" ----
by_today_match () {
  local f="$1" today="$2"
  awk -F, -v TODAY="$today" '
    function max(a,b){return (a>b)?a:b}
    function ymd_num(y,m,d){ return y*10000 + m*100 + d }
    BEGIN{ max_mdy=0; max_dmy=0 }
    NR>2{
      d=$1; gsub(/^\xEF\xBB\xBF/,"",d)
      if (d ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/) {
        y=substr(d,7,4)+0
        p1=substr(d,1,2)+0
        p2=substr(d,4,2)+0
        # MDY: month=p1, day=p2
        v_mdy = ymd_num(y, p1, p2)
        # DMY: month=p2, day=p1
        v_dmy = ymd_num(y, p2, p1)
        if (v_mdy > max_mdy) max_mdy = v_mdy
        if (v_dmy > max_dmy) max_dmy = v_dmy
      }
    }
    END{
      y=substr(TODAY,1,4)+0; m=substr(TODAY,6,2)+0; d=substr(TODAY,9,2)+0
      today_num = y*10000 + m*100 + d
      if (max_mdy==today_num && max_dmy!=today_num) print "MDY"
      else if (max_dmy==today_num && max_mdy!=today_num) print "DMY"
      else print "UNKNOWN"
    }
  ' "$f"
}

# ---- Funkce: „pomalost změny“ – méně unikátů určí měsíc ----
by_slow_change () {
  local f="$1"
  awk -F, '
    BEGIN{ split("",u1); split("",u2) }
    NR>2{
      d=$1; gsub(/^\xEF\xBB\xBF/,"",d)
      if (d ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/) {
        p1=substr(d,1,2)
        p2=substr(d,4,2)
        u1[p1]=1
        u2[p2]=1
      }
    }
    END{
      c1=0; for (k in u1) c1++
      c2=0; for (k in u2) c2++
      if (c1<c2) print "MDY";     # 1. pozice se mění pomaleji => měsíc => MDY
      else if (c2<c1) print "DMY" # 2. pozice se mění pomaleji => měsíc => DMY
      else print "UNKNOWN"
    }
  ' "$f"
}

# ---- Funkce: diagnostika (pro log) – ukáže i max MDY/DMY ----
print_detect_diag () {
  local f="$1" today="$2"
  awk -F, -v TODAY="$today" '
    function ymd(y,m,d){ return sprintf("%04d-%02d-%02d", y,m,d) }
    function ymd_num(y,m,d){ return y*10000 + m*100 + d }
    BEGIN{
      d1gt=0; d2gt=0; max_mdy=0; max_dmy=0
    }
    NR>2{
      d=$1; gsub(/^\xEF\xBB\xBF/,"",d)
      if (d ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/) {
        y=substr(d,7,4)+0
        p1=substr(d,1,2)+0
        p2=substr(d,4,2)+0
        if (p1>12) d1gt++
        if (p2>12) d2gt++
        vm=ymd_num(y,p1,p2)
        vd=ymd_num(y,p2,p1)
        if (vm>max_mdy) { max_mdy=vm; y_m=y; m_m=p1; d_m=p2 }
        if (vd>max_dmy) { max_dmy=vd; y_d=y; m_d=p2; d_d=p1 }
        u1[p1]=1; u2[p2]=1
      }
    }
    END{
      c1=0; for (k in u1) c1++
      c2=0; for (k in u2) c2++
      printf "   Diagnostika:\n"
      printf "     • Pojistka >12:  pos1>12=%d  pos2>12=%d\n", d1gt, d2gt
      if (max_mdy>0) printf "     • Max (MDY): %s\n", ymd(y_m,m_m,d_m)
      if (max_dmy>0) printf "     • Max (DMY): %s\n", ymd(y_d,m_d,d_d)
      printf "     • Dnešek: %s\n", TODAY
      printf "     • Unikáty: pos1=%d  pos2=%d\n", c1, c2
    }
  ' "$f"
}

# ---- Funkce: finální rozhodnutí o formátu pro soubor ----
guess_date_format () {
  local f="$1"

  # 0) pojistka >12
  local fast
  fast="$(force_by_gt12 "$f")"
  if [ "$fast" != "UNKNOWN" ]; then
    echo "$fast"
    return
  fi

  # 1) max == TODAY
  local bytoday
  bytoday="$(by_today_match "$f" "$TODAY")"
  if [ "$bytoday" != "UNKNOWN" ]; then
    echo "$bytoday"
    return
  fi

  # 2) pomalost změny
  local slow
  slow="$(by_slow_change "$f")"
  if [ "$slow" != "UNKNOWN" ]; then
    echo "$slow"
    return
  fi

  echo "UNKNOWN"
}

# ====== Hlavní běh ======
rm -f "$OUTPUT"
first=1
total_lines=0
idx=0

for file in "${files[@]}"; do
  idx=$((idx+1))
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📄 [$idx/${#files[@]}] Zpracovávám: $file"
  location="$(basename "$file" | awk -F'_' '{print $3}')"
  echo "   Location: $location"

  # vzorky vstupu
  print_input_samples "$file"

  # diagnostika a rozhodnutí
  print_detect_diag "$file" "$TODAY"
  fmt="$(guess_date_format "$file")"
  echo "   => Určený formát: $fmt"

  if [ "$fmt" = "UNKNOWN" ]; then
    echo "❌ Nedokážu spolehlivě určit formát (MDY/DMY). Skript končí (fail-fast)."
    echo "   Tip: je v souboru jen jediný den a není to dnešek? Pak pravidla 1/2 nejsou průkazná."
    exit 3
  fi

  # zápis hlavičky
  if [ $first -eq 1 ]; then
    echo "Datetime,Temperature_Celsius,Relative_Humidity(%),Location" > "$OUTPUT"
    first=0
  fi

  # převod (podporujeme i HH:MM:SS)
  awk -v OFS="," -v loc="$location" -v fmt="$fmt" '
    BEGIN { FS="," }
    NR <= 2 { next }  # přeskočit popis + hlavičku
    {
      gsub(/^\xEF\xBB\xBF/, "", $1)
    }
    NF && $1 ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ && $2 ~ /^[0-9]{1,2}:[0-9]{2}(:[0-9]{2})?$/ {
      split($1, d, "/")
      day   = (fmt == "DMY" ? d[1]+0 : d[2]+0)
      month = (fmt == "DMY" ? d[2]+0 : d[1]+0)
      year  = d[3]+0

      split($2, t, ":")
      hour   = sprintf("%02d", t[1])
      minute = sprintf("%02d", t[2])
      second = (t[3] ? sprintf("%02d", t[3]) : "00")

      datetime = sprintf("%04d-%02d-%02d %s:%s:%s", year, month, day, hour, minute, second)
      print datetime, $3, $4, loc
    }
  ' "$file" >> "$OUTPUT"

  lines=$(awk 'NR > 2' "$file" | wc -l)
  echo "   Přidáno řádků (vstupních): $lines"
  total_lines=$((total_lines + lines))
done

echo ""
echo "✅ Hotovo. Celkem sloučeno řádků: $total_lines"
echo "🗂️ Výstupní soubor: $OUTPUT"
echo "   Výstup – prvních ${SAMPLE_N} řádků:"
head -n $((SAMPLE_N+1)) "$OUTPUT" || true
echo "   Výstup – posledních ${SAMPLE_N} řádků:"
tail -n "$SAMPLE_N" "$OUTPUT" || true

# Bezpečnostní kontrola: v Datetime nesmí být měsíc > 12
badm=$(awk -F, 'NR>1 { split($1,a,/[- :]/); if (a[2]>12) c++ } END{print c+0}' "$OUTPUT")
if [ "$badm" -gt 0 ]; then
  echo "❗ Neočekávané: ve výstupu je $badm řádků s měsícem > 12. Selhávám."
  exit 4
fi

echo "🎉 Dokončeno bez chyb."
