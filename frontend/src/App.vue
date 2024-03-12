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
          <ObjectBrowser class="mb-4" />
          <YamlEditor />
        </v-col>
        <v-col cols="8">
          <MainContent class="mb-4"/>
          <MessageZone />
        </v-col>
      </v-row>
    </v-container>
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
      title: "DAC analysis frame"
    }
  }
}
</script>

<style>
/* Add global styles here */
</style>
