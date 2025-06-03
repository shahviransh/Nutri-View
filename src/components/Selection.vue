<template>
    <div :class="[theme, 'select-container']">
        <div class="form-container-ref">
            <div v-if="['Time'].includes(daType)">
                <div class="form-group">
                    <label for="date-start">Model Start Date:</label>
                    <input id="date-start" type="date" v-model="defaultStartDate" class="input-field" readonly />
                </div>
                <div class="form-group">
                    <label for="date-end">Model End Date:</label>
                    <input id="date-end" type="date" v-model="defaultEndDate" class="input-field" readonly />
                </div>
            </div>
            <div v-else-if="daType === 'Month'">
                <div class="form-group">
                    <label for="date-start">Model Start Month:</label>
                    <input id="date-start" type="text" v-model="defaultStartDate" class="input-field" readonly />
                </div>
                <div class="form-group">
                    <label for="date-end">Model End Month:</label>
                    <input id="date-end" type="text" v-model="defaultEndDate" class="input-field" readonly />
                </div>
            </div>
            <div class="form-group">
                <label for="interval">Model Interval:</label>
                <input id="interval" type="text" v-model="capitalizedInterval" class="input-field" readonly />
            </div>
        </div>
        <div class="form-container">
            <div class="form-group">
                <label for="id-select">Select IDs:</label>
                <Multiselect id="id-select" v-model="selectIds" :options="ids" :multiple="true" :close-on-select="false"
                    :clear-on-select="false" :preserve-search="true" placeholder="Select IDs">
                </Multiselect>
            </div>
            <div class="form-group">
                <label for="date-start-date" v-if="['Time'].includes(daType)">Start Date:</label>
                <label for="date-start-text" v-else-if="daType === 'Month'">Start Month:</label>
                <input id="date-start" type="date" v-if="['Time'].includes(daType)" v-model="selectedDateStart"
                    class="input-field" />
                <input id="date-start" type="text" v-else-if="daType === 'Month'" v-model="selectedDateStart"
                    placeholder="Enter month" class="input-field" />
            </div>
            <div class="form-group">
                <label for="date-end-date" v-if="['Time'].includes(daType)">End Date:</label>
                <label for="date-end-text" v-else-if="daType === 'Month'">End Month:</label>
                <input id="date-end" type="date" v-if="['Time'].includes(daType)" v-model="selectedDateEnd"
                    class="input-field" />
                <input id="date-end" type="text" v-else-if="daType === 'Month'" v-model="selectedDateEnd"
                    placeholder="Enter month" class="input-field" />
            </div>
        </div>
        <div class="form-container">
            <div class="form-group">
                <label for="export-id-select">Export Select IDs:</label>
                <Multiselect id="export-id-select" v-model="expIds" :options="ids" :multiple="true"
                    :close-on-select="false" :clear-on-select="false" :preserve-search="true" placeholder="Select IDs">
                </Multiselect>
            </div>

            <div class="form-group">
                <label for="exp-date-start-date" v-if="['Time'].includes(daType)">Start Date:</label>
                <label for="exp-date-start-text" v-else-if="daType === 'Month'">Start Month:</label>
                <input id="exp-date-start" type="date" v-if="['Time'].includes(daType)" v-model="expDateStart"
                    class="input-field" />
                <input id="exp-date-start" type="text" v-else-if="daType === 'Month'" v-model="expDateStart"
                    placeholder="Enter month" class="input-field" />
            </div>

            <div class="form-group">
                <label for="exp-date-end-date" v-if="['Time'].includes(daType)">End Date:</label>
                <label for="exp-date-end-text" v-else-if="daType === 'Month'">End Month:</label>
                <input id="exp-date-end" type="date" v-if="['Time'].includes(daType)" v-model="expDateEnd"
                    class="input-field" />
                <input id="exp-date-end" type="text" v-else-if="daType === 'Month'" v-model="expDateEnd"
                    placeholder="Enter month" class="input-field" />
            </div>
        </div>
    </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'; // Import Vuex helpers
import Multiselect from 'vue-multiselect';

