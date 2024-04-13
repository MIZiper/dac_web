<template>
    <v-card>
        <v-row class="ma-0">
            <v-card-title>YAML Editor</v-card-title>
            <v-spacer></v-spacer>

            <v-btn :disabled="!editCallback" @click="saveNode" variant="text" title="Save config">
                <v-icon>mdi-check-circle</v-icon>
            </v-btn>
            <v-btn :disabled="!editCallback" @click="fireNode" variant="text" title="Save and run">
                <v-icon>mdi-fire-circle</v-icon>
            </v-btn>
        </v-row>
        <v-card-text class="pt-0">
            <v-textarea v-model="yamlCode" rows="7" auto-grow style="font-family: 'Consolas', 'Courier New', Courier, monospace;"></v-textarea>
        </v-card-text>
    </v-card>
</template>

<script>
import YAML from 'yaml';

export default {
    mounted() {
        this.emitter.on('edit-node', eventPair => {
            this.editCallback = eventPair[1];
            this.yamlCode = YAML.stringify(eventPair[0]);
        });
    },
    data() {
        return {
            yamlCode: 'sample: YAML\nkey: value',
            editCallback: null,
        }
    },
    methods: {
        saveNode() {
            this.editCallback(YAML.parse(this.yamlCode), false);
        },
        fireNode() {
            this.editCallback(YAML.parse(this.yamlCode), true);
        }
    },
}
</script>

<style scoped>
/* Add component-specific styles here */
</style>