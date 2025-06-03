<template>
    <div :class="[theme, 'popup']">
        <div class="popup-content">
            <button class="close-button" @click="closePopup">&times;</button>
            <div class="mode-selection">
                <label>
                    <input type="radio" v-model="mode" value="auto" /> Auto Mode
                </label>
                <label>
                    <input type="radio" v-model="mode" value="manual" /> Manual Mode
                </label>
            </div>

            <h3>Preview:</h3>
            <div class="preview">
                <p>{{ preview }}</p>
            </div>

            <h4>Selected Columns:</h4>
            <div class="buttons">
                <button v-for="col in selectColumns" :key="col" :disabled="mode === 'auto' || stack.includes(col)"
                    @click="handleColumnClick(col)">
                    {{ col }}
                </button>
            </div>

            <div class="calculator-grid">
                <button v-for="num in numbers" :key="num" class="number" @click="handleNumberClick(num)">
                    {{ num }}
                </button>
                <button class="decimal" @click="handleDecimalClick">.</button>
                <button v-for="operator in operators" :key="operator" class="operator"
                    @click="handleOperatorClick(operator)">
                    {{ operator }}
                </button>
                <button class="backspace" @click="handleBackspace">⌫</button>
                <button class="equal" @click="saveFormula(true)">=</button>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState, mapActions } from "vuex";

export default {
    data() {
        return {
            mode: "auto", // 'auto' or 'manual'
            preview: this.mathFormula || "",
            currentNumber: "",
            selectedOperator: null,
            numbers: Array.from({ length: 10 }, (_, i) => i.toString()),
            operators: ["+", "-", "*", "/"],
            stack: [],
        };
    },
    computed: {
        ...mapState(["selectedColumns", "theme", "mathFormula", "idColumn", "dateType", "geoColumns"]),
        selectColumns() {
            return this.selectedColumns.filter(
                (col) => !this.geoColumns.includes(col) && col !== this.dateType && col !== this.idColumn
            );
        }
    },
    methods: {
        ...mapActions(["updateCalculation", "pushMessage"]),
        handleColumnClick(col) {
            if (this.mode !== "manual") {
                return;
            }
            this.preview += col;
            this.stack.push(col);
            this.saveFormula();
        },
        handleNumberClick(num) {
            if (this.mode === "auto" && !this.selectedOperator) {
                this.currentNumber += num;
                this.preview = this.currentNumber;
            } else if (this.mode === "manual") {
                this.preview += num;
            }
            this.saveFormula();
        },
        handleDecimalClick() {
            if (this.mode === "auto" && !this.currentNumber.includes(".")) {
                this.currentNumber += ".";
                this.preview = this.currentNumber;
            } else if (this.mode === "manual" && !this.preview.endsWith(".")) {
                this.preview += ".";
            }
            this.saveFormula();
        },
        handleOperatorClick(operator) {
            if (this.mode === "auto") {
                // Check if currentNumber is not empty, then append operator to it and selectedColumns
                // If empty, append operator to selectedColumns
                this.preview = this.currentNumber ? this.selectColumns
                    .map((col) => `${this.currentNumber}${operator}${col}`)
                    .join(", ") : this.selectColumns
                        .map((col) => `${col}`)
                        .join(` ${operator} `);
                this.selectedOperator = operator;
            } else if (this.mode === "manual") {
                this.preview += ` ${operator} `;
            }
            this.saveFormula();
        },
        handleBackspace() {
            if (this.mode === "manual") {
                const lastChar = this.preview.slice(-1);
                if (lastChar === " ") {
                    this.preview = this.preview.slice(0, -3); // Remove operator and spaces
                } else if (this.operators.includes(lastChar)) {
                    this.preview = this.preview.slice(0, -2); // Remove operator and space
                } else if (this.numbers.includes(lastChar) || lastChar === ".") {
                    this.preview = this.preview.slice(0, -1); // Remove last number or decimal
                } else {
                    this.preview = this.preview.replace(this.stack.pop(), ""); // Remove last column
                }
            } else if (this.mode === "auto") {
                if (this.currentNumber) {
                    this.currentNumber = this.currentNumber.slice(0, -1);
                    this.preview = this.currentNumber;
                } else if (this.selectedOperator) {
                    this.selectedOperator = null;
                    this.preview = "";
                }
            }
            this.saveFormula();
        },
        saveFormula(message = false) {
            this.updateCalculation(this.preview);
            if (message) {
                this.pushMessage({ message: `Formula Saved: ${this.preview}`, type: 'success' });
                this.closePopup();
            }
        },
        closePopup() {
            this.$emit("closePopup");
        },
    },
};
</script>

<style>
.light {
    --top-bar-bg: #f57c00;
    --top-bar-text: #ffffff;
    --taskbar-bg: #f5f5f5;
    --taskbar-text: #333333;
    --active-bg: #4caf50;
    --button-hover-bg: #388e3c;
    --border-color: #e0e0e0;
}


.dark {
    --top-bar-bg: #212121;
    --top-bar-text: #e0e0e0;
    --taskbar-bg: #424242;
    --taskbar-text: #bdbdbd;
    --active-bg: #64dd17;
    --button-hover-bg: #1b5e20;
    --border-color: #616161;
}

.popup {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1200;
}

.popup-content {
    background: var(--top-bar-bg);
    color: var(--top-bar-text);
    padding: 20px;
    border-radius: 12px;
    width: 300px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    font-family: 'Roboto', sans-serif;
    animation: fadeIn 0.3s ease-in-out;
    position: relative;
}

/* Smooth fade-in animation */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: scale(0.9);
    }

    to {
        opacity: 1;
        transform: scale(1);
    }
}

.mode-selection label {
    font-size: 16px;
    font-weight: 500;
    color: var(--taskbar-text);
    margin-right: 15px;
    cursor: pointer;
}

.mode-selection input[type="radio"] {
    margin-right: 5px;
}

.preview {
    margin-top: 10px;
    padding: 10px;
    background: var(--taskbar-bg);
    border: 1px solid var(--active-bg);
    border-radius: 8px;
    font-size: 14px;
    font-family: 'Courier New', monospace;
    color: var(--taskbar-text);
    text-align: center;
    overflow-y: auto;
}


.calculator-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 5px;
    margin-top: 10px;
}

button {
    background: var(--taskbar-bg);
    color: var(--top-bar-text);
    border: none;
    border-radius: 8px;
    padding: 15px;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: center;
}

button:hover {
    background: var(--button-hover-bg);
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

button:disabled {
    background: #ccc;
    cursor: not-allowed;
}

.number {
    grid-column: span 1;
}

.operator {
    background: var(--active-bg);
    grid-column: span 1;
}

.decimal {
    grid-column: span 1;
}

.backspace {
    background: #f44336;
    color: #fff;
    grid-column: span 1;
    font-size: 20px;
    font-weight: bold;
}

.equal {
    background: #d1c4e9;
    color: #000;
    grid-column: span 2;
    font-size: 20px;
    font-weight: bold;
}

.buttons {
    margin-top: 10px;
    display: flex;
    flex-wrap: wrap;
    max-height: 100px;
    overflow-y: auto;
    justify-content: center;
}

.close-button {
    position: absolute;
    top: 10px;
    right: 10px;
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: var(--text-color);
    z-index: 1300;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>