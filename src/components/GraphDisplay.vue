<template>
    <div class="graph-display">
        <v-chart :option="chartOptions" :theme="theme" :key="refreshKey" autoresize></v-chart>
    </div>
</template>

<script>
import { use } from 'echarts/core';
import { LineChart, ScatterChart, BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, TitleComponent, LegendComponent, DataZoomComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import VChart from 'vue-echarts';

use([LineChart, BarChart, ScatterChart, GridComponent, TooltipComponent, TitleComponent, DataZoomComponent, LegendComponent, CanvasRenderer]);

export default {
    name: "GraphDisplay",
    components: {
        VChart,
    },
    props: {
        data: Array,
        selectedColumns: Array,
        selectedIds: Array,
        dateType: String,
        ID: String,
        theme: String,
        refreshKey: Number,
        currentZoomStart: Number,
        currentZoomEnd: Number,
        multiGraphType: Array,
        graphType: String,
    },
    methods: {
        getType(column) {
            // Use the Vuex state multiGraphType, which updates dynamically
            if (this.multiGraphType?.length > 0) {
                const multiGraph = this.multiGraphType.find(col => col.name === column);
                if (multiGraph) {
                    return multiGraph.type;
                }
            }
            // Handle cases where graphType contains a dash ('-')
            if (this.graphType.includes('-')) {
                return this.graphType.split('-')[0];
            }
            return this.graphType;
        },
        columnNeedsSecondaryAxis(column) {
            // Adjust logic based on actual data thresholds
            return this.data.some(row => row[column] > 100);
        },
    },
    computed: {
        chartOptions() {
            const xAxisData = this.data.map(row => row[this.dateType]);

            // Preprocess `this.data` to create a lookup table for each ID and Date/Month
            const dataLookup = {};
            this.data.forEach(row => {
                const id = row[this.ID];
                const date = row[this.dateType];

                if (!dataLookup[id]) {
                    dataLookup[id] = {};
                }
                dataLookup[id][date] = row;
            });

            // Create the chart options
            return {
                tooltip: {
                    trigger: 'axis',
                },
                legend: {
                    top: 'bottom',
                    type: 'scroll',
                    orient: 'horizontal',
                    // Exclude Date/Month from the legend
                    data: this.selectedIds.length
                        ? this.selectedColumns
                            .filter(column => column !== this.dateType && column !== this.ID)
                            .flatMap(column =>
                                this.selectedIds.map(id => `${column} - ${this.ID}: ${id}`)
                            ) // Legend entries in the format "Col - ID"
                        : this.selectedColumns.filter(column => column !== this.dateType)
                },
                grid: {
                    left: '4%',
                    right: '2%',
                    bottom: '10%',
                    top: '5%',
                    containLabel: true
                },
                dataZoom: [
                    {
                        type: 'slider',
                        start: this.currentZoomStart,
                        end: this.currentZoomEnd,
                        height: 20
                    },
                    {
                        type: 'inside',
                        start: this.currentZoomStart,
                        end: this.currentZoomEnd
                    }
                ],
                xAxis: {
                    type: 'category',
                    data: xAxisData,
                    name: this.dateType,
                    nameLocation: 'middle',
                    nameTextStyle: {
                        fontSize: 14,
                        padding: 10,
                        color: this.theme === 'dark' ? 'white' : 'black',
                    },
                    axisLabel: {
                        fontSize: 14,
                        color: this.theme === 'dark' ? 'white' : 'black',
                    },
                    axisLine: {
                        lineStyle: {
                            color: this.theme === 'dark' ? 'white' : 'black',
                            width: 2
                        }
                    },
                    splitLine: {
                        show: false
                    }
                },
                yAxis: [
                    {
                        type: 'value',
                        name: 'Values',
                        nameLocation: 'middle',
                        nameTextStyle: {
                            fontSize: 14,
                            padding: 15,
                            color: this.theme === 'dark' ? 'white' : 'black',
                        },
                        axisLabel: {
                            fontSize: 14,
                            color: this.theme === 'dark' ? 'white' : 'black',
                        },
                        axisLine: {
                            show: true,
                            lineStyle: {
                                color: this.theme === 'dark' ? 'white' : 'black',
                                width: 2
                            }
                        },
                        axisTick: {
                            alignWithLabel: true,
                        },
                        splitLine: {
                            lineStyle: {
                                type: 'dashed',
                                color: this.theme === 'dark' ? '#333' : '#ccc',
                            },
                        },
                        alignTicks: true,
                        scale: true,
                    },
                    {
                        type: 'value',
                        nameLocation: 'middle',
                        nameTextStyle: {
                            fontSize: 14,
                            padding: 10,
                            color: this.theme === 'dark' ? 'white' : 'black',
                        },
                        axisLabel: {
                            fontSize: 14,
                            color: this.theme === 'dark' ? 'white' : 'black',
                        },
                        axisLine: {
                            show: true,
                            lineStyle: {
                                color: this.theme === 'dark' ? 'white' : 'black',
                                width: 2
                            }
                        },
                        splitLine: {
                            show: false
                        },
                    }
                ],
                series: this.selectedIds.length
                    ? this.selectedColumns // Exclude Date/Month from the series
                        .filter(column => column !== this.dateType && column !== this.ID)
                        // Create a series for each ID and Date/Month
                        .flatMap(column =>
                            this.selectedIds.map(id => ({
                                name: `${column} - ${this.ID}: ${id}`,
                                type: this.getType(column),
                                yAxisIndex: this.columnNeedsSecondaryAxis(column) ? 1 : 0, // Dynamically assign y-axis
                                data: xAxisData.map(date => {
                                    const row = dataLookup[id] && dataLookup[id][date];
                                    return row ? row[column] : null;
                                })
                            }))
                        )
                    : this.selectedColumns
                        .filter(column => column !== this.dateType)
                        // Create a series for each column
                        .map(column => ({
                            name: column,
                            type: this.getType(column),
                            yAxisIndex: this.columnNeedsSecondaryAxis(column) ? 1 : 0, // Dynamically assign y-axis
                            data: this.data.map(row => row[column])
                        }))
            };
        },
    }
};
</script>

<style scoped>
.graph-display {
    width: 100%;
    height: 100%;
    overflow: hidden;
    display: flex;
}
</style>