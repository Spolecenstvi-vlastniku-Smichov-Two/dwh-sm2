#!/usr/bin/env bash

output="./gdrive/all_sensors_merged.csv"
first=1
total_lines=0

# Vyčisti předchozí výsledek
rm -f "$output"

# Pokud neexistují žádné soubory
if ! ls ./latest/ThermoProSensor_export_*.csv 1> /dev/null 2>&1; then
  echo "Nenalezen žádný soubor - vytvářím prázdný výstup s hlavičkou"
  echo "Datetime,Temperature_Celsius,Relative_Humidity(%),Location" > "$output"
  exit 0
fi

# Funkce pro určení formátu data
guess_date_format() {
  local file="$1"
  local d m
  local dmy=0
  local mdy=0
  local unknown=0

  local current_month=$(date +%m | sed 's/^0*//')  # např. 07 → 7

  awk -F',' 'NR % 1000 == 1 && NR > 1 && $1 ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ {print $1}' "$file" | while read -r line; do
    d=$(echo "$line" | cut -d'/' -f1)
    m=$(echo "$line" | cut -d'/' -f2)

    if ((10#$d > 12)); then
      dmy=$((dmy + 1))
    elif ((10#$m > 12)); then
      mdy=$((mdy + 1))
    else
      # nejednoznačný případ → porovnání s aktuálním měsícem
      if ((10#$d == current_month)); then
        mdy=$((mdy + 1))
      elif ((10#$m == current_month)); then
        dmy=$((dmy + 1))
      else
        unknown=$((unknown + 1))
      fi
    fi
  done

  if (( dmy > mdy )); then
    echo "DMY"
  else
    echo "MDY"
  fi
}

# Pro každý soubor
for file in ./latest/ThermoProSensor_export_*.csv; do
  echo "📄 Zpracovávám: $file"

  location=$(basename "$file" | awk -F'_' '{print $3}')
  echo "   - Location: $location"

  # Odstranit popisnou hlavičku pokud začíná 'Timestamp'
  awk 'NR==1 && /^Timestamp/ {next} {print}' "$file" > tmp && mv tmp "$file"

  # Odstranit BOM znaky
  sed -i 's/\xEF\xBB\xBF//g' "$file"

  # Odstranit koncovou čárku v hlavičce
  sed -i '1s/,[[:space:]]*$//' "$file"

  # Detekce formátu data
  date_format=$(guess_date_format "$file")
  echo "   - Formát datumu: $date_format"

  if [ $first -eq 1 ]; then
    # První soubor: přidej hlavičku
    awk -F',' -v loc="$location" -v fmt="$date_format" 'BEGIN{OFS=","}
    NR==1 {
      print "Datetime,Temperature_Celsius,Relative_Humidity(%),Location"
      next
    }
    NF && $1 ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ && $2 ~ /^[0-9]{1,2}:[0-9]{2}$/ {
      split($1, d, "/")
      day = (fmt == "DMY" ? d[1] : d[2])
      month = (fmt == "DMY" ? d[2] : d[1])
      year = d[3]

      split($2, t, ":")
      hour = t[1]; minute = t[2]
      if (length(hour)==1) hour = "0" hour
      datetime = year "-" sprintf("%02d", month) "-" sprintf("%02d", day) " " hour ":" minute ":00"

      print datetime, $3, $4, loc
    }' "$file" > "$output"

    lines=$(awk 'NR>1 && NF' "$file" | wc -l)
    first=0
  else
    # Další soubory: bez hlavičky
    awk 'NR==1 && /^Timestamp/ {next} NR==1 {next} {print}' "$file" > tmp && mv tmp "$file"

    awk -F',' -v loc="$location" -v fmt="$date_format" 'BEGIN{OFS=","}
    NF && $1 ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ && $2 ~ /^[0-9]{1,2}:[0-9]{2}$/ {
      split($1, d, "/")
      day = (fmt == "DMY" ? d[1] : d[2])
      month = (fmt == "DMY" ? d[2] : d[1])
      year = d[3]

      split($2, t, ":")
      hour = t[1]; minute = t[2]
      if (length(hour)==1) hour = "0" hour
      datetime = year "-" sprintf("%02d", month) "-" sprintf("%02d", day) " " hour ":" minute ":00"

      print datetime, $3, $4, loc
    }' "$file" >> "$output"

    lines=$(awk 'NR>1 && NF' "$file" | wc -l)
  fi

  echo "   - Přidáno řádků: $lines"
  total_lines=$((total_lines + lines))
done

echo "✅ Hotovo!"
echo "Celkem sloučeno řádků: $total_lines"
echo "Výstupní soubor: $output"

echo "🗂️ Náhled prvních 10 řádků:"
head -n 10 "$output"
