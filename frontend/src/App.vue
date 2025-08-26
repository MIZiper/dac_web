<template>
  <v-app>
    <v-app-bar app color="primary">
      <v-img src="./assets/logo-w.png" max-height="48" max-width="48" class="ml-4"></v-img>
      <v-toolbar-title>{{ title }}</v-toolbar-title>

      <v-spacer> </v-spacer>

      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn v-bind="props" title="Scenarios">
            <v-icon>mdi-view-list</v-icon>
            {{ current_scenario }}
          </v-btn>
        </template>
        <v-list>
          <v-list-item v-for="scenario in scenarios" :key="scenario" @click="switchScenario(scenario)">
            <v-list-item-title>{{ scenario }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>

      <v-btn title="Import data"> <!-- save project, publish project -->
        <v-icon>mdi-database-import</v-icon>
      </v-btn>
      <SavePublish />
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

    <v-dialog v-model="start_dialog.is_show" persistent max-width="600px">
      <v-card>
        <v-progress-linear v-if="start_dialog.progress_bar" color="green darken-1" indeterminate></v-progress-linear>
        <v-card-title>{{ start_dialog.title }}</v-card-title>
        <v-card-text>
          {{ start_dialog.desc }}
          <span v-if="start_dialog.error" style="color: red; font-weight: bold;">{{ start_dialog.error }}</span>
        </v-card-text>
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
  </v-app>
</template>

<script>
import DataBrowser from './components/DataBrowser.vue';
import ActionBrowser from './components/ActionBrowser.vue';
import ContextList from './components/ContextList.vue';
import YamlEditor from './components/YamlEditor.vue';
import MainContent from './components/MainContent.vue';
import MessageZone from './components/MessageZone.vue';
import SavePublish from './components/SavePublish.vue';
import { VTreeview } from 'vuetify/labs/VTreeview';
import { ax_api, ax_app, SESSID_KEY, project_prefix } from '@/utils';

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

      start_dialog: {
        is_show: true,
        progress_bar: true,
        title: "Welcome to DAC",
        desc: "Initializing DAC ...",
        error: "",
      },

      actives: [],
      files: [
        {
          relpath: "/",
          name: "Projects",
          children: [],
        },
      ],

      current_scenario: 'Scenario 0',
      scenarios: ['Scenario 1', 'Scenario 2', 'Scenario 3'],
    }
  },
  mounted() {
    this.emitter.on('scenario-refresh-request', this.handleScenarioRequest);

    let pathname = window.location.pathname;
    if (pathname.startsWith(project_prefix)) {
      let project_id = pathname.substring(project_prefix.length);

      this.start_dialog.desc = "Loading project ...";
      this.start_dialog.progress_bar = true;
      this.start_dialog.error = "";

      ax_api.post('/load', { project_id: project_id }).then(response => {
        console.log(response.data['message']);

        this.start_dialog.is_show = false;

        this.initAnalysis(response.data[SESSID_KEY]);
      }).catch(error => {
        this.start_dialog.progress_bar = false;
        if (error.response.status == 404) {
          this.start_dialog.error = "Project not found, create or load one.";
        } else {
          this.start_dialog.error = "Unknown error.";
        }
        console.error("There was an error loading project:", error);
      });
    } else {
      this.start_dialog.progress_bar = false;
      this.start_dialog.desc = "Start a new analysis project or load from list below.";
    }
  },
  methods: {
    startOption(option) {
      this.start_dialog.progress_bar = true;
      if (option == 'new') {
        ax_api.post('/new').then(response => {
          console.log(response.data['message']);

          this.start_dialog.is_show = false;
          window.history.replaceState(null, null, "/"); // reset to empty, including case for unfound project
          this.initAnalysis(response.data[SESSID_KEY]);
        }).catch(error => {
          this.start_dialog.progress_bar = false;
          this.start_dialog.error = "Error while creating new session.";
          console.error("There was an error creating new session:", error);
        });
      } else if (option == 'load') {
        ax_api.post('/load_saved', { project_path: this.actives[0] }).then(response => {
          console.log(response.data['message']);

          this.start_dialog.is_show = false;
          window.history.replaceState(null, null, project_prefix + response.data['project_id']);
          this.initAnalysis(response.data[SESSID_KEY]);
        }).catch(error => {
          this.start_dialog.progress_bar = false;
          this.start_dialog.error = "Error while loading project.";
          console.error("There was an error loading project:", error);
        });
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
      ax_app.defaults.headers.common[SESSID_KEY] = sess_id;
      ax_api.defaults.headers.common[SESSID_KEY] = sess_id;

      this.emitter.emit('context-refresh-request');
      this.emitter.emit('scenario-refresh-request');
      this.emitter.emit('context_type-refresh-request');
      this.emitter.emit('action_type-refresh-request');
      this.emitter.emit('mpl-init-request', sess_id);

      window.addEventListener("beforeunload", function (e) {
        navigator.sendBeacon('/api/term', JSON.stringify({[SESSID_KEY]: sess_id}));
        // POST only triggered when refreshing page or to same domain or with the prevent dialog
        // navigator.sendBeacon is async and works
      });
    },

    handleScenarioRequest() {
      ax_app.get('/scenarios').then(response => {
        this.scenarios = response.data['scenarios'];
        this.current_scenario = response.data['current_scenario'];
      }).catch(error => {
        console.error("There was an error fetching scenario list:", error);
      });
    },
    switchScenario(scenario) {
      ax_app.post("/scenarios", {
        scenario: scenario
      }).then(response => {
        console.log(response.data['message']);
        this.current_scenario = response.data['current_scenario'];
        this.emitter.emit('context_type-refresh-request');
        this.emitter.emit('action_type-refresh-request');
      }).catch(error => {
        console.error("There was an error switching scenario:", error);
      });
    },

    fetchProjects(item) {
      if (item.children.length > 0) {
        return;
      }

      // If I return code below, only folders-in-one-chain can be opened
      // no idea how to solve

      ax_api.post('/project_files', {
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