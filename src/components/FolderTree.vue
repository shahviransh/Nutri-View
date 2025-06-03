<template>
    <div :class="[theme, 'folder-tree']">
        <ul class="list-group">
            <li v-for="(node, index) in treeData" :key="node.id">
                <div :class="['node', {
                    'folder-node': node.type === 'folder',
                    'file-node': node.type === 'file' || node.type === 'database' || node.type === 'table',
                    'top-level-node': index === 0,
                    'expanded': node.expanded,
                    'selected-node': node.selected
                }]" @click="toggleNode(node)">
                    <span v-if="node.type === 'folder'">{{ node.expanded ? '📂' : '📁' }}</span>
                    <span v-else-if="node.type === 'database'">🗄️</span>
                    <span v-else-if="node.type === 'table'">📑</span>
                    <span v-else>📄</span>
                    {{ node.name }}
                </div>
                <!-- Recursively display children if the node is expanded -->
                <folder-tree v-if="node.children && node.children.length > 0 && node.expanded" :treeData="node.children"
                    @select="onSelect" :page="page" />
            </li>
        </ul>
    </div>
</template>

<script>
import { mapState } from 'vuex'; // Import Vuex helpers
export default {
    name: 'FolderTree',
    props: {
        treeData: {
            type: Object,
            required: true
        },
        page: {
            type: String,
            required: true
        }
    },
    watch: {
        treeData: {
            handler(newVal) {
                this.expandNodesBasedOnPage(this.page);
            },
            deep: true
        },
        page: {
            handler(newVal) {
                this.expandNodesBasedOnPage(newVal);
            }
        }
    },
    computed: {
        ...mapState(['modelFolder', 'theme']),
    },
    methods: {
        toggleNode(node) {
            if (node.type === 'folder' || node.type === 'database') {
                // Toggle the expanded state directly
                node.expanded = !node.expanded;
                this.$emit('select', node); // Emit the folder node
            } else if (node.type === 'table' || node.type === 'file') {
                node.selected = !node.selected; // Toggle selection state
                this.$emit('select', node); // Emit selected node and if selected
            }

        },
        onSelect(node) {
            // Propagate the select event upwards
            this.$emit('select', node);
        },
        expandNodesBasedOnPage(page) {
            if (this.modelFolder.includes('Jenette_Creek_Watershed')) {
                if (page === 'Table') {
                    // Automatically expand the database node folder
                    this.expandSpecificNode(this.treeData, 'database');
                } else if (page === 'Project') {
                    // Automatically expand the Model01\Output\Scenario_2 folder
                    this.expandSpecificNode(this.treeData, 'model');
                } else if (page === 'Graph') {
                    // Automatically expand the Model01\Output\Scenario_2 folder
                    this.expandSpecificNode(this.treeData, 'model');
                } else if (page === 'Map') {
                    // Automatically expand the Geospatial & Model folder
                    this.expandSpecificNode(this.treeData, 'geospatial');
                    this.expandSpecificNode(this.treeData, 'model');
                }
            }
        },
        expandSpecificNode(nodes, targetName) {
            for (const node of nodes) {
                if (node.id == 1) {
                    node.expanded = true;
                    this.expandSpecificNode(node.children, targetName);
                    return;
                }
                if (node.name.toLowerCase().includes(targetName)) {
                    node.expanded = true;

                    // Expand the folder child nodes
                    if (node.children && node.children.length > 0) {
                        this.expandAll(node.children);
                    }
                    return;
                }
            }
        },
        expandAll(nodes) {
            for (const node of nodes) {
                if (node.type == "folder") {
                    node.expanded = true;
                    if (node.children && node.children.length > 0) {
                        this.expandAll(node.children);
                    }
                }
            }
        }
    }
};
</script>


<style scoped>
/* Theme variables */
.light {
    --text-color: #333;
    --selected-bg: #d0e8ff;
    --hover-bg: #f0f0f0;
}

.dark {
    --text-color: #f9f9f9;
    --selected-bg: #555;
    --hover-bg: #666;
}

.folder-tree {
    list-style-type: none;
    padding-left: 10px;
}

.list-group {
    padding-left: 5px;
    list-style-type: none;
}

.node {
    display: flex;
    align-items: center;
    cursor: pointer;
    margin: 5px 0;
    padding: 2px 0px;
    border-radius: 4px;
    user-select: none;
    font-size: 14px;
    word-break: break-word;
    color: var(--text-color);
}

/* Adjust padding for first-level nodes */
.top-level-node .node {
    padding-left: 0;
}

.selected-node {
    background-color: var(--selected-bg);
}

.folder-node:hover,
.file-node:hover {
    background-color: var(--hover-bg);
}

/* Use data attribute for expanded state */
.folder-node::before {
    content: '▶';
    display: inline-block;
    width: 1em;
    margin-right: 5px;
    transition: transform 0.2s ease-in-out;
}

.folder-node.expanded::before {
    /* Apply rotation when the node is expanded */
    transform: rotate(90deg);
}

/* Proper alignment of the icons and text */
.node span:first-child {
    margin-right: 5px;
}
</style>