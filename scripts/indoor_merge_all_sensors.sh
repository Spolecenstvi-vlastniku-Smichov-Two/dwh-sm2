#!/usr/bin/env bash

set -euo pipefail

output="./gdrive/all_sensors_merged.csv"
first=1
total_lines=0

rm -f "$output"

if ! ls ./latest/ThermoProSensor_export_*.csv 1> /dev/null 2>&1; then
  echo "Nenalezen žádný soubor - vytvářím prázdný výstup s hlavičkou"
  echo "Datetime,Temperature_Celsius,Relative_Humidity(%),Location" > "$output"
  exit 0
fi

is_valid_date() {
  local y="$1" m="$2" d="$3"
  # základní rozsahy
  if (( m < 1 || m > 12 || d < 1 || d > 31 )); then
    return 1
  fi
  # hrubá validace délky měsíců (únor 29 povolíme, leap-year neřešíme)
  case "$m" in
    4|6|9|11) (( d <= 30 )) || return 1 ;;
    2) (( d <= 29 )) || return 1 ;;
  esac
  return 0
}

# Zpracování všech souborů
for file in ./latest/ThermoProSensor_export_*.csv; do
  echo "📄 Zpracovávám: $file"
  location=$(basename "$file" | awk -F'_' '{print $3}')
  echo "   - Location: $location"

  if [ $first -eq 1 ]; then
    echo "Datetime,Temperature_Celsius,Relative_Humidity(%),Location" > "$output"
    first=0
  fi

  awk -v OFS="," -v loc="$location" '
    BEGIN { FS="," }
    NR <= 2 { next }                             # přeskočit popis a hlavičku
    {
      gsub(/^\xEF\xBB\xBF/, "", $1)              # odstranit BOM v prvním poli
    }

    # Očekáváme datum ve tvaru DD/MM/YYYY nebo MM/DD/YYYY v $1
    # a čas v $2 (HH:MM nebo HH:MM:SS). Filtrujeme ostatní řádky.
    $1 ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ && $2 ~ /^[0-9]{1,2}:[0-9]{2}(:[0-9]{2})?$/ {
      split($1, dmy, "/")
      dd = dmy[1] + 0
      mm = dmy[2] + 0
      yy = dmy[3] + 0

      # rozpad času
      split($2, t, ":")
      hh = sprintf("%02d", t[1])
      mi = sprintf("%02d", t[2])
      ss = (length(t) >= 3 ? sprintf("%02d", t[3]) : "00")

      # kandidáti
      # A) DMY: dd/mm/yyyy
      dA = dd; mA = mm
      # B) MDY: mm/dd/yyyy
      dB = mm; mB = dd

      validA = (mA>=1 && mA<=12 && dA>=1 && dA<=31)
      if (validA && (mA==4 || mA==6 || mA==9 || mA==11) && dA>30) validA=0
      if (validA && mA==2 && dA>29) validA=0

      validB = (mB>=1 && mB<=12 && dB>=1 && dB<=31)
      if (validB && (mB==4 || mB==6 || mB==9 || mB==11) && dB>30) validB=0
      if (validB && mB==2 && dB>29) validB=0

      chosen_day = -1
      chosen_month = -1

      if (validA && !validB) {
        chosen_day = dA; chosen_month = mA
      } else if (!validA && validB) {
        chosen_day = dB; chosen_month = mB
      } else if (validA && validB) {
        # remíza -> preferuj evropské DMY
        chosen_day = dA; chosen_month = mA
      } else {
        # nevalidní datum, přeskoč řádek
        next
      }

      datetime = sprintf("%04d-%02d-%02d %s:%s:%s", yy, chosen_month, chosen_day, hh, mi, ss)
      print datetime, $3, $4, loc
    }
  ' "$file" >> "$output"

  lines=$(awk 'NR > 2' "$file" | wc -l)
  echo "   - Zpracováno řádků (vstup): $lines"
  total_lines=$((total_lines + lines))
done

echo "✅ Hotovo!"
echo "Celkem prošlo vstupních řádků: $total_lines"
echo "Výstupní soubor: $output"
echo "🗂️ Náhled prvních 10 řádků:"
head -n 10 "$output"
