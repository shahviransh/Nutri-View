<template>
    <div :class="[theme, 'export-container']">
        <div class="export-field" v-if="!!window.__TAURI__">
            <label for="export-path" class="export-label">Export Path:</label>
            <input type="text" id="export-path" v-model="expPath" class="export-input" />
        </div>

        <div class="export-field">
            <label for="export-name" class="export-label">Export Filename:</label>
            <input type="text" id="export-name" v-model="expFilename" class="export-input"
                @change="onExportFileChange" />
        </div>

        <div class="export-field">
            <label for="export-format" class="export-label">Export Format:</label>
            <select id="export-format" v-model="expFormat" class="export-select">
                <template v-if="['Project', 'Table', 'Graph'].includes(pageTitle)">
                    <option value="csv">CSV</option>
                    <option value="txt">Text</option>
                </template>
                <!-- Conditional Graph Export Options -->
                <template v-if="pageTitle === 'Graph'">
                    <option value="xlsx">Graph In Excel</option>
                    <option value="png">Graph As PNG</option>
                    <option value="jpg">Graph As JPG</option>
                    <option value="jpeg">Graph As JPEG</option>
                    <option value="svg">Graph As SVG</option>
                    <option value="pdf">Graph As PDF</option>
                </template>
                <template v-if="pageTitle === 'Map'">
                    <option value="shp">Map As Shapefiles</option>
                    <option value="png">Map As PNG</option>
                    <option value="jpg">Map As JPG</option>
                    <option value="jpeg">Map As JPEG</option>
                    <option value="pdf">Map As PDF</option>
                </template>
            </select>
        </div>
        <div v-if="pageTitle === 'Graph'" class="export-field">
            <label for="graph-type" class="export-label">Graph Type:</label>
            <select id="graph-type" v-model="graType" class="export-select">
                <option value="bar">Bar</option>
                <option value="line">Line</option>
                <option value="scatter">Scatter</option>
                <option value="pie">Pie</option>
                <option value="bar-line">Line & Bar</option>
                <option value="line-scatter">Line & Scatter</option>
                <option value="bar-scatter">Bar & Scatter</option>
                <option value="bar-line-scatter">Line, Bar & Scatter</option>
            </select>
            <!-- Conditional Multiselects -->
            <div v-if="['bar-line', 'line-scatter', 'bar-scatter'].includes(graType)" class="export-field">
                <label for="multiselect1" class="export-label">{{ capitalizedFirstLetter(this.mapping[0]) }}
                    Columns:</label>
                <Multiselect id="multiselect1" v-model="selectedColumns1" :options="filteredOptions1" :multiple="true"
                    :close-on-select="false" placeholder="Select Columns" @update:modelValue="onSelectionChange"
                    :class="tagClass(selectedColumns1)" />

                <label for="multiselect2" class="export-label">{{ capitalizedFirstLetter(this.mapping[1]) }}
                    Columns:</label>
                <Multiselect id="multiselect2" v-model="selectedColumns2" :options="filteredOptions2" :multiple="true"
                    :close-on-select="false" placeholder="Select Columns" @update:modelValue="onSelectionChange"
                    :class="tagClass(selectedColumns2)" />
            </div>
            <div v-else-if="graType === 'bar-line-scatter'" class="export-field">
                <label for="multiselect3" class="export-label">{{ capitalizedFirstLetter(this.mapping[0]) }}
                    Columns:</label>
                <Multiselect id="multiselect3" v-model="selectedColumns1" :options="filteredOptions3" :multiple="true"
                    :close-on-select="false" placeholder="Select Columns" @update:modelValue="onSelectionChange"
                    :class="tagClass(selectedColumns1)" />
                <label for="multiselect4" class="export-label">{{ capitalizedFirstLetter(this.mapping[1]) }}
                    Columns:</label>
                <Multiselect id="multiselect4" v-model="selectedColumns2" :options="filteredOptions4" :multiple="true"
                    :close-on-select="false" placeholder="Select Columns" @update:modelValue="onSelectionChange"
                    :class="tagClass(selectedColumns2)" />
                <label for="multiselect5" class="export-label">{{ capitalizedFirstLetter(this.mapping[2]) }}
                    Columns:</label>
                <Multiselect id="multiselect5" v-model="selectedColumns3" :options="filteredOptions5" :multiple="true"
                    :close-on-select="false" placeholder="Select Columns" @update:modelValue="onSelectionChange"
                    :class="tagClass(selectedColumns3)" />
            </div>
        </div>
    </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'; // Import Vuex helpers
import Multiselect from 'vue-multiselect';
import DOMPurify from 'dompurify';

