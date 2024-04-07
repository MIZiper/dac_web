<template>
    <v-card>
        <v-row class="ma-0">
            <v-card-title>YAML Editor</v-card-title>
            <v-spacer></v-spacer>

            <v-btn variant="text" title="Save config">
                <v-icon>mdi-check-circle</v-icon>
            </v-btn>
            <v-btn variant="text" title="Save and run">
                <v-icon>mdi-fire-circle</v-icon>
            </v-btn>
        </v-row>
        <v-card-text>
            <v-textarea v-model="yamlCode" rows="10"></v-textarea>
        </v-card-text>
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