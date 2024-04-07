<template>
  <v-app>
    <v-app-bar app color="primary">
      <v-img src="./assets/logo-w.png" max-height="48" max-width="48" class="ml-4"></v-img>
      <v-toolbar-title>{{ title }}</v-toolbar-title>

      <v-spacer> </v-spacer>

      <v-btn icon>
        <v-icon>mdi-account-circle</v-icon>
      </v-btn>
      <v-btn icon>
        <v-icon>mdi-settings</v-icon>
      </v-btn>
      <v-btn icon>
        <v-icon>mdi-help-circle</v-icon>
      </v-btn>
    </v-app-bar>

    <v-container fluid class="mt-16">
      <v-row>
        <v-col cols="4">
          <v-row style="height: 75vh;" class="ma-0">
            <ObjectBrowser style="width: 49%;" />
            <v-spacer></v-spacer>
            <ActionBrowser style="width: 49%;" />
          </v-row>
          <YamlEditor class="mt-4" />
        </v-col>
        <v-col cols="8">
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
import ObjectBrowser from './components/ObjectBrowser.vue';
import ActionBrowser from './components/ActionBrowser.vue';
import YamlEditor from './components/YamlEditor.vue';
import MainContent from './components/MainContent.vue';
import MessageZone from './components/MessageZone.vue';
import axios from 'axios'

export default {
  components: {
    ObjectBrowser,
    ActionBrowser,
    YamlEditor,
    MainContent,
    MessageZone
  },
  data() {
    return {
      title: "DAC analysis frame",
      start_dialog: true,
    }
  },
  methods: {
    startOption(option) {
      if (option == 'new') {
        axios.post('/new').then(response => {
          sess_id = response.data['dac-sess_id'];
          sessionStorage.setItem('sess_id', sess_id);
          this.start_dialog = false;
        }).catch(error => {
          console.error("There was an error fetching session id:", error);
        });
      } else {
        axios.get('/projects/', {
          headers: {
            'dac-sess_id': sessionStorage.getItem('sess_id')
          }
        }).then(response => {

        }).catch(error => {
          console.error("There was an error starting project:", error);
        });
      }
      this.start_dialog = false;
    }
  }
}
</script>

<style>
/* Add global styles here */
</style>