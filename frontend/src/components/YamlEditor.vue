<template>
    <v-card>
        <v-card-title>YAML Editor</v-card-title>
        <v-card-text>
            <v-textarea v-model="yamlCode" rows="10"></v-textarea>
        </v-card-text>
      <v-btn icon>
        <v-icon>mdi-account-circle</v-icon>
      </v-btn>
    </v-card>
</template>

<script>
export default {
    data() {
        return {
            yamlCode: 'sample: YAML\nkey: value'
        }
    }
}
</script>

<style scoped>
/* Add component-specific styles here */
</style>