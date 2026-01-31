// Data Explorer Configuration
// Jednoduchý konfigurační objekt pro definici datasetu a chování aplikace

export const DATASET_CONFIG = {
  // Metadata o datasetu
  name: 'SM2 Teploty',
  version: '1.0.0',

  // Definice datového zdroje
  source: {
    type: 'parquet',
    url: './sm2_public_dataset.parquet',
    // Mapování sloupců z Parquetu
    columns: {
      time: 0,      // Date
      location: 1,  // string - 'sm2_01', '1NP-1', atd.
      floor: 2,     // string - 'Atrea', 'ThermoPro'
      metric: 4,    // string - 'temp_indoor', 'temp_ambient', atd.
      value: 5      // number - hodnota
    }
  },

  // Definice metrik - řídí filter UI a chování
  metrics: {
    temp_indoor: {
      label: 'vnitřní',
      order: 1,
      global: false
    },
    temp_ambient: {
      label: 'venkovní',
      order: 2,
      global: true,           // Ignoruje filtr sekcí
      aggregateLocation: true // Sloučí všechny lokace do jedné
    },
    temp_fresh: {
      label: 'čerstvý',
      order: 3,
      global: false
    },
    temp_intake: {
      label: 'sací',
      order: 4,
      global: false
    },
    temp_waste: {
      label: 'odpadní',
      order: 5,
      global: false
    }
  },

  // Definice sekcí - řídí checkboxy
  sections: [1, 2, 3, 4, 5, 6, 7, 8, 9],

  // Definice zdrojů dat - řídí checkboxy a logiku filtrů
  sources: {
    Atrea: {
      key: 'Atrea',
      label: 'Atrea',
      checkboxLabel: 'Zobrazit Atrea',
      default: true,
      // Detekce: řádek patří tomuto zdroji když floor === 'Atrea'
      floorValue: 'Atrea',
      // Parsování sekce z location (např. 'sm2_01' -> '1')
      locationPrefix: 'sm2',
      sectionParse: 'after_prefix',  // sekce je za prefixem (sm2_01 -> 1)
      // Řazení
      sortType: 'Atrea',
      sortPriority: 1  // Atrea první
    },
    ThermoPro: {
      key: 'ThermoPro',
      label: 'ThermoPro',
      default: false,
      // Detekce: řádek patří tomuto zdroji když floor === 'ThermoPro'
      floorValue: 'ThermoPro',
      // Parsování sekce z location (např. '1NP-1' -> '1')
      locationSeparator: '-',
      sectionParse: 'after_separator',  // sekce je za pomlčkou
      // Podlaží
      floors: true,
      floorCodeLength: 3,  // délka kódu podlaží (1NP, 2PP)
      floorCodePosition: 'prefix',  // kód je na začátku location
      // Řazení
      sortType: 'NP/PP',  // určí se z floorCode
      sortPriority: 2  // po Atrea
    }
  },

  // Definice filtrů - generuje UI filtrů
  filters: [
    {
      key: 'sections',
      label: 'Sekce',
      type: 'checkboxes',
      checkboxClass: 'section-cb',
      items: [1, 2, 3, 4, 5, 6, 7, 8, 9],  // Pole hodnot
      itemLabel: (value) => String(value),  // Jak získat label z hodnoty
      default: 'all'  // 'all' = všechno vybráno
    },
    {
      key: 'metrics',
      label: 'Metriky',
      type: 'checkboxes',
      checkboxClass: 'metric-cb',
      items: {  // Objekt s konfigurací
        temp_indoor: { label: 'vnitřní', global: false },
        temp_ambient: { label: 'venkovní', global: true },
        temp_fresh: { label: 'čerstvý', global: false },
        temp_intake: { label: 'sací', global: false },
        temp_waste: { label: 'odpadní', global: false }
      },
      itemLabel: (key, config) => config.label,
      default: (items) => Object.keys(items).filter(k => items[k].global)
    },
    {
      key: 'sources',
      label: 'Zdroje',
      type: 'hierarchical',  // Zanořené filtry (zdroj → podlaží)
      checkboxClass: 'source-cb',
      sourceConfig: 'sources',  // Odkaz na DATASET_CONFIG.sources
      default: { Atrea: true, ThermoPro: [] }  // Atrea zaškrtnuto, ThermoPro nic
    }
  ],

  // Definice granularity - řídí select
  granularity: [
    { value: 'month', label: 'měsíční' },
    { value: 'day', label: 'denní' },
    { value: 'hour', label: 'hodinová' }
  ],

  // Režimy zobrazení
  viewModes: [
    { value: 'max-avg-min', label: 'MAX-AVG-MIN', default: true },
    { value: 'avg', label: 'AVG' }
  ],

  // Vizualizace - barvy a styly
  chart: {
    library: 'Chart.js',
    type: 'line',
    colors: [
      '#4285f4', // blue
      '#34A853', // green
      '#FBBC05', // yellow
      '#EA4335', // red
      '#9C27B0', // purple
      '#FF9800', // orange
      '#00BCD4', // cyan
      '#8BC34A', // light green
      '#E91E63'  // pink
    ],
    height: '65vh',
    datasets: {
      'max-avg-min': {
        min: { borderWidth: 1, fill: false, pointRadius: 0 },
        max: { borderWidth: 1, fill: -1, pointRadius: 0 },
        avg: { borderWidth: 3, fill: false, pointRadius: 4 }
      },
      avg: {
        avg: { borderWidth: 2, fill: false, pointRadius: 2 }
      }
    }
  },

  // Chování aplikace
  behavior: {
    // Jak se má zachovat perioda při změně filtrů
    periodSelection: {
      onAddFilter: 'keep',           // Při přidání - ponechat
      onRemoveFilter: 'findPast',    // Při odebrání - hledat v minulosti
      onGranularityChange: 'last'    // Při změně granularity - poslední
    },
    // Formát záhlaví
    headerFormat: '{sections} • {metrics} • {granularity} • Perioda {period} • Zdroj {sources}'
  },

  // Lokalizace
  i18n: {
    month: 'měsíční',
    day: 'denní',
    hour: 'hodinová',
    noData: 'Žádná data',
    noDataInHistory: 'Pro aktuální filtr neexistují žádná data v dostupné historii.',
    dataLoaded: 'Data načtena! {count} řádků.',
    oldestPeriodReached: 'Aktuálně vybraná perioda je nejstarší dostupná pro daný výběr dat.',
    newestPeriodReached: 'Aktuálně vybraná perioda je nejnovější dostupná pro daný výběr dat.',
    errorLoading: 'Chyba při načítání dat: {error}',
    errorNoData: 'Pro zadané filtry nebyla nalezena žádná data.'
  }
};

