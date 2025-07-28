<template>
    <!-- Main Content -->
    <div :class="[theme, 'content']" :style="{ height: heightVar() }">

        <!-- Component 1: Folder Navigation -->
        <div class="folder-navigation">
            <DatabaseDropdown />
        </div>

        <!-- Component 2: Column Navigation -->
        <div class="column-navigation">
            <ColumnDropdown :selectedDbsTables="selectedDbsTables" />
        </div>
        <div class="right-panel">
            <!-- Component 3: Selection, Interval, Aggregation, and Export Config -->
            <div class="settings-panel">
                <Selection />
                <IntervalDropdown />
                <StatisticsDropdown />
                <ExportConfig />
                <span>
                    <ExportTableStats />
                    <button @click="fetchData">Fetch Data</button>
                    <button @click="exportData">Export Data</button>
                    <!-- Button to open the filter popup -->
                    <button @click="showFilterPopup = true">
                        Filter Columns
                    </button>
                </span>
                <!-- Filter Popup -->
                <div v-if="showFilterPopup" class="filter-popup-overlay" @click.self="showFilterPopup = false">
                    <div class="filter-popup">
                        <h3>Filter Columns</h3>
                        <div v-for="col in selectedColumns" :key="col" class="filter-row">
                            <label :for="'filter-' + col">{{ col }}:</label>
                            <Multiselect :id="'filter-' + col" v-model="columnFilters[col]"
                                :options="uniqueColumnValues[col] || []" :multiple="true" :close-on-select="false"
                                :clear-on-select="false" :preserve-search="true" placeholder="Select values"
                                label="value" track-by="value" class="filter-multiselect" />
                        </div>
                        <div class="popup-actions">
                            <button @click="applyFilters">Apply</button>
                            <button @click="showFilterPopup = false">Close</button>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Component 4: Main View (Table and Stats Display) -->
            <TableStatsDisplay :data="filteredData" :stats="stats" :statsColumns="statsColumns"
                :selectedColumns="selectedColumns" :rowLimit="rowLimit" />
        </div>
    </div>
</template>

<script>
import { mapState, mapActions } from "vuex";
import DatabaseDropdown from "../components/DatabaseDropdown.vue";
import ColumnDropdown from "../components/ColumnDropdown.vue";
import Selection from "../components/Selection.vue";
import IntervalDropdown from "../components/IntervalDropdown.vue";
import StatisticsDropdown from "../components/StatisticsDropdown.vue";
import ExportConfig from "../components/ExportConfig.vue";
import ExportTableStats from "../components/ExportTableStats.vue";
import TableStatsDisplay from "../components/TableStatsDisplay.vue";
import axios from 'axios';
import Multiselect from 'vue-multiselect';

