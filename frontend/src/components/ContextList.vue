<template>
    <v-card>
        <v-row class="ma-0">
            <v-card-title>Context</v-card-title>
            <v-spacer></v-spacer>
            <v-menu>
                <template v-slot:activator="{ props }">
                    <v-btn variant="text" v-bind="props" title="Add context">
                        <v-icon>mdi-plus-circle</v-icon>
                    </v-btn>
                </template>
                <v-list>
                    <v-list-item v-for="ctx_cls in context_types" :key="ctx_cls.type" @click="addContext(ctx_cls.type)">
                        <v-list-item-title>{{ ctx_cls.name }}</v-list-item-title>
                    </v-list-item>
                </v-list>
            </v-menu>
        </v-row>
        <v-card-text class="pb-0 pt-0">
            <v-select v-model="current_context" :items="context_keys" item-title="name" item-value="uuid"
                density="compact" label="Select a context"></v-select>
        </v-card-text>
    </v-card>
</template>

<script>
import { ax_base, ax_project } from '@/utils';

export default {
    data() {
        return {
            current_context: null,
            context_keys: [
                { name: 'Context 1', uuid: 'uuid1' }
            ],
            context_types: [
                { name: 'Context Type 1', type: 'context.type.1' }
            ],
        };
    },
    mounted() {
        this.emitter.on('context-refresh-request', this.handleContextRequest);
        this.emitter.on('context_type-refresh-request', this.handleContextTypeRequest);
    },
    methods: {
        handleContextRequest() {
            ax_project.get('contexts').then(response => {
                this.context_keys = response.data['contexts'];
            }).catch(error => {
                console.error("There was an error fetching context key list:", error);
            });
        },
        handleContextTypeRequest() {
            ax_project.get('types/context').then(response => {
                this.context_types = response.data['context_types'];
            }).catch(error => {
                console.error("There was an error fetching context type list:", error);
            });
        },
    }
}
</script>

<style scoped>
/* Add component-specific styles here */
</style>