export default {
    data() {
        return {
            selectedColumns1: [],
            selectedColumns2: [],
            selectedColumns3: [],
            allOptions: this.selectedColumns,
            mapping: this.graType,
        };
    },
    components: {
        Multiselect,
    },
    computed: {
        expPath: {
            get() {
                return this.exportPath;
            },
            set(value) {
                this.updateExportPath(DOMPurify.sanitize(value));
            },
        },
        expFilename: {
            get() {
                return this.exportFilename;
            },
            set(value) {
                this.updateExportFilename(DOMPurify.sanitize(value));
            },
        },
        expFormat: {
            get() {
                return this.exportFormat;
            },
            set(value) {
                this.updateExportFormat(value);
            },
        },
        graType: {
            get() {
                return this.graphType;
            },
            set(value) {
                this.updateGraphType(value);
            },
        },
        filteredOptions1() {
            return this.allOptions.filter(option => !this.selectedColumns2.includes(option));
        },
        filteredOptions2() {
            return this.allOptions.filter(option => !this.selectedColumns1.includes(option));
        },
        filteredOptions3() {
            return this.allOptions.filter(option => !this.selectedColumns2.includes(option) && !this.selectedColumns3.includes(option));
        },
        filteredOptions4() {
            return this.allOptions.filter(option => !this.selectedColumns1.includes(option) && !this.selectedColumns3.includes(option));
        },
        filteredOptions5() {
            return this.allOptions.filter(option => !this.selectedColumns2.includes(option) && !this.selectedColumns1.includes(option));
        },
        ...mapState(['exportPath', 'exportFilename', 'exportFormat', "theme", "idColumn", "pageTitle", "graphType", "selectedColumns", "dateType"]),
    },
    methods: {
        ...mapActions(["updateExportPath", "updateExportFilename", "updateExportFormat", "updateGraphType", "updateMultiGraphType", "pushMessage"]),
        onSelectionChange() {
            let formats = [];
            const col1 = this.selectedColumns1.map(col => ({ name: col, type: this.mapping[0] }));
            const col2 = this.selectedColumns2.map(col => ({ name: col, type: this.mapping[1] }));
            if (this.graType === "bar-line-scatter") {
                const col3 = this.selectedColumns3.map(col => ({ name: col, type: this.mapping[2] }));
                formats = [...col1, ...col2, ...col3];
            } else {
                formats = [...col1, ...col2];
            }

            // Check if all selected columns are in formats
            const allColumnsInFormats = this.allOptions.every(col => formats.some(format => format.name === col));
            if (!allColumnsInFormats) {
                alert("All selected columns must be in the multi-graph formats");
            } else {
                this.pushMessage({ message: "All selected columns are in the multi-graph formats", type: "success" });
            }

            this.updateMultiGraphType(formats);
        },
        tagClass(selectedVar) {
            return selectedVar.length > 4 ? 'small-tags' : 'normal-tags';
        },
        capitalizedFirstLetter(string) {
            if (string) {
                return string.charAt(0).toUpperCase() + string.slice(1);
            }
            return "";
        },
    },
    watch: {
        graphType() {
            this.mapping = this.graphType.split('-');
        },
        selectedColumns() {
            this.allOptions = this.selectedColumns.filter(option => option !== this.dateType && !option.includes(this.idColumn));
        },
        pageTitle() {
            if (['Project', 'Table'].includes(this.pageTitle)) {
                this.updateExportFormat("csv");
            } else {
                this.updateExportFormat("png");
            }
        },
    },
};
</script>

<style scoped>
/* Theme variables */
.light {
    --text-color: #333;
    --bg-color: antiquewhite;
    --border-color: #ccc;
    --box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    --focus-border: #555;
}

.dark {
    --text-color: #f9f9f9;
    --bg-color: #444;
    --border-color: #666;
    --box-shadow: 0 2px 5px rgba(255, 255, 255, 0.1);
    --focus-border: #888;
}

.export-container {
    display: flex;
    flex-direction: column;
    gap: 5px;
    margin: 0px 0px;
    padding: 5px;
    border-radius: 4px;
    box-shadow: var(--box-shadow);
    background-color: var(--bg-color);
    overflow-y: auto;
}

label {
    font-weight: 600;
    font-size: 14px;
    color: var(--text-color);
    margin-bottom: 5px;
}

.export-label {
    font-weight: bold;
    font-size: 14px;
    color: var(--text-color);
    margin-bottom: 5px;
}

.export-input {
    padding: 5px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 14px;
    width: 100%;
    box-sizing: border-box;
    background-color: var(--bg-color);
    color: var(--text-color);
    transition: border-color 0.3s ease-in-out;
}

.export-input:focus {
    border-color: var(--focus-border);
    outline: none;
}

.export-select {
    padding: 5px;
    border: 1px solid var(--border-color);
    background-color: var(--bg-color);
    color: var(--text-color);
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    width: 100%;
}

.export-select:focus {
    border-color: var(--focus-border);
    outline: none;
}

.export-container select,
.export-container input {
    max-width: 300px;
    /* Limit width to make it look consistent */
}
</style>