export default {
    name: "Project",
    components: {
        DatabaseDropdown,
        ColumnDropdown,
        Selection,
        IntervalDropdown,
        StatisticsDropdown,
        ExportConfig,
        ExportTableStats,
        TableStatsDisplay,
        Multiselect,
    },
    data() {
        return {
            stats: [],
            statsColumns: [],
            data: [],
            rowLimit: 100,
            showFilterPopup: false,
            columnFilters: {},
            filteredData: [],
            uniqueColumnValues: {},
        };
    },
    computed: {
        ...mapState(["selectedDbsTables", "selectedColumns", "allSelectedColumns", "mathFormula", "selectedIds", "idColumn", "dateRange", "selectedInterval", "selectedStatistics", "selectedMethod", "exportColumns", "exportIds", "exportDate", "exportInterval", "dateType", "exportPath", "exportFilename", "exportFormat", "exportOptions", "theme"]),
    },
    methods: {
        ...mapActions(["updateSelectedColumns", "updateExportOptions", "updateAllSelectedColumns", "pushMessage", "clearMessages"]),
        heightVar() {
            // Set the height based on the environment
            const isTauri = !!window.__TAURI__;
            return isTauri ? "calc(100vh - 14vh)" : "calc(100vh - 16vh)";
        },
        // Fetch data from the API
        async fetchData() {
            try {
                // Choose all the columns if they are not selected
                if (this.selectedColumns.length === 0) {
                    this.updateSelectedColumns("All");
                    this.updateAllSelectedColumns(true);
                }

                this.pushMessage({ message: `Table Loading`, type: 'info' });

                // Fetch the data for the map
                const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/get_data`, {
                    params: {
                        db_tables: JSON.stringify(this.selectedDbsTables),
                        columns: JSON.stringify(this.allSelectedColumns ? "All" : this.selectedColumns.filter((column) => column !== 'Season')),
                        id: JSON.stringify(this.selectedIds),
                        id_column: this.idColumn,
                        start_date: this.dateRange.start,
                        end_date: this.dateRange.end,
                        date_type: this.dateType,
                        interval: this.selectedInterval,
                        statistics: JSON.stringify(this.selectedStatistics),
                        method: JSON.stringify(this.selectedMethod),
                        math_formula: this.mathFormula,
                        filter: JSON.stringify(this.columnFilters),
                    },
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("token")}`
                    }
                });
                // Check if the new feature is added to columns
                if (response.data.new_feature && !this.selectedColumns.includes(response.data.new_feature)) {
                    this.updateSelectedColumns(this.selectedColumns.concat([response.data.new_feature]));
                }
                if (this.selectedInterval === 'seasonally' && !this.selectedMethod.includes('Equal') && !this.selectedColumns.includes('Season')) {
                    this.updateSelectedColumns(this.selectedColumns.concat(['Season']));
                } else if (this.selectedColumns.includes('Season') && this.selectedInterval !== 'seasonally') {
                    this.updateSelectedColumns(this.selectedColumns.filter((column) => column !== 'Season'));
                }
                this.data = response.data.data;
                this.stats = response.data.stats;
                this.statsColumns = response.data.statsColumns;
                if (response.data.error) {
                    alert('Error fetching data: ' + response.data.error);
                    return;
                } else {
                    // Wait until the table has rendered, then trigger messages
                    this.$nextTick(() => {
                        this.pushMessage({ message: `Fetched ${this.selectedColumns.length} columns x ${this.data.length} rows`, type: 'success' });
                        this.pushMessage({ message: `Loaded ${this.rowLimit} rows`, type: 'success' });
                        if (this.statsColumns.length > 0) {
                            this.pushMessage({ message: `Fetched ${this.statsColumns.length - 1} statistics columns for ${(this.selectedMethod.length >= this.selectedStatistics.length ? this.selectedMethod : this.selectedStatistics).join(", ")}`, type: 'success' });
                        }
                    });
                }
            } catch (error) {
                console.error('Error fetching data: ', error.message);
            }
        },
        // Export data to a file
        async exportData() {
            try {
                const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/export_data`, {
                    params: {
                        db_tables: JSON.stringify(this.selectedDbsTables),
                        columns: JSON.stringify(this.allSelectedColumns ? "All" : this.exportColumns.filter((column) => column !== 'Season')),
                        id: JSON.stringify(this.exportIds),
                        id_column: this.idColumn,
                        start_date: this.exportDate.start,
                        end_date: this.exportDate.end,
                        interval: this.exportInterval,
                        statistics: JSON.stringify(this.selectedStatistics),
                        method: JSON.stringify(this.selectedMethod),
                        date_type: this.dateType,
                        export_path: this.exportPath,
                        export_filename: this.exportFilename,
                        export_format: this.exportFormat,
                        options: JSON.stringify(this.exportOptions),
                        math_formula: this.mathFormula,
                        filter: JSON.stringify(this.columnFilters),
                    },
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("token")}`
                    },
                    responseType: 'blob'
                });
                if (response.data.error) {
                    alert('Error fetching data: ' + response.data.error);
                    return;
                }
                else { this.pushMessage({ message: `Exported ${this.exportColumns.length} columns x ${this.data.length} rows`, type: 'success' }); }
                if (this.selectedInterval === 'seasonally' && !this.selectedMethod.includes('Equal') && !this.selectedColumns.includes('Season')) {
                    this.updateSelectedColumns(this.selectedColumns.concat(['Season']));
                } else if (this.selectedColumns.includes('Season') && this.selectedInterval !== 'seasonally') {
                    this.updateSelectedColumns(this.selectedColumns.filter((column) => column !== 'Season'));
                }

                if (!window.__TAURI__) {
                    // Download the file using the browser as a blob
                    const blob = new Blob([response.data], { type: response.headers['content-type'] });
                    const link = document.createElement('a');
                    const url = URL.createObjectURL(blob);
                    link.href = url;
                    link.setAttribute('download', this.exportFilename);
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    URL.revokeObjectURL(url);
                }
            } catch (error) {
                console.error('Error exporting data: ', error.message);
            }
        },
        computeUniqueColumnValues() {
            if (!this.data || !Array.isArray(this.data)) {
                this.uniqueColumnValues = {};
                return;
            }
            const values = {};
            this.selectedColumns.forEach(col => {
                const colValues = Array.from(new Set(this.data.map(row => row[col]).filter(v => v !== undefined && v !== null)));
                values[col] = colValues.map(v => ({ value: v }));
            });
            this.uniqueColumnValues = values;
        },
        applyFilters() {
            // Filter this.data using columnFilters and selectedColumns
            if (!this.data || !Array.isArray(this.data)) {
                this.filteredData = [];
                return;
            }
            this.filteredData = this.data.filter(row => {
                return this.selectedColumns.every(col => {
                    const selected = this.columnFilters[col];
                    if (!selected || selected.length === 0) return true;
                    return selected.some(sel => row[col] === sel.value);
                });
            });
            this.showFilterPopup = false;
        },
    },
};
</script>
<style src="../assets/pages.css"></style>