<template>
    <div :class="[theme, 'interval-container']">
        <label for="interval-select" class="interval-label">Select Interval:</label>
        <select id="interval-select" v-model="selectInterval" class="interval-dropdown">
            <option value="daily">Daily</option>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
            <option value="seasonally">Seasonally</option>
        </select>

        <label for="export-interval-select" class="interval-label">Export Select Interval:</label>
        <select id="export-interval-select" v-model="expInterval" @change="onExportChange" class="interval-dropdown">
            <option value="daily">Daily</option>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
            <option value="seasonally">Seasonally</option>
        </select>
        <!-- Use v-show instead of v-if -->
        <div v-show="shouldShowMonth">
            <label for="month-interval-select" class="interval-label">Select Month:</label>
            <select id="month-interval-select" v-model="monInterval" class="interval-dropdown">
                <option v-for="month in months" :key="month.value" :value="month.value">
                    {{ month.label }}
                </option>
            </select>
        </div>

        <div v-show="shouldShowSeason">
            <label for="season-interval-select" class="interval-label">Select Season:</label>
            <select id="season-interval-select" v-model="seaInterval" class="interval-dropdown">
                <option value="summer">Summer</option>
                <option value="fall">Fall</option>
                <option value="winter">Winter</option>
                <option value="spring">Spring</option>
            </select>
        </div>
    </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'; // Import Vuex helpers

export default {
    data() {
        return {
        };
    },
    computed: {
        selectInterval: {
            get() {
                return this.selectedInterval;
            },
            set(value) {
                this.updateSelectedInterval(value);
                this.updateExportInterval(value); // Update export interval as well to match selected interval
                this.checkMethodSelection(value);
            }
        },
        expInterval: {
            get() {
                return this.exportInterval;
            },
            set(value) {
                this.updateExportInterval(value);
            }
        },
        monInterval: {
            get() {
                return this.selectedMonth;
            },
            set(value) {
                this.updateSelectedMonth(value);
            }
        },
        seaInterval: {
            get() {
                return this.selectedSeason;
            },
            set(value) {
                this.updateSelectedSeason(value);
            }
        },
        shouldShowMonth() {
            return [this.selectInterval, this.expInterval].includes("monthly") && this.pageTitle === "Map";
        },
        shouldShowSeason() {
            return [this.selectInterval, this.expInterval].includes("seasonally") && this.pageTitle === "Map";
        },
        months() {
            return [
                { value: "1", label: "January" },
                { value: "2", label: "February" },
                { value: "3", label: "March" },
                { value: "4", label: "April" },
                { value: "5", label: "May" },
                { value: "6", label: "June" },
                { value: "7", label: "July" },
                { value: "8", label: "August" },
                { value: "9", label: "September" },
                { value: "10", label: "October" },
                { value: "11", label: "November" },
                { value: "12", label: "December" },
            ];
        },
        ...mapState(["selectedInterval", "exportInterval", "selectedSeason", "selectedMethod", "selectedMonth", "theme", "pageTitle"]),
    },
    methods: {
        ...mapActions(["updateSelectedInterval", "updateExportInterval", "updateSelectedMonth", "updateSelectedSeason"]),
        onExportChange() {
            if (this.isValidExportInterval(this.selectedInterval, this.exportInterval)) {
                this.updateExportInterval(this.exportInterval);
            } else {
                alert("Export interval cannot be less than the selected interval.");
                this.updateExportInterval(this.selectedInterval);
            }
        },
        isValidExportInterval(importInterval, exportInterval) {
            const intervals = ["daily", "monthly", "seasonally", "yearly"];
            return intervals.indexOf(exportInterval) >= intervals.indexOf(importInterval);
        },
        checkMethodSelection(interval) {
            if (interval !== "daily" && (!this.selectedMethod || this.selectedMethod.includes("Equal"))) {
                alert("Please choose at least one of Average, Sum, Minimum, or Maximum from the Method Conversion.");
            }
        }
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

.interval-container {
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-height: fit-content;
    margin: 0px 0px;
    padding: 5px;
    background-color: var(--bg-color);
    border-radius: 4px;
    box-shadow: var(--box-shadow);
}

.interval-label {
    font-weight: 600;
    margin-bottom: 0px;
    font-size: 14px;
    color: var(--text-color);
}

.interval-dropdown {
    padding: 5px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-color);
    font-size: 14px;
    color: var(--text-color);
    cursor: pointer;
    box-shadow: var(--box-shadow);
    transition: border-color 0.2s ease-in-out;
}

.interval-dropdown:hover {
    border-color: var(--focus-border);
}

.interval-dropdown:focus {
    border-color: var(--focus-border);
    outline: none;
}

@media (min-width: 1650px) {
    .interval-container {
        flex: 1 1 200px;
        min-width: 200px;
    }
}
</style>