// Helper funkce pro práci s konfigurací
export const ConfigHelpers = {
  // Získání seřazených metrik
  getMetricsInOrder() {
    return Object.entries(DATASET_CONFIG.metrics)
      .sort(([, a], [, b]) => a.order - b.order)
      .map(([key, cfg]) => ({ key, ...cfg }));
  },

  // Získání výchozích metrik
  getDefaultMetrics() {
    return Object.entries(DATASET_CONFIG.metrics)
      .filter(([, cfg]) => cfg.global)
      .map(([key]) => key);
  },

  // Je metrika globální?
  isGlobalMetric(metric) {
    return DATASET_CONFIG.metrics[metric]?.global || false;
  },

  // Má se agregovat location pro tuto metriku?
  shouldAggregateLocation(metric) {
    return DATASET_CONFIG.metrics[metric]?.aggregateLocation || false;
  },

  // Získání labelu metriky
  getMetricLabel(metric) {
    return DATASET_CONFIG.metrics[metric]?.label || metric;
  },

  // Získání názvu granularity v češtině
  getGranularityLabel(value) {
    const item = DATASET_CONFIG.granularity.find(g => g.value === value);
    return item?.label || value;
  },

  // Lokalizační zpráva
  t(key, params = {}) {
    let message = DATASET_CONFIG.i18n[key] || key;
    Object.entries(params).forEach(([k, v]) => {
      message = message.replace(`{${k}}`, v);
    });
    return message;
  },

  // Získání hodnoty z řádku podle názvu sloupce
  getColumn(row, columnName) {
    const index = DATASET_CONFIG.source.columns[columnName];
    return row[index];
  },

  // Získání zdroje podle floor hodnoty
  getSourceByFloor(floorValue) {
    return Object.values(DATASET_CONFIG.sources).find(s => s.floorValue === floorValue);
  },

  // Je řádek z daného zdroje?
  isSourceFloor(floorValue, sourceKey) {
    const source = DATASET_CONFIG.sources[sourceKey];
    return source && floorValue === source.floorValue;
  },

  // Parsování sekce z location podle zdroje
  parseSection(location, source) {
    if (!source) return null;

    if (source.sectionParse === 'after_prefix' && source.locationPrefix) {
      // sm2_01 -> 1
      const prefix = source.locationPrefix;
      if (location.startsWith(prefix)) {
        const numPart = location.substring(prefix.length);
        return String(parseInt(numPart, 10));
      }
    } else if (source.sectionParse === 'after_separator' && source.locationSeparator) {
      // 1NP-1 -> 1
      const parts = location.split(source.locationSeparator);
      if (parts.length > 1) {
        return parts[1];
      }
    }

    // Fallback - poslední znak
    return String(parseInt(location.slice(-1)));
  },

  // Získání floorCode z location pro ThermoPro
  getFloorCode(location, source) {
    if (!source || !source.floorCodeLength) return null;
    return location.substring(0, source.floorCodeLength);
  },

  // Získání sortType z location
  getSortType(location, source) {
    if (!source) return location;

    if (source.sortType === 'Atrea') {
      return 'Atrea';
    } else if (source.sortType === 'NP/PP') {
      const floorCode = this.getFloorCode(location, source);
      return (floorCode && floorCode.includes('NP')) ? 'NP' : 'PP';
    }

    return source.sortType || location;
  },

  // Získání filtrů
  getFilters() {
    return DATASET_CONFIG.filters || [];
  },

  // Získání filtru podle klíče
  getFilter(key) {
    return this.getFilters().find(f => f.key === key);
  }
};

// Exportovat jako default pro snadnější import
export default DATASET_CONFIG;
