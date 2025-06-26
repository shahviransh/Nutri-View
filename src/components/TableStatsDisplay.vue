<template>
    <div class="main-view">
        <!-- Table Container with Scrollable Body -->
        <div class="table-container">
            <table class="styled-table">
                <thead>
                    <tr>
                        <th v-for="column in selectedColumnsFilter" :key="column">{{ column }}</th>
                    </tr>
                    <tr>
                        <th v-for="column in selectedColumnsFilter" :key="column">
                            <input type="text" v-model="columnFilters[column]" @input="onFilterChange"
                                placeholder="Filter" class="column-filter" />
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(row, index) in visibleData" :key="index">
                        <td v-for="column in selectedColumnsFilter" :key="column">{{
                            row[column] }}</td>
                    </tr>
                </tbody>
            </table>
            <!-- Load More Button -->
            <div v-if="canLoadMore" class="load-more-container">
                <button class="load-more-button" @click="loadMoreRows">Load More</button>
            </div>
        </div>
        <!-- Stats Container with Scrollable Body -->
        <div class="stats-container" v-if="statsColumns && statsColumns.length">
            <table class="styled-table">
                <thead>
                    <tr>
                        <th v-for="column in statsColumns" :key="column">{{ column }}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(row, index) in stats" :key="index">
                        <td v-for="column in statsColumns" :key="column">{{ row[column] }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        data: Array,
        stats: Array,
        selectedColumns: Array,
        statsColumns: Array,
        properties: Array,
        rowLimit: [Number],
    },
    data() {
        return {
            visibleData: [],
            canLoadMore: true,
            columnFilters: {},
        };
    },
    computed: {
        selectedColumnsFilter() {
            return this.properties ? this.selectedColumns.filter(c => !this.properties.includes(c)) : this.selectedColumns
        },
        filteredData() {
            return this.data.filter((row) => {
                return this.selectedColumnsFilter.every((col) => {
                    const filter = this.columnFilters[col];
                    return !filter || String(row[col]).toLowerCase().includes(filter.toLowerCase());
                });
            });
        },
    },
    methods: {
        // Load initial rows when the data is loaded
        loadInitialRows() {
            this.visibleData = this.filteredData.slice(0, this.rowLimit);
            this.canLoadMore = this.filteredData.length > this.rowLimit;
        },
        // Load more rows when the load more button is clicked
        loadMoreRows() {
            const nextRowLimit = this.visibleData.length + this.rowLimit;
            // Ensure we don't exceed the total number of filtered rows
            const nextRows = this.filteredData.slice(this.visibleData.length, nextRowLimit);
            this.visibleData = [...this.visibleData, ...nextRows];
            if (this.visibleData.length >= this.filteredData.length) {
                this.canLoadMore = false;
            }
        },
        onFilterChange() {
            this.loadInitialRows();
        },
    },
    watch: {
        data: {
            immediate: true,
            handler() {
                // Initialize filters
                this.selectedColumnsFilter.forEach((col) => {
                    this.columnFilters[col] = '';
                });
                this.loadInitialRows();
            }
        }
    }
};
</script>
<style src="../assets/pages.css" />

<style scoped>
.column-filter {
    width: 100%;
    padding: 4px;
    box-sizing: border-box;
}
</style>