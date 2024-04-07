/**
 * main.js
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins
import { registerPlugins } from '@/plugins'

// Components
import App from './App.vue'

// Composables
import { createApp } from 'vue'

import mitt from 'mitt';

const app = createApp(App)
const emitter = mitt();
app.config.globalProperties.emitter = emitter;

registerPlugins(app)

app.mount('#app')
