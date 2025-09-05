#!/usr/bin/env bash
# indoor_merge_all_sensors.sh — robustní detekce formátu datumu (MDY vs DMY)
# Pravidla:
#  0) Pojistka >12 (okamžité vyloučení)
#  1) Max datum == dnešní datum (preferovaná jistota)
#  2) Pomalost změny: pozice s menším počtem unikátů je měsíc
# Pokud je i tak výsledek neurčitý -> FAIL (raději skončit než zničit data).
#
# Loguje vzorky vstupu (head/tail) i výstupu a shrnutí detekce.
# Null tokeny ('-', 'NA', 'N/A', 'NULL') se mapují na prázdno; defaultně fail-fast.
# Přepínače:
#   ALLOW_NULL_TOKENS=1      … pouze zaloguje, neukončí s chybou
#   NULL_TOKEN_SAMPLE_N=25   … počet ukázek do logu
#   NULL_TOKEN_DUMP=1        … vypíše všechny řádky s null tokeny (pozor na objem logu)

set -euo pipefail

INPUT_GLOB="./latest/ThermoProSensor_export_*.csv"
OUTPUT="./gdrive/all_sensors_merged.csv"

# --- Konfigurovatelné přes env ---
SAMPLE_N="${SAMPLE_N:-5}"                         # kolik ukázek vstupu/výstupu ukázat
TZ="${TZ:-Europe/Prague}"                         # časová zóna
TODAY="${TODAY:-$(TZ="$TZ" date +%Y-%m-%d)}"      # dnešní datum (lze přepsat env TODAY=YYYY-MM-DD)

# Null-token logging & policy
ALLOW_NULL_TOKENS="${ALLOW_NULL_TOKENS:-0}"       # 0 = fail-fast, 1 = jen loguj
NULL_TOKEN_SAMPLE_N="${NULL_TOKEN_SAMPLE_N:-25}"  # ukázky na soubor
NULL_TOKEN_DUMP="${NULL_TOKEN_DUMP:-0}"           # 1 = vypiš všechny výskyty

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
  awk -v n="$SAMPLE_N" '
    NR>2 {
      gsub(/^\xEF\xBB\xBF/, "", $0)  # očista BOM pro hezký výpis
      print
      if (++c == n) exit
    }
  ' "$f" || true

  echo "   Vstup – posledních ${SAMPLE_N} datových řádků:"
  awk -v n="$SAMPLE_N" '
    NR>2 {
      gsub(/^\xEF\xBB\xBF/, "", $0)
      buf[++c] = $0
    }
    END {
      if (c == 0) exit
      start = (c > n ? c - n + 1 : 1)
      for (i = start; i <= c; i++) print buf[i]
    }
  ' "$f" || true
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
      if (d1gt>0 && d2gt==0) print "DMY";      # první pozice >12 => den => DMY
      else if (d2gt>0 && d1gt==0) print "MDY"; # druhá pozice >12 => den => MDY
      else print "UNKNOWN"
    }
  ' "$f"
}

# ---- Funkce: validátor (použijeme ve více awk blocích) ----
awk_valid_fn='
  function valid(d,m){ if(m<1||m>12||d<1||d>31) return 0; if((m==4||m==6||m==9||m==11)&&d>30) return 0; if(m==2&&d>29) return 0; return 1 }
'

