# SM2 Data Warehouse - Uživatelská Příručka

**Cílová skupina**: Správci budovy, data analytici, vývojáři aplikací  
**Účel**: Přístup k datům ze senzorů SM2 budovy  
**Aktualizace**: Denně v 02:00 UTC

---

## 📊 Dostupná Data

### Ventilační Systém (Atrea)
- **Zdroj**: Atrea vzduchotechnická jednotka
- **Frekvence**: Každou hodinu
- **Metriky**: Venkovní teplota, vlhkost, rychlost větru, tlak
- **Lokace**: Venkovní senzory (střecha budovy)

### Vnitřní Klima (ThermoPro)
- **Zdroj**: ThermoPro senzory v bytech
- **Frekvence**: Každých 6 hodin
- **Metriky**: Teplota, vlhkost
- **Lokace**: Různé místnosti v budově

---

## 🔗 Přístup k Datům

### 1. Veřejný Dataset (Doporučeno)

**URL**: `sm2drive:Public/sm2_public_dataset.csv.gz`

**Formáty**:
- `sm2_public_dataset.csv.gz` - Komprimovaný CSV (nejmenší)
- `sm2_public_dataset.parquet` - Parquet formát (nejrychlejší)

**Schéma**:
```csv
time,location,source,measurement,data_key,data_value
2024-01-01T00:00:00Z,outdoor,Atrea,nonadditive,temperature,15.2
2024-01-01T00:00:00Z,1PP-S1,ThermoPro,nonadditive,temperature,21.5
```

**Stažení**:
```bash
# Pomocí rclone
rclone copy sm2drive:Public/sm2_public_dataset.csv.gz ./data/

# Pomocí curl (pokud je veřejně dostupný)
curl -o sm2_data.csv.gz https://example.com/sm2_public_dataset.csv.gz
```

### 2. Raw Data (Pro Pokročilé)

**Ventilace**: `sm2drive:Vzduchotechnika/Model/fact.csv`  
**Indoor**: `sm2drive:Indoor/Model/fact_indoor_*.csv`

### 3. Agregovaná Data (Pro Analýzy)

**Hodinové agregace**: `sm2drive:Normalized/*_YYYY-MM.hourly.csv`

---

## 💻 Použití v Kódu

### Python (pandas)

```python
import pandas as pd

# Načtení dat
df = pd.read_csv('sm2_public_dataset.csv.gz')

# Filtrování podle lokace
outdoor_data = df[df['location'] == 'outdoor']

# Filtrování podle metriky
temperature_data = df[df['data_key'] == 'temperature']

# Časové řady
df['time'] = pd.to_datetime(df['time'])
df.set_index('time', inplace=True)

# Denní průměry
daily_avg = df.groupby(['location', 'data_key']).resample('D')['data_value'].mean()
```

### R

```r
library(readr)
library(dplyr)
library(lubridate)

# Načtení dat
df <- read_csv("sm2_public_dataset.csv.gz")

# Filtrování a agregace
temperature_summary <- df %>%
  filter(data_key == "temperature") %>%
  mutate(time = as_datetime(time)) %>%
  group_by(location, date = as_date(time)) %>%
  summarise(avg_temp = mean(data_value, na.rm = TRUE))
```

### SQL (DuckDB)

```sql
-- Načtení dat
CREATE TABLE sm2_data AS 
SELECT * FROM read_csv_auto('sm2_public_dataset.csv.gz');

-- Denní průměry teploty
SELECT 
    location,
    DATE_TRUNC('day', time::TIMESTAMP) as date,
    AVG(data_value) as avg_temperature
FROM sm2_data 
WHERE data_key = 'temperature'
GROUP BY location, date
ORDER BY date DESC;
```

---

## 📈 Časté Analýzy

### 1. Porovnání Venkovní vs Vnitřní Teploty

