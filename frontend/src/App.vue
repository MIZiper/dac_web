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
            <ObjectBrowser style="width: 49%;" />
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
import YamlEditor from './components/YamlEditor.vue';
import MainContent from './components/MainContent.vue';
import MessageZone from './components/MessageZone.vue';

export default {
  components: {
    ObjectBrowser,
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
      this.start_dialog = false;
    }
  }
}
</script>

<style>
/* Add global styles here */
</style>
