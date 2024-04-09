<template>
    <v-card>
        <v-row class="ma-0">
            <v-card-title>Action</v-card-title>
            <v-spacer></v-spacer>
            <v-menu>
                <template v-slot:activator="{ props }">
                    <v-btn variant="text" v-bind="props" title="Add action">
                        <v-icon>mdi-plus-circle</v-icon>
                    </v-btn>
                </template>
                <v-list>
                    <v-list-item v-for="act_cls in action_types" :key="act_cls.type" @click="addAction(act_cls.type)">
                        <v-list-item-title>{{ act_cls.name }}</v-list-item-title>
                    </v-list-item>
                </v-list>
            </v-menu>
        </v-row>
        <v-card-text>
            <v-list density="compact">
                <v-list-item v-for="act_itm in actions" :key="act_itm.uuid">
                    <v-list-item-title><v-icon>mdi-folder</v-icon> {{ act_itm.name }}</v-list-item-title>
                </v-list-item>
            </v-list>
        </v-card-text>
    </v-card>
</template>

<script>
import { ax_base, ax_project } from '@/utils';

export default {
    data() {
        return {
            actions: [
                { name: 'Context 1', uuid: 'uuid1' }
            ],
            action_types: [
                { name: 'Context Type 1', type: 'path/to/context1' }
            ],
        };
    },
    mounted() {
        this.emitter.on('action-refresh-request', this.handleActionRequest);
        this.emitter.on('action_type-refresh-request', this.handleActionTypeRequest);
    },
    methods: {
        handleActionRequest() {

        },
        handleActionTypeRequest() {
            ax_project.get('types/action').then(response => {
                this.action_types = response.data['action_types'];
            }).catch(error => {
                console.error("There was an error fetching action type list:", error);
            });
        },
    }
}
</script>

<style scoped>
/* Add component-specific styles here */
</style>