```python
import matplotlib.pyplot as plt

# Filtrování dat
outdoor_temp = df[(df['location'] == 'outdoor') & (df['data_key'] == 'temperature')]
indoor_temp = df[(df['location'] != 'outdoor') & (df['data_key'] == 'temperature')]

# Denní průměry
outdoor_daily = outdoor_temp.resample('D')['data_value'].mean()
indoor_daily = indoor_temp.groupby(indoor_temp.index.date)['data_value'].mean()

# Graf
plt.figure(figsize=(12, 6))
plt.plot(outdoor_daily.index, outdoor_daily.values, label='Venkovní')
plt.plot(indoor_daily.index, indoor_daily.values, label='Vnitřní (průměr)')
plt.legend()
plt.title('Porovnání Teplot')
plt.show()
```

### 2. Analýza Vlhkosti po Místnostech

```python
# Vlhkost podle místností
humidity_by_room = df[
    (df['data_key'] == 'humidity') & 
    (df['location'] != 'outdoor')
].groupby('location')['data_value'].agg(['mean', 'std', 'min', 'max'])

print(humidity_by_room)
```

### 3. Korelace Venkovní Teploty a Spotřeby Energie

```python
# Spojení dat
outdoor_temp = df[(df['location'] == 'outdoor') & (df['data_key'] == 'temperature')]
energy_data = df[df['data_key'] == 'energy_consumption']

# Korelační analýza
correlation = outdoor_temp['data_value'].corr(energy_data['data_value'])
print(f"Korelace teplota vs energie: {correlation:.3f}")
```

---

## 🔧 Troubleshooting

### Problém: Data nejsou aktuální
**Řešení**:
1. Zkontrolujte GitHub Actions: [dwh-sm2/actions](https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2/actions)
2. Posledním úspěšný run by měl být < 24 hodin
3. Pokud ne, kontaktujte správce

### Problém: Chybějící data pro určitou lokaci
**Řešení**:
1. Zkontrolujte `location_map.csv` pro mapování názvů
2. Některé senzory mohou být dočasně offline
3. Zkontrolujte raw data v `sm2drive:Vzduchotechnika/Latest/`

### Problém: Neočekávané hodnoty
**Řešení**:
1. Zkontrolujte jednotky (°C, %, atd.)
2. Additive data = hodinové sumy
3. Non-additive data = hodinové průměry

---

## 📋 Schéma Dat

### Sloupce

| Sloupec | Typ | Popis | Příklad |
|---------|-----|-------|---------|
| `time` | datetime | UTC timestamp (hodinové) | `2024-01-01T12:00:00Z` |
| `location` | string | Normalizovaná lokace | `outdoor`, `1PP-S1`, `5NP-S9` |
| `source` | string | Zdroj měření | `Atrea`, `ThermoPro` |
| `measurement` | string | Typ agregace | `additive`, `nonadditive` |
| `data_key` | string | Název metriky | `temperature`, `humidity` |
| `data_value` | number | Hodnota (sum/mean) | `21.5`, `65.2` |

### Measurement Types

- **`additive`**: Hodinové sumy (energie, spotřeba)
- **`nonadditive`**: Hodinové průměry (teplota, vlhkost)

### Lokace

| Kód | Popis |
|-----|-------|
| `outdoor` | Venkovní senzory |
| `1PP-S1` | 1. podzemní podlaží, senzor 1 |
| `5NP-S9` | 5. nadzemní podlaží, senzor 9 |

*Kompletní mapování v `seeds/location_map.csv`*

---

## 🔐 Licence a Citace

### Licence
- **Zdrojový kód**: MIT License
- **Dataset**: CC BY 4.0

### Citace
Při použití dat prosím citujte:
```
SM2 Building Sensor Dataset. 
Společenství vlastníků Smíchov Two. 
https://github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2
```

---

## 📞 Podpora

### Pro Uživatele Dat
- **GitHub Issues**: Bug reports, feature requests
- **Email**: [kontakt přes GitHub]
- **Blog**: [horkovsm2.blogspot.com](https://horkovsm2.blogspot.com/)

### Pro Vývojáře
- **DEVELOPER_SETUP_GUIDE.md**: Kompletní setup
- **PHASE_1_IMPLEMENTATION.md**: Technické detaily
- **Makefile**: `make help` pro dostupné příkazy

---

**Poslední aktualizace**: 2026-01-04  
**Verze datasetu**: Denní build  
**Status**: ✅ Produkční
