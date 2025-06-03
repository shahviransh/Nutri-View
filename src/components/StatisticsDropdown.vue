<template>
    <div :class="[theme, 'statistics-container']">
        <label for="method-select" class="method-label">Method Conversion:</label>
        <Multiselect id="method-select" v-model="selectedMethod" :options="options" :multiple="true" :close-on-select="false"
            :clear-on-select="false" :preserve-search="true"
            @update:modelValue="onMethodChange" :class="tagClassMethod">
        </Multiselect>
        <label for="statistics-select" class="statistics-label">Select Statistics:</label>
        <Multiselect id="statistics-select" v-model="selectedStatistics" :options="option" :multiple="true" :close-on-select="false"
            :clear-on-select="false" :preserve-search="true" @update:modelValue="onStatisticsChange" :class="tagClass">
        </Multiselect>
    </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'; // Import Vuex helpers
import Multiselect from 'vue-multiselect';

export default {
    data() {
        return {
            selectedStatistics: ["None"],
            option: ["None", "Average", "Sum", "Maximum", "Minimum", "Standard Deviation"],
            selectedMethod: ["Equal"],
            options: ["Equal", "Average", "Sum", "Maximum", "Minimum"],
        };
    },
    computed: {
        tagClass() {
            return this.selectedStatistics.length > 3 ? 'small-tags' : 'normal-tags';
        },
        tagClassMethod() {
            return this.selectedMethod.length > 3 ? 'small-tags' : 'normal-tags';
        },
        ...mapState(["theme"]),
    },
    components: {
        Multiselect,
    },
    methods: {
        ...mapActions(["updateSelectedStatistics", "updateSelectedMethod"]),
        onStatisticsChange() {
            this.selectedStatistics = this.selectedStatistics.length > 1 ? this.selectedStatistics.filter(stat => stat !== "None") : ["None"];
            this.updateSelectedStatistics(this.selectedStatistics);
        },
        onMethodChange() {
            this.selectedMethod = this.selectedMethod.length > 1 ? this.selectedMethod.filter(method => method !== "Equal") : ["Equal"];
            this.updateSelectedMethod(this.selectedMethod);
        },
    },
};
</script>
<style src="vue-multiselect/dist/vue-multiselect.css"></style>
<style>
.multiselect {
    font-size: 14px;
}

.multiselect__tag {
    padding: 2px 18px 2px 5px;
    margin-right: 5px;
    font-size: 12px;
}

.multiselect__tag-icon {
    line-height: 16px;
}

.small-tags .multiselect__tag {
    font-size: 8px;
}

.normal-tags .multiselect__tag {
    font-size: 12px;
}
</style>
<style scoped>
/* Theme variables */
.light {
    --text-color: #333;
    --bg-color: antiquewhite;
    --box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.dark {
    --text-color: #f9f9f9;
    --bg-color: #444;
    --box-shadow: 0 2px 5px rgba(255, 255, 255, 0.1);
}

.statistics-container {
    display: flex;
    flex-direction: column;
    gap: 5px;
    margin: 0px 0px;
    padding: 5px;
    border-radius: 4px;
    box-shadow: var(--box-shadow);
    background-color: var(--bg-color);
    z-index: 1000;
}

.statistics-label {
    font-weight: 600;
    margin-bottom: 0px;
    font-size: 14px;
    color: var(--text-color);
}

.method-label {
    font-weight: 600;
    font-size: 14px;
    color: var(--text-color);
    margin-bottom: 0px;
}

@media (min-width: 1650px) {
    .statistics-container {
        flex: 1 1 200px;
        min-width: 200px;
    }
}
</style>