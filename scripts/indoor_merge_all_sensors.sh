#!/usr/bin/env bash

output="./gdrive/all_sensors_merged.csv"
first=1
total_lines=0

rm -f "$output"

if ! ls ./latest/ThermoProSensor_export_*.csv 1> /dev/null 2>&1; then
  echo "Nenalezen žádný soubor - vytvářím prázdný výstup s hlavičkou"
  echo "Datetime,Temperature_Celsius,Relative_Humidity(%),Location" > "$output"
  exit 0
fi

# Funkce pro detekci formátu datumu
guess_date_format() {
  local file="$1"
  local d m
  local dmy=0
  local mdy=0
  local ambiguous=0
  local current_month=$(date +%m | sed 's/^0*//')

  awk 'NR > 2' "$file" | sed 's/^\xEF\xBB\xBF//' | \
  awk -F',' 'NR % 1000 == 1 && $1 ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ {print $1}' | \
  while read -r line; do
    d=$(echo "$line" | cut -d'/' -f1)
    m=$(echo "$line" | cut -d'/' -f2)

    if ((10#$d > 12)); then
      dmy=$((dmy + 1))
    elif ((10#$m > 12)); then
      mdy=$((mdy + 1))
    else
      ambiguous=$((ambiguous + 1))
    fi
  done

  if (( dmy > 0 && mdy == 0 )); then
    echo "DMY"
  elif (( mdy > 0 && dmy == 0 )); then
    echo "MDY"
  elif (( dmy > mdy )); then
    echo "DMY"
  elif (( mdy > dmy )); then
    echo "MDY"
  else
    # fallback – použít první dostupné datum a porovnat s aktuálním měsícem
    first_date=$(awk 'NR > 2' "$file" | sed 's/^\xEF\xBB\xBF//' | awk -F',' '$1 ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ {print $1; exit}')
    if [ -n "$first_date" ]; then
      f1=$(echo "$first_date" | cut -d'/' -f1)
      f2=$(echo "$first_date" | cut -d'/' -f2)
      if ((10#$f1 == current_month)); then
        echo "MDY"
      elif ((10#$f2 == current_month)); then
        echo "DMY"
      else
        echo "DMY"
      fi
    else
      echo "DMY"
    fi
  fi
}

# Zpracování všech souborů
for file in ./latest/ThermoProSensor_export_*.csv; do
  echo "📄 Zpracovávám: $file"

  location=$(basename "$file" | awk -F'_' '{print $3}')
  echo "   - Location: $location"

  date_format=$(guess_date_format "$file")
  echo "   - Formát datumu: $date_format"

  if [ $first -eq 1 ]; then
    echo "Datetime,Temperature_Celsius,Relative_Humidity(%),Location" > "$output"
    first=0
  fi

  awk -v OFS="," -v loc="$location" -v fmt="$date_format" '
    BEGIN { FS="," }
    NR <= 2 { next }  # přeskočit popis a hlavičku
    {
      gsub(/^\xEF\xBB\xBF/, "", $1)  # odstranit BOM, pokud zůstal
    }
    NF && $1 ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ && $2 ~ /^[0-9]{1,2}:[0-9]{2}$/ {
      split($1, d, "/")
      day = (fmt == "DMY" ? d[1] : d[2])
      month = (fmt == "DMY" ? d[2] : d[1])
      year = d[3]

      split($2, t, ":")
      hour = sprintf("%02d", t[1])
      minute = t[2]
      datetime = year "-" sprintf("%02d", month) "-" sprintf("%02d", day) " " hour ":" minute ":00"

      print datetime, $3, $4, loc
    }
  ' "$file" >> "$output"

  lines=$(awk 'NR > 2' "$file" | wc -l)
  echo "   - Přidáno řádků: $lines"
  total_lines=$((total_lines + lines))
done

echo "✅ Hotovo!"
echo "Celkem sloučeno řádků: $total_lines"
echo "Výstupní soubor: $output"
echo "🗂️ Náhled prvních 10 řádků:"
head -n 10 "$output"
