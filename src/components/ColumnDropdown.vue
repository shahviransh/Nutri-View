<template>
    <div :class="theme">
        <h5 class="parameter-heading">Parameters:</h5>
        <div v-if="['Project', 'Table', 'Map'].includes(pageTitle)">
            <div class="form-container">
                <div class="form-group">
                    <label for="column-select">Select Columns:</label>
                    <select id="column-select" class="dropdown" v-model="selectedColumns" multiple
                        :style="{ height: heightVar() }" @mousedown.prevent="toggleSelection($event)">
                        <option v-for="column in columns" :key="column" :value="column" :title="findTableName(column)"
                            @click.stop>
                            {{ column }}
                        </option>
                    </select>
                </div>
            </div>
            <div class="form-container">
                <div class="form-group">
                    <label for="export-column-select">Export Select Columns:</label>
                    <select id="export-column-select" class="dropdown" v-model="exportColumns" multiple
                        :style="{ height: heightVar() }" @mousedown.prevent="toggleSelection($event, true)">
                        <option v-for="column in columns" :key="column" :value="column" :title="findTableName(column)"
                            @click.stop>
                            {{ column }}
                        </option>
                    </select>
                </div>
            </div>
        </div>
        <!-- Conditional Axes Dropdowns -->
        <div v-if="pageTitle === 'Graph'">
            <div class="form-container">
                <div class="form-group">
                    <label for="x-axis-select">X-Axis:</label>
                    <select id="x-axis-select" class="dropdown" v-model="xaxis" :style="{ height: heightVar(true) }">
                        <option v-for="column in columns.filter(col => col === dateType)" :key="column" :value="column"
                            :title="findTableName(column)">
                            {{ column }}
                        </option>
                    </select>
                </div>
            </div>
            <div class="form-container">
                <div class="form-group">
                    <label for="y-axis-select">Y-Axis:</label>
                    <select id="y-axis-select" class="dropdown" v-model="yAxis" multiple
                        :style="{ height: heightVar(undefined, true) }"
                        @mousedown.prevent="toggleSelection($event)">
                        <option v-for="column in columns.filter(col => col !== dateType)" :key="column" :value="column"
                            :title="findTableName(column)" @click.stop>
                            {{ column }}
                        </option>
                    </select>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'; // Import Vuex helpers
import _ from 'lodash';

export default {
    props: {
        selectedDbsTables: {
            type: Array,
            default: null
        }
    },
    computed: {
        // Binding selected columns directly from Vuex
        xaxis: {
            get() {
                return this.xAxis;
            },
            set(value) {
                this.updateXAxis(value);
            }
        },
        ...mapState(['columns', 'ids', 'selectedColumns', 'theme', 'idColumn', 'selectedGeoFolders', 'dateType', 'tooltipColumns', 'exportColumns', 'pageTitle', 'xAxis', 'yAxis', 'dateType'])
    },
    data() {
        return {
        };
    },
    watch: {
        selectedDbsTables: {
            // Debounce is used to prevent multiple API calls in quick succession
            handler: _.debounce(function (newDbsTables) {
                if (newDbsTables.length > 0) {
                    this.fetchColumns(newDbsTables);
                }
            }, 1000), // Adjust debounce delay as needed
            deep: true
        },
    },
    methods: {
        ...mapActions(['fetchColumns', 'updateSelectedColumns', 'updateExportColumns', 'updateXAxis', 'updateYAxis']),
        findTableName(column) {
            for (const [key, columns] of Object.entries(this.tooltipColumns)) {
                const table_name = key.split(',')[1].replace(")", "").replace(/['"]/g, '').trim();
                if (column.includes(table_name)) {
                    return table_name;
                } else if (columns.includes(column)) {
                    const table_name = key.split(',')[1].replace(")", "").replace(/['"]/g, '');
                    if ([this.dateType, this.idColumn].includes(column)) {
                        return 'All Tables';
                    }
                    else {
                        return table_name;
                    }
                } else if (column.includes(table_name)) {
                    return table_name;
                }
            }
            return 'Unknown'; // Fallback if no table is found
        },
        heightVar(isXAxis, isYAxis) {
            const isTauri = !!window.__TAURI__;
            const screenHeight = window.innerHeight;

            if (screenHeight > 1080) {
                if (isXAxis) {
                    return '6vh';
                } else if (isYAxis) {
                    return isTauri ? '78vh' : '74vh';
                } else {
                    return isTauri ? '44vh' : '42vh';
                }
            } else if (isXAxis) {
                return '5vh';
            } else if (isYAxis) {
                return isTauri ? '66vh' : '62vh';
            } else {
                return isTauri ? '36vh' : '34vh';
            }
        },
        toggleSelection(event, exportColumns = false) {
            const option = event.target;
            if (option.tagName === 'OPTION') {
                const optionValue = option.value;
                let modelArray = exportColumns ? [...this.exportColumns] : [...this.selectedColumns];
                const index = modelArray.indexOf(optionValue);
                if (index > -1) {
                    modelArray.splice(index, 1); // Remove if already selected
                } else {
                    modelArray.push(optionValue); // Add if not selected
                }

                // Prevent default and stop propagation to avoid native behavior
                event.preventDefault();
                event.stopPropagation();
                // Vue nextTick to ensure the DOM updates with Vue reactivity
                this.$nextTick(() => {
                    this.$forceUpdate(); // Force update to reflect changes
                });

                // Update Vuex state based on the page title and exportColumns flag
                if (exportColumns) {
                    this.updateExportColumns(modelArray);
                } else if (['Project', 'Table', 'Map'].includes(this.pageTitle)) {
                    this.updateSelectedColumns(modelArray);
                } else if (this.pageTitle === 'Graph') {
                    this.updateYAxis(modelArray);
                }
            }
        }
    },
};
</script>
<style src="vue-multiselect/dist/vue-multiselect.css"></style>
<style scoped>
/* Theme variables */
.light {
    --text-color: #333;
    --bg-color: #f9f9f9;
    --border-color: #ccc;
    --dropdown-bg: #fff;
    --box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.dark {
    --text-color: #f9f9f9;
    --bg-color: #333;
    --border-color: #666;
    --dropdown-bg: #444;
    --box-shadow: 0 4px 10px rgba(255, 255, 255, 0.1);
}

.parameter-heading {
    font-size: 14px;
    font-weight: 600;
    margin: 0px 0px 0px 0px;
    color: var(--text-color);
}

div.form-container {
    display: flex;
    flex-direction: column;
    gap: 5px;
    max-width: 500px;
    margin: 0px auto;
    padding: 10px;
    background-color: var(--bg-color);
    border-radius: 8px;
    box-shadow: var(--box-shadow);
    height: 50%;
}

.form-group {
    display: flex;
    flex-direction: column;
    margin-bottom: 10px;
}

label {
    font-weight: 600;
    margin: 0px 0px 0px 0px;
    font-size: 14px;
    color: var(--text-color);
}

.dropdown {
    padding: 10px;
    border: 1px solid var(--border-color);
    border-radius: 5px;
    background-color: var(--dropdown-bg);
    font-size: 14px;
    width: 100%;
}

.dropdown[multiple] {
    padding: 5px;
    overflow: auto;
}
</style>