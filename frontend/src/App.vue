<template>
  <v-app>
    <v-app-bar app color="primary">
      <v-img src="./assets/logo-w.png" max-height="48" max-width="48" class="ml-4"></v-img>
      <v-toolbar-title>{{ title }}</v-toolbar-title>

      <v-spacer> </v-spacer>

      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn v-bind="props" title="Plugins">
            <v-icon>mdi-view-list</v-icon>
            {{ current_plugin }}
          </v-btn>
        </template>
        <v-list>
          <v-list-item v-for="plugin in plugins" :key="plugin" @click="switchPlugin(plugin)">
            <v-list-item-title>{{ plugin }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>

      <v-btn title="Import data"> <!-- save project, publish project -->
        <v-icon>mdi-download</v-icon>
      </v-btn>
      <v-btn title="Open project">
        <v-icon>mdi-folder-open</v-icon>
      </v-btn>
    </v-app-bar>

    <v-container fluid class="mt-16">
      <v-row>
        <v-col>
          <ContextList class="mb-4" />
          <v-row style="height: 65vh;" class="ma-0">
            <DataBrowser style="width: 49%;" />
            <v-spacer></v-spacer>
            <ActionBrowser style="width: 49%;" />
          </v-row>
          <YamlEditor class="mt-4" />
        </v-col>
        <v-col>
          <MainContent class="mb-4" />
          <MessageZone />
        </v-col>
      </v-row>
    </v-container>

    <v-dialog v-model="start_dialog" persistent max-width="600px">
      <v-card>
        <v-card-title>Start analysis</v-card-title>
        <v-card-text style="color: red; font-weight: bold;">Site under development, service not yet
          available</v-card-text>
        <v-card-text>Choose the options below to start analysis</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="green darken-1" text @click="startOption('new')">New</v-btn>
          <v-btn color="green darken-1" text @click="startOption('load')">Load</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script>
import DataBrowser from './components/DataBrowser.vue';
import ActionBrowser from './components/ActionBrowser.vue';
import ContextList from './components/ContextList.vue';
import YamlEditor from './components/YamlEditor.vue';
import MainContent from './components/MainContent.vue';
import MessageZone from './components/MessageZone.vue';
import axios from 'axios'
import { ax_base, ax_project } from '@/utils';

export default {
  components: {
    DataBrowser,
    ActionBrowser,
    ContextList,
    YamlEditor,
    MainContent,
    MessageZone
  },
  data() {
    return {
      title: "DAC analysis frame",
      start_dialog: true,

      current_plugin: 'Plugin 0',
      plugins: ['Plugin 1', 'Plugin 2', 'Plugin 3'],
    }
  },
  mounted() {
    this.emitter.on('plugin-refresh-request', this.handlePluginRequest);
  },
  methods: {
    startOption(option) {
      if (option == 'new') {
        /*
        ax_base.post('/new').then(response => {
          sess_id = response.data['dac-sess_id'];
          sessionStorage.setItem('sess_id', sess_id);
          this.start_dialog = false;
        }).catch(error => {
          console.error("There was an error creating new session:", error);
        });
        */
        this.start_dialog = false;
        this.initAnalysis();
      } else {
        /*
        ax_base.get('/projects/', {
          headers: {
            'dac-sess_id': sessionStorage.getItem('sess_id')
          }
        }).then(response => {

        }).catch(error => {
          console.error("There was an error loading project:", error);
        });
        */
        ax_project.post('init', {}).then(response => {
          console.log(response.data['message']);
          this.start_dialog = false;
          this.initAnalysis();
        }).catch(error => {
          console.error("There was an error loading project:", error);
        });
      }
    },
    initAnalysis() {
      this.emitter.emit('context-refresh-request');
      this.emitter.emit('plugin-refresh-request');
      this.emitter.emit('context_type-refresh-request');
      this.emitter.emit('action_type-refresh-request');
    },

    handlePluginRequest() {
      ax_project.get('plugins').then(response => {
        this.plugins = response.data['plugins'];
        this.current_plugin = response.data['current_plugin'];
      }).catch(error => {
        console.error("There was an error fetching plugin list:", error);
      });
    },
    switchPlugin(plugin) {
      ax_project.post("plugins", {
        plugin: plugin
      }).then(response => {
        console.log(response.data['message']);
        this.current_plugin = response.data['current_plugin'];
        this.emitter.emit('context_type-refresh-request');
        this.emitter.emit('action_type-refresh-request');
      }).catch(error => {
        console.error("There was an error switching plugin:", error);
      });
    }
  }
}
</script>

<style>
/* Add global styles here */
</style>