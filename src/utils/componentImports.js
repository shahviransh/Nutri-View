// src/utils/componentImports.js
import { defineAsyncComponent } from "vue";

export const DatabaseDropdown = defineAsyncComponent(() =>
  import(/* webpackPrefetch: true */ "../components/DatabaseDropdown.vue")
);
export const ColumnDropdown = defineAsyncComponent(() =>
  import(/* webpackPrefetch: true */ "../components/ColumnDropdown.vue")
);
export const Selection = defineAsyncComponent(() =>
  import(/* webpackPrefetch: true */ "../components/Selection.vue")
);
export const IntervalDropdown = defineAsyncComponent(() =>
  import(/* webpackPrefetch: true */ "../components/IntervalDropdown.vue")
);
export const StatisticsDropdown = defineAsyncComponent(() =>
  import(/* webpackPrefetch: true */ "../components/StatisticsDropdown.vue")
);
export const ExportConfig = defineAsyncComponent(() =>
  import(/* webpackPrefetch: true */ "../components/ExportConfig.vue")
);
export const ExportTableStats = defineAsyncComponent(() =>
  import(/* webpackPrefetch: true */ "../components/ExportTableStats.vue")
);
export const TableStatsDisplay = defineAsyncComponent(() =>
  import(/* webpackPrefetch: true */ "../components/TableStatsDisplay.vue")
);
export const GraphDisplay = defineAsyncComponent(() =>
  import(/* webpackPrefetch: true */ "../components/GraphDisplay.vue")
);
export const FolderTree = defineAsyncComponent(() =>
  import(/* webpackPrefetch: true */ "../components/FolderTree.vue")
);