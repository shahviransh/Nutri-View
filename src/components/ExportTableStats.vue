<template>
    <div :class="[theme, 'export-field']">
        <label for="export-stats">Export Table and/or Stats:</label>
        <Multiselect id="export-stats" v-model="selectedOptions" :options="filteredExportOptions" :multiple="true"
            :close-on-select="false" :clear-on-select="false" :preserve-search="true" placeholder="Select"
            @update:modelValue="onOptionsChange">
        </Multiselect>
    </div>
</template>
<script>
import { mapState, mapActions } from 'vuex'; // Import Vuex helpers
import Multiselect from 'vue-multiselect';
export default {
    data() {
        return {
            selectedOptions: ['Table'],
        };
    },
    components: {
        Multiselect,
    },
    computed:{
        filteredExportOptions() {
            // Conditionally include "Stats" based on our original condition
            return this.selectedStatistics.includes('None') === this.selectedMethod.includes('Equal')
                ? ['Table']
                : ['Table', 'Stats'];
        },
        tagClass() {
            return this.selectedOptions.length > 4 ? 'small-tags' : 'normal-tags';
        },
        ...mapState(["selectedStatistics", "selectedMethod", "theme"]),
    },
    methods: {
        ...mapActions(["updateExportOptions"]),
        onOptionsChange(value) {
            this.selectedOptions = value;
            this.updateExportOptions({
                table: this.selectedOptions.includes('Table'),
                stats: this.selectedOptions.includes('Stats')
            });
        },
    },
};
</script>
<style src="vue-multiselect/dist/vue-multiselect.css"></style>
<style>
.small-tags .multiselect__tag {
    font-size: 10px;
}

.normal-tags .multiselect__tag {
    font-size: 12px;
}
</style>
<style scoped>
/* Theme variables */
.light {
    color: #333;
}

/* Dark Theme */
.dark {
    color: #f0f0f0;
}

.export-field {
    display: flex;
    flex-direction: column;
    cursor: pointer;
    color: var(--color);
}

label {
    font-weight: 600;
    margin-bottom: 5px;
    font-size: 14px;
    color: var(--color);
}
</style>