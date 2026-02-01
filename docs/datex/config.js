// Data Explorer Configuration
// Jednoduchý konfigurační objekt pro definici datasetu a chování aplikace

export const DATASET_CONFIG = {
  // Metadata o datasetu
  name: 'SM2 Teploty',
  version: '1.0.0',
  locale: 'cs-CZ',  // Pro formátování data

  // Definice datového zdroje
  source: {
    type: 'parquet',
    url: '/dwh-sm2/datex/sm2_public_dataset.parquet',
    // Mapování sloupců z Parquetu
    columns: {
      time: 0,      // Date
      location: 1,  // string - 'sm2_01', '1NP-1', atd.
      floor: 2,     // string - 'Atrea', 'ThermoPro'
      type: 3,      // string - 'additive', 'nonadditive' (nový sloupec!)
      metric: 4,    // string - 'temp_indoor', 'temp_ambient', atd.
      value: 5      // number - hodnota
    }
  },

  // UI Konfigurace
  ui: {
    header: {
      title: '🏠 SM2 Průzkumník Teplot',
      subtitle: 'Apache Arrow.js + Chart.js • Parquet přímo v browseru'
    },
    // První panel - časové ovládání
    timeControls: [
      {
        id: 'language',
        label: 'Language',
        type: 'select',
        options: [
          { value: 'cz', label: 'Čeština' },
          { value: 'en', label: 'English' }
        ]
      },
      {
        id: 'view-mode',
        label: 'Zobrazení',
        type: 'select',
        configKey: 'viewModes'
      },
      {
        id: 'grain',
        label: 'Granularita',
        type: 'select',
        configKey: 'granularity'
      },
      {
        id: 'period',
        label: 'Perioda',
        type: 'select',
        dynamic: true  // Naplňuje se dynamicky podle dat
      }
    ],
    // Navigační tlačítka (v panelu filtrů)
    navButtons: [
      {
        id: 'btn-prev',
        label: '◀ Zpět',
        class: 'indigo',
        action: 'priorPeriod'
      },
      {
        id: 'btn-next',
        label: 'Vpřed ▶',
        class: 'green',
        action: 'nextPeriod'
      }
    ],
    // Akční tlačítka (v headeru)
    actionButtons: [
      {
        id: 'btn-copy-url',
        label: '🔗 URL',
        class: 'blue',
        action: 'copyShareURL'
      },
      {
        id: 'btn-save-favorite',
        label: '⭐ Uložit',
        class: 'yellow',
        action: 'saveFavorite'
      },
      {
        id: 'btn-clear',
        label: '🔄 Vyčistit',
        class: 'red',
        action: 'clearFilters'
      }
    ],
    // Dropdown pro oblíbené filtry
    favoritesDropdown: {
      id: 'favorites-select',
      label: 'Oblíbené',
      emptyLabel: '-- Vyber oblíbené --',
      showDelete: true
    }
  },

  // Definice stavových proměnných pro filtry
  filterState: {
    // Hierarchické filtry (zdroje s podlažími/podkategoriemi)
    hierarchical: {
      // Klíč = zdroj, hodnota = stav
      // 'simple' = boolean, 'hierarchical' = array
      sources: {
        Atrea: { type: 'simple', default: true },
        ThermoPro: { type: 'hierarchical', default: [] }
      }
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
      locationSeparator: '_',
      sectionParse: 'after_separator',  // sekce je za oddělovačem (sm2_01 -> 1)
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

  // ===== LOCATION HIERARCHIE =====
  // Definuje hierarchii location filtrů - může být globální i specifická pro zdroje
  locationHierarchy: {
    // Globální úrovně - společné pro všechny zdroje
    global: [
      {
        key: 'section',
        label: 'Sekce',
        type: 'checkboxes',
        checkboxClass: 'section-cb',
        // Jak parsovat hodnotu z location stringu
        parseFrom: {
          method: 'suffix',     // poslední znak location
          length: 1
        },
        items: [1, 2, 3, 4, 5, 6, 7, 8, 9],
        itemLabel: (value) => String(value),
        default: []
      }
    ],
    // Specifické úrovně pro jednotlivé zdroje
    sources: {
      ThermoPro: [
        {
          key: 'floor',
          label: 'Podlaží',
          type: 'checkboxes',
          checkboxClass: 'floor-cb',
          // Jak parsovat hodnotu z location stringu
          parseFrom: {
            method: 'prefix',    // první 3 znaky location
            length: 3
          },
          items: 'dynamic',  // Zjistí se dynamicky z dat
          itemLabel: (value) => String(value),
          default: [],
          // Filtr pro validaci hodnot (pouze NP/PP)
          itemFilter: (value) => value.includes('NP') || value.includes('PP'),
          // Vlastní řazení: NP před PP, v rámci NP sestupně, v rámci PP vzestupně
          customSort: (a, b) => {
            const getPrefix = (s) => parseInt(s.slice(0, -2)) || 0;
            const getSuffix = (s) => s.slice(-2);

            const suffixA = getSuffix(a);
            const suffixB = getSuffix(b);

            // NP před PP
            if (suffixA !== suffixB) {
              return suffixA === 'NP' ? -1 : 1;
            }

            // Stejný suffix - řadit podle čísla
            // Pro NP sestupně, pro PP vzestupně
            if (suffixA === 'NP') {
              return getPrefix(b) - getPrefix(a);
            } else {
              return getPrefix(a) - getPrefix(b);
            }
          }
        }
      ]
    }
  },

  // ===== METRIKY =====
  // Definice metrik - oddělené od location hierarchie
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

  // Filtry - generuje UI (metadata, metrics, sources)
  filters: [
    {
      key: 'metrics',
      label: 'Metriky',
      type: 'checkboxes',
      checkboxClass: 'metric-cb',
      configKey: 'metrics',  // Odkaz na DATASET_CONFIG.metrics
      itemLabel: (key, config) => config.label,
      default: (items) => Object.keys(items).filter(k => items[k].global)
    },
    {
      key: 'sources',
      label: 'Zdroje',
      type: 'hierarchical',
      checkboxClass: 'source-cb',
      sourceConfig: 'sources',
      default: { Atrea: true, ThermoPro: [] }
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
    errorNoData: 'Pro zadané filtry nebyla nalezena žádná data.',
    // URL a oblíbené
    copiedToClipboard: '✓ Zkopírováno!',
    favoriteSaved: '✓ Uloženo!',
    favoriteNamePrompt: 'Název oblíbeného filtru:',
    deleteFavoriteConfirm: 'Smazat tento oblíbený filtr?',
    deleteFavoriteNamedConfirm: 'Smazat oblíbený filtr "{name}"?',
    favoriteDeleteIcon: '🗑️',
    favoriteDeleteTitle: 'Smazat vybraný oblíbený filtr',
    selectFavoritePlaceholder: '-- Vyber oblíbené --',
    // UI texty
    section: 'Sekce',
    period: 'Perioda',
    source: 'Zdroj',
    all: 'Všechny',
    none: 'Žádná',
    temperature: 'Teplota (°C)',
    time: 'čas'
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

  // ===== LOCATION HIERARCHIE HELPERS =====

  // Získat všechny location levely (globální + pro daný zdroj)
  getLocationLevels(sourceKey = null) {
    const levels = [];

    // Globální úrovně
    if (DATASET_CONFIG.locationHierarchy?.global) {
      levels.push(...DATASET_CONFIG.locationHierarchy.global);
    }

    // Specifické úrovně pro zdroj
    if (sourceKey && DATASET_CONFIG.locationHierarchy?.sources?.[sourceKey]) {
      levels.push(...DATASET_CONFIG.locationHierarchy.sources[sourceKey]);
    }

    return levels;
  },

  // Parsovat hodnotu location levelu z location stringu
  parseLocationLevel(location, levelConfig, source) {
    if (!levelConfig.parseFrom) return null;

    const { method, length, separator } = levelConfig.parseFrom;

    switch (method) {
      case 'suffix':
        // Posledních N znaků
        return location.slice(-length);
      case 'prefix':
        // Prvních N znaků
        return location.substring(0, length);
      case 'after_separator':
        // Za separátorem
        if (separator) {
          const parts = location.split(separator);
          if (parts.length > 1) return parts[1];
        }
        return null;
      case 'after_prefix':
        // Za prefixem (např. 'sm2_01' -> '01')
        if (source?.locationPrefix) {
          const prefix = source.locationPrefix;
          if (location.startsWith(prefix)) {
            return location.substring(prefix.length);
          }
        }
        return null;
      default:
        return null;
    }
  },

  // Získat location levely pro daný řádek (source + location)
  getRowLocationLevels(row, sourceKey) {
    const location = this.getColumn(row, 'location');
    const levels = this.getLocationLevels(sourceKey);
    const result = {};

    levels.forEach(level => {
      const value = this.parseLocationLevel(location, level, DATASET_CONFIG.sources[sourceKey]);
      if (value !== null) {
        result[level.key] = value;
      }
    });

    return result;
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