export default {
    components: { Multiselect },
    props: {
        selectedColumns: {
            type: Array,
            default: null
        }
    },
    computed: {
        // Binding selected IDs directly from Vuex
        selectIds: {
            get() {
                return this.selectedIds; // Get the value from Vuex
            },
            set(value) {
                this.updateSelectedIds(value); // Update Vuex state on change
                this.updateExportIds(value);
            }
        },
        // Binding date range (start and end) directly from Vuex
        selectedDateStart: {
            get() {
                return this.dateRange.start;
            },
            set(value) {
                this.updateSelectedDateStart(value);
                this.updateExportDateStart(value);
            }
        },
        capitalizedInterval() {
            return this.capitalizedFirstLetter(this.defaultInterval);
        },
        selectedDateEnd: {
            get() {
                return this.dateRange.end; // Get the date range from Vuex
            },
            set(value) {
                this.updateSelectedDateEnd(value);
                this.updateExportDateEnd(value);
            }
        },
        daType() {
            return this.dateType; // Get the date type from Vuex (no need to set this directly)
        },
        expIds: {
            get() {
                return this.exportIds; // Get the value from Vuex
            },
            set(value) {
                this.updateExportIds(value);
            }
        },
        expDateStart: {
            get() {
                return this.exportDate.start; // Get the date range from Vuex
            },
            set(value) {
                this.updateExportDateStart(value);
            }
        },
        expDateEnd: {
            get() {
                return this.exportDate.end; // Get the date range from Vuex
            },
            set(value) {
                this.updateExportDateEnd(value);
            }
        },
        ...mapState(['columns', 'ids', 'selectedIds', 'dateRange', 'theme', 'dateType', 'exportIds', 'exportDate', 'defaultStartDate', 'defaultEndDate', 'defaultInterval']),
    },
    data() {
        return {
        };
    },
    methods: {
        ...mapActions(['updateSelectedIds', 'updateSelectedDateStart', 'updateSelectedDateEnd', 'updateExportIds', 'updateExportDateStart', 'capitalizedFirstLetter', 'updateExportDateEnd']),
        capitalizedFirstLetter(string) {
            if (string) {
                return string.charAt(0).toUpperCase() + string.slice(1);
            }
            return "";
        },
    },
};
</script>
<style src="vue-multiselect/dist/vue-multiselect.css"></style>
<style scoped>
/* Theme variables */
.light {
    --text-color: #333;
    --bg-color: antiquewhite;
    --bg-color-ref: #f9f9f9;
    --border-color: #ccc;
    --box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.dark {
    --text-color: #f9f9f9;
    --bg-color-ref: #333;
    --bg-color: #444;
    --border-color: #666;
    --box-shadow: 0 2px 5px rgba(255, 255, 255, 0.1);
}

.select-container {
    display: flex;
    flex-direction: row;
    gap: 5px;
    margin: 0px auto;
    min-width: 45%;
    align-items: stretch;
    overflow-y: auto;
}

.form-container,
.form-container-ref {
    display: flex;
    flex-direction: column;
    gap: 5px;
    margin: 0px 0px;
    padding: 5px;
    border-radius: 4px;
    box-shadow: var(--box-shadow);
    min-height: fit-content;
}

.form-container-ref {
    background-color: var(--bg-color-ref);
}

.form-container-ref .form-group .input-field {
    background-color: var(--bg-color-ref);
}

.form-container {
    background-color: var(--bg-color);
}

.form-container .form-group .input-field {
    background-color: var(--bg-color);
}

.form-group {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 8.35rem;
}

label {
    font-weight: 600;
    margin-bottom: 5px;
    font-size: 14px;
    color: var(--text-color);
}

.input-field {
    padding: 8px;
    font-size: 14px;
    border: 1px solid var(--border-color);
    color: var(--text-color);
    border-radius: 5px;
    width: 100%;
    margin-bottom: 2px;
}

input[type="date"],
input[type="text"] {
    height: 1.5rem;
    box-sizing: border-box;
}

input[type="date"]::-webkit-calendar-picker-indicator {
    cursor: pointer;
}

input[type="text"]::placeholder {
    color: #999;
    font-style: italic;
}

@media (min-width: 1650px) {
    .form-container,
    .form-container-ref {
        flex: 1 1 200px;
        min-width: 100px;
    }
}
</style>