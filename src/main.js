import { createApp } from 'vue';
import App from './App.vue';
import store from './store'; // Import the Vuex store
import router from './router'; // Import the Vue Router

createApp(App)
  .use(store) // Register Vuex store
  .use(router) // Register Vue Router
  .mount('#app');