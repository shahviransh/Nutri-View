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

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";
import { mapState } from "vuex";
const { theme } = mapState(["theme"]);

const permissions = ref({
    read: false,
    write: false,
    upload: false,
    download: false,
});
const permissionKeys = Object.keys(permissions.value);

const loading = ref(false);
const message = ref("");
const error = ref("");

const fetchPermissions = async () => {
    try {
        const res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/guest-permissions`, {
            headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        });
        permissions.value = { ...permissions.value, ...res.data };
    } catch (err) {
        error.value = "Failed to fetch guest permissions.";
    }
};

const savePermissions = async () => {
    loading.value = true;
    message.value = "";
    error.value = "";
    try {
        await axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/guest-permissions`, permissions.value, {
            headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        });
        message.value = "Guest permissions updated successfully.";
    } catch (err) {
        error.value = "Failed to save guest permissions.";
    } finally {
        loading.value = false;
    }
};

onMounted(fetchPermissions);
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