# ---- Funkce: rozhodnutí dle "max datum == TODAY" (bere jen validní kombinace) ----
by_today_match () {
  local f="$1" today="$2"
  awk -F, -v TODAY="$today" "$awk_valid_fn
    function ymd_num(y,m,d){ return y*10000 + m*100 + d }
    BEGIN{ max_mdy=0; max_dmy=0 }
    NR>2{
      d=$1; gsub(/^\xEF\xBB\xBF/,"",d)
      if (d ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/) {
        y=substr(d,7,4)+0
        p1=substr(d,1,2)+0
        p2=substr(d,4,2)+0
        # MDY: month=p1, day=p2
        if (valid(p2,p1)) {
          v_mdy = ymd_num(y, p1, p2)
          if (v_mdy > max_mdy) max_mdy = v_mdy
        }
        # DMY: month=p2, day=p1
        if (valid(p1,p2)) {
          v_dmy = ymd_num(y, p2, p1)
          if (v_dmy > max_dmy) max_dmy = v_dmy
        }
      }
    }
    END{
      y=substr(TODAY,1,4)+0; m=substr(TODAY,6,2)+0; d=substr(TODAY,9,2)+0
      today_num = y*10000 + m*100 + d
      if (max_mdy==today_num && max_dmy!=today_num) print "MDY"
      else if (max_dmy==today_num && max_mdy!=today_num) print "DMY"
      else print "UNKNOWN"
    }
  " "$f"
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

# ---- Funkce: diagnostika (pro log) – validní maxima; hezký tisk ----
print_detect_diag () {
  local f="$1" today="$2"
  awk -F, -v TODAY="$today" "$awk_valid_fn
    function ymd(y,m,d){ return sprintf(\"%04d-%02d-%02d\", y,m,d) }
    function ymd_num(y,m,d){ return y*10000 + m*100 + d }
    BEGIN{
      d1gt=0; d2gt=0; max_mdy=0; max_dmy=0;
      have_mdy=0; have_dmy=0;
    }
    NR>2{
      d=$1; gsub(/^\xEF\xBB\xBF/,\"\",d)
      if (d ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/) {
        y=substr(d,7,4)+0
        p1=substr(d,1,2)+0
        p2=substr(d,4,2)+0

        if (p1>12) d1gt++
        if (p2>12) d2gt++

        # MDY valid
        if (valid(p2,p1)) {
          vm=ymd_num(y,p1,p2)
          if (vm>max_mdy) { max_mdy=vm; y_m=y; m_m=p1; d_m=p2; have_mdy=1 }
        }
        # DMY valid
        if (valid(p1,p2)) {
          vd=ymd_num(y,p2,p1)
          if (vd>max_dmy) { max_dmy=vd; y_d=y; m_d=p2; d_d=p1; have_dmy=1 }
        }

        u1[p1]=1; u2[p2]=1
      }
    }
    END{
      c1=0; for (k in u1) c1++
      c2=0; for (k in u2) c2++
      printf \"   Diagnostika:\\n\"
      printf \"     • Pojistka >12:  pos1>12=%d  pos2>12=%d\\n\", d1gt, d2gt
      if (have_mdy) printf \"     • Max (MDY): %s\\n\", ymd(y_m,m_m,d_m); else printf \"     • Max (MDY): n/a (nenalezen validní)\\n\"
      if (have_dmy) printf \"     • Max (DMY): %s\\n\", ymd(y_d,m_d,d_d); else printf \"     • Max (DMY): n/a (nenalezen validní)\\n\"
      printf \"     • Dnešek: %s\\n\", TODAY
      printf \"     • Unikáty: pos1=%d  pos2=%d\\n\", c1, c2
    }
  " "$f"
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

  # 1) max == TODAY (jen validní kombinace)
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
  echo "📄 [${idx}/${#files[@]}] Zpracovávám: $file"
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

  # převod (HH:MM[:SS]) + mapování null tokenů + explicitní výpis INPUT/OUTPUT řádků s nullem + fail-fast
  awk -v OFS="," \
      -v loc="$location" -v fmt="$fmt" -v SRC="$file" \
      -v SAMPLE="$NULL_TOKEN_SAMPLE_N" -v DUMP="$NULL_TOKEN_DUMP" -v ALLOW="$ALLOW_NULL_TOKENS" '
    function trim(s){ sub(/^ +/,"",s); sub(/ +$/,"",s); return s }
    function is_num(s){ return (s ~ /^-?[0-9]+([.][0-9]+)?$/) }
    function is_null_tok(s,  u){ s=trim(s); u=toupper(s); return (s=="" || s=="-" || u=="NA" || u=="N/A" || u=="NULL") }

    BEGIN { FS=","; null_hits=0; shown=0 }
    NR <= 2 { next }
    { gsub(/^\xEF\xBB\xBF/, "", $1) }

    NF && $1 ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ && $2 ~ /^[0-9]{1,2}:[0-9]{2}(:[0-9]{2})?$/ {
      split($1, d, "/")
      day   = (fmt == "DMY" ? d[1]+0 : d[2]+0)
      month = (fmt == "DMY" ? d[2]+0 : d[1]+0)
      year  = d[3]+0

      split($2, t, ":")
      hour   = sprintf("%02d", t[1])
      minute = sprintf("%02d", t[2])
      second = (t[3] ? sprintf("%02d", t[3]) : "00")

      raw_temp = $3
      raw_rh   = $4
      temp = trim(raw_temp)
      rh   = trim(raw_rh)

      had_null = 0
      if (is_null_tok(temp)) { temp=""; had_null=1 }
      if (is_null_tok(rh))   { rh  =""; had_null=1 }

      datetime = sprintf("%04d-%02d-%02d %s:%s:%s", year, month, day, hour, minute, second)

      if (had_null) {
        null_hits++
        if (DUMP==1 || shown < SAMPLE) {
          shown++
          # INPUT exact
          fprintf(stderr, "  == NULL TOKEN (file=%s line=%d)\n    input:  \"%s,%s,%s,%s\"\n", SRC, NR, $1,$2,raw_temp,raw_rh)
          # OUTPUT projection (po mapování na prázdno)
          fprintf(stderr, "    output: \"%s,%s,%s,%s\"\n", datetime, (temp==""?"":temp), (rh==""?"":rh), loc)
        }
      }

      # přísnost na jiné nečíselné řetězce
      if (temp!="" && !is_num(temp)) { fprintf(stderr, "  !! non_numeric temp | file=%s | raw=\"%s,%s,%s,%s\"\n", SRC, $1,$2,raw_temp,raw_rh); exit 6 }
      if (rh  !="" && !is_num(rh))   { fprintf(stderr, "  !! non_numeric  rh | file=%s | raw=\"%s,%s,%s,%s\"\n", SRC, $1,$2,raw_temp,raw_rh); exit 6 }

      print datetime, temp, rh, loc
    }

    END {
      if (null_hits > 0) {
        fprintf(stderr, "   — Souhrn null tokenů v souboru: %d řádků (viz výše).%s\n",
                        null_hits, (ALLOW?" Pokračuji (ALLOW_NULL_TOKENS=1).":""))
        if (!ALLOW) {
          fprintf(stderr, "❌ Nalezeny null tokeny (\"-\", \"NA\", \"N/A\", \"NULL\"). Selhávám (ALLOW_NULL_TOKENS=0).\n")
          exit 5
        }
      }
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
