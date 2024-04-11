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
                <v-list density="compact">
                    <template v-for="act_cls in action_types" :key="act_cls.type">
                        <template v-if="typeof act_cls === 'string'">
                            <v-list-subheader v-if="act_cls !== '[<]'">{{ act_cls }}</v-list-subheader>
                        </template>
                        <v-list-item v-else @click="addAction(act_cls.type)">
                        <v-list-item-title>{{ act_cls.name }}</v-list-item-title>
                    </v-list-item>
                    </template>
                </v-list>
            </v-menu>
        </v-row>
        <v-card-text class="pt-0 pl-2 pr-0">
            <v-list density="compact">
                <v-list-item v-for="act_itm in actions" :key="act_itm.uuid">
                    <v-list-item-title @click="editAction(act_itm.uuid)">
                        <v-icon>
                            <template v-if="act_itm.status === 0">
                                mdi-file-plus-outline
                            </template>
                            <template v-else-if="act_itm.status === 1">
                                mdi-file-edit-outline
                            </template>
                            <template v-else-if="act_itm.status === 2">
                                mdi-file-check-outline
                            </template>
                            <template v-else>
                                mdi-file-remove-outline
                            </template>
                        </v-icon>
                        {{ act_itm.name }}
                    </v-list-item-title>
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
                { name: 'Action 1', uuid: 'uuid1', status: 0 }
            ],
            action_types: [
                { name: 'Action Type 1', type: 'action.type.1' }
            ],
        };
    },
    mounted() {
        this.emitter.on('action-refresh-request', this.handleActionRequest);
        this.emitter.on('action_type-refresh-request', this.handleActionTypeRequest);
    },
    methods: {
        handleActionRequest(context_uuid) {
            ax_project.get(context_uuid + '/actions').then(response => {
                this.actions = response.data['actions'];
            }).catch(error => {
                console.error("There was an error fetching action list:", error);
            });
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