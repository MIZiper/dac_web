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
        <v-card-text>Start a new analysis or load an existing project</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="green darken-1" text @click="startOption('new')">New</v-btn>
          <v-btn color="green darken-1" text :disabled="!actives.length" @click="startOption('load')">Load</v-btn>
          <!-- <v-btn color="green darken-1" text @click="startOption('test')">TestApp</v-btn> -->
        </v-card-actions>
        <v-treeview :items="files" :load-children="fetchProjects" v-model:activated="actives" density="compact"
          item-title="name" item-value="relpath" open-on-click activatable>
          <template v-slot:prepend="{ item }">
            <v-icon v-if="item.children">mdi-folder</v-icon>
            <v-icon v-else>mdi-file</v-icon>
          </template>
        </v-treeview>
      </v-card>
    </v-dialog>

    <v-dialog v-model="load_dialog" persistent max-width="600px">
      <v-card>
        <v-progress-linear color="green darken-1" indeterminate></v-progress-linear>
        <v-card-title>Load project</v-card-title>
        <v-card-text>Loading project ...</v-card-text>
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
import { VTreeview } from 'vuetify/labs/VTreeview';
import { ax_router, ax_app, SESSID_KEY, site_prefix } from '@/utils';

export default {
  components: {
    DataBrowser,
    ActionBrowser,
    ContextList,
    YamlEditor,
    MainContent,
    MessageZone,
    VTreeview,
  },
  data() {
    return {
      title: "DAC analysis frame",
      start_dialog: true,
      load_dialog: false,

      actives: [],
      files: [
        {
          relpath: "/",
          name: "Projects",
          children: [],
        },
      ],

      current_plugin: 'Plugin 0',
      plugins: ['Plugin 1', 'Plugin 2', 'Plugin 3'],
    }
  },
  mounted() {
    this.emitter.on('plugin-refresh-request', this.handlePluginRequest);

    let pathname = window.location.pathname;
    const project_prefix = site_prefix + "/projects/";
    if (pathname.startsWith(project_prefix)) {
      let project_id = pathname.substring(project_prefix.length);

      this.start_dialog = false;
      this.load_dialog = true;

      ax_router.post('/load', { project_id: project_id }).then(response => {
        console.log(response.data['message']);
        ax_app.defaults.headers.common[SESSID_KEY] = response.data[SESSID_KEY];
        this.load_dialog = false;
        this.initAnalysis(response.data[SESSID_KEY]);
      }).catch(error => {
        console.error("There was an error loading project:", error);
      });
    }
  },
  methods: {
    startOption(option) {
      if (option == 'new') {
        ax_router.post('/new').then(response => {
          console.log(response.data['message']);
          ax_app.defaults.headers.common[SESSID_KEY] = response.data[SESSID_KEY];

          this.start_dialog = false;
          this.initAnalysis(response.data[SESSID_KEY]);
        }).catch(error => {
          console.error("There was an error creating new session:", error);
        });
      } else if (option == 'load') {
        // display project browser
        // ax_router.post('/load') // or redirect to /projects/xxxx-yy-zzzz
      } else {
        // directly go to app_entry.py, for dev/debug
        // change in utils.js the url

        ax_app.post('/init', {}).then(response => {
          console.log(response.data['message']);

          this.start_dialog = false;
          this.initAnalysis("not-mandatory");
        }).catch(error => {
          console.error("There was an error:", error);
        });
      }
    },
    initAnalysis(sess_id) {
      this.emitter.emit('context-refresh-request');
      this.emitter.emit('plugin-refresh-request');
      this.emitter.emit('context_type-refresh-request');
      this.emitter.emit('action_type-refresh-request');
      this.emitter.emit('mpl-init-request', sess_id);
    },

    handlePluginRequest() {
      ax_app.get('/plugins').then(response => {
        this.plugins = response.data['plugins'];
        this.current_plugin = response.data['current_plugin'];
      }).catch(error => {
        console.error("There was an error fetching plugin list:", error);
      });
    },
    switchPlugin(plugin) {
      ax_app.post("/plugins", {
        plugin: plugin
      }).then(response => {
        console.log(response.data['message']);
        this.current_plugin = response.data['current_plugin'];
        this.emitter.emit('context_type-refresh-request');
        this.emitter.emit('action_type-refresh-request');
      }).catch(error => {
        console.error("There was an error switching plugin:", error);
      });
    },

    fetchProjects(item) {
      if (item.children.length > 0) {
        return;
      }

      // If I return code below, only folders-in-one-chain can be opened
      // no idea how to solve

      ax_router.post('/project_files', {
        relpath: item.relpath,
      }).then(response => {
        response.data['dirnames'].forEach(d => {
          item.children.push({
            relpath: item.relpath + d + "/",
            name: d,
            children: [],
          });
        });
        response.data['filenames'].forEach(f => {
          item.children.push({
            relpath: item.relpath + f,
            name: f,
          });
        });
      }).catch(error => {
        console.error("There was an error fetching projects:", error);
      })
    },
  }
}
</script>

<style>
/* Add global styles here */
</style>