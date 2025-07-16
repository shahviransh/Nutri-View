<template>
    <div :class="['container', theme]">
        <h2>Guest Permissions Management</h2>

        <div class="permissions">
            <label v-for="perm in permissionKeys" :key="perm" class="permission-toggle">
                <input type="checkbox" v-model="permissions[perm]" />
                {{ perm.charAt(0).toUpperCase() + perm.slice(1) }}
            </label>
        </div>

        <button @click="savePermissions" :disabled="loading" :class="{ disabled: loading }">
            {{ loading ? "Saving..." : "Save Changes" }}
        </button>

        <p v-if="message" class="message">{{ message }}</p>
        <p v-if="error" class="error">{{ error }}</p>
    </div>
</template>

<script>
import axios from "axios";
import { mapState } from "vuex";

export default {
    name: "GuestPermissions",
    computed: {
        ...mapState(["theme"]),
        permissionKeys() {
            return Object.keys(this.permissions);
        }
    },
    data() {
        return {
            permissions: {
                read: false,
                write: false,
                upload: false,
                download: false
            },
            loading: false,
            message: "",
            error: ""
        };
    },
    methods: {
        async fetchPermissions() {
            try {
                const res = await axios.get(
                    `${import.meta.env.VITE_API_BASE_URL}/api/guest-permissions`,
                    {
                        headers: {
                            Authorization: `Bearer ${localStorage.getItem("token")}`
                        }
                    }
                );
                this.permissions = { ...this.permissions, ...res.data };
            } catch (err) {
                this.error = "Failed to fetch guest permissions.";
            }
        },
        async savePermissions() {
            this.loading = true;
            this.message = "";
            this.error = "";
            try {
                const res = await axios.post(
                    `${import.meta.env.VITE_API_BASE_URL}/api/guest-permissions`,
                    this.permissions,
                    {
                        headers: {
                            Authorization: `Bearer ${localStorage.getItem("token")}`,
                            "Content-Type": "application/json"
                        }
                    }
                );
                this.message = "Guest permissions updated successfully.";
                // If the API returns the updated perms:
                if (res.data.permissions) {
                    this.permissions = { ...this.permissions, ...res.data.permissions };
                }
            } catch (err) {
                this.error = "Failed to save guest permissions.";
            } finally {
                this.loading = false;
            }
        }
    },
    mounted() {
        this.fetchPermissions();
    }
};
</script>

<style scoped>
.light {
    --bg-color: #fefefe;
    --text-color: #000000;
    --primary-color: #0066cc;
    --disabled-color: #cccccc;
    --message-color: green;
    --error-color: red;
}

.dark {
    --bg-color: #2e2e2e;
    --text-color: #fafafa;
    --primary-color: #3399ff;
    --disabled-color: #555555;
    --message-color: #8f8;
    --error-color: #f88;
}

.container {
    max-width: 400px;
    margin: 40px auto;
    padding: 24px;
    border: 1px solid #ccc;
    border-radius: 12px;
    background-color: var(--bg-color);
    color: var(--text-color);
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.06);
}

h2 {
    font-size: 1.4rem;
    margin-bottom: 20px;
    text-align: center;
}

.permissions {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 20px;
    color: var(--text-color);
}

.permission-toggle {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 500;
    color: var(--text-color);
}

button {
    width: 100%;
    padding: 10px 0;
    border: none;
    border-radius: 6px;
    color: var(--primary-color);
    font-weight: bold;
    cursor: pointer;
    transition: background-color 0.2s;
}

button:disabled {
    background-color: var(--disabled-color);
    cursor: not-allowed;
}

.message {
    color: var(--message-color);
    text-align: center;
    margin-top: 10px;
}

.error {
    color: var(--error-color);
    text-align: center;
    margin-top: 10px;
}
</style>
