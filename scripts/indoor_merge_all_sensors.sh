#!/usr/bin/env bash

output="./gdrive/all_sensors_merged.csv"
first=1
total_lines=0

rm -f "$output"

# Kontrola: jestli existují soubory k merge
if ! ls ./latest/ThermoProSensor_export_*.csv 1> /dev/null 2>&1; then
  echo "Nenalezen žádný soubor - vytvářím prázdný výstup s hlavičkou"
  echo "Datetime,Temperature_Celsius,Relative_Humidity(%),Location" > "$output"
  exit 0
fi

for file in ./latest/ThermoProSensor_export_*.csv; do
  echo "📄 Zpracovávám: $file"

  location=$(basename "$file" | awk -F'_' '{print $3}')
  echo "   - Location: $location"

  # Smazat popisnou hlavičku
  awk 'NR==1 && /^Timestamp/ {next} {print}' "$file" > tmp && mv tmp "$file"

  # Smazat BOM znaky
  sed -i 's/\xEF\xBB\xBF//g' "$file"

  # Opravit koncovou čárku v hlavičce
  sed -i '1s/,[[:space:]]*$//' "$file"

  if [ $first -eq 1 ]; then
    # První soubor: hlavička + data s robustní validací
    awk -F',' -v loc="$location" 'BEGIN{OFS=","}
    NR==1 {
      print "Datetime", $3, $4, "Location"
      next
    }
    NF && $1 ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ && $2 ~ /^[0-9]{1,2}:[0-9]{2}$/ {
      split($1, d, "/")
      datetime = d[3] "-" sprintf("%02d", d[1]) "-" sprintf("%02d", d[2])

      split($2, t, ":")
      hour = t[1]; minute = t[2]
      if (length(hour)==1) hour = "0" hour
      datetime = datetime " " hour ":" minute ":00"

      print datetime, $3, $4, loc
    }' "$file" > "$output"

    lines=$(awk 'NR>1 && NF' "$file" | wc -l)
    first=0
  else
    # Další soubory: bez hlavičky + validace
    awk 'NR==1 && /^Timestamp/ {next} NR==1 {next} {print}' "$file" > tmp && mv tmp "$file"

    awk -F',' -v loc="$location" 'BEGIN{OFS=","}
    NF && $1 ~ /^[0-9]{2}\/[0-9]{2}\/[0-9]{4}$/ && $2 ~ /^[0-9]{1,2}:[0-9]{2}$/ {
      split($1, d, "/")
      datetime = d[3] "-" sprintf("%02d", d[1]) "-" sprintf("%02d", d[2])

      split($2, t, ":")
      hour = t[1]; minute = t[2]
      if (length(hour)==1) hour = "0" hour
      datetime = datetime " " hour ":" minute ":00"

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
