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
                            <v-divider></v-divider>
                            <!-- TODO: make [>] as subgroup -->
                            <v-list-subheader v-if="act_cls !== '[<]'">{{ act_cls }}</v-list-subheader>
                        </template>
                        <v-list-item v-else @click="addAction(act_cls)">
                            <v-list-item-title>{{ act_cls.name }}</v-list-item-title>
                        </v-list-item>
                    </template>
                </v-list>
            </v-menu>
        </v-row>
        <v-card-text class="pt-0 pl-2 pr-0">
            <v-list density="compact">
                <v-list-item v-for="act_itm in actions" @click="showContextMenu($event, act_itm.uuid)"
                    :key="act_itm.uuid">
                    <v-list-item-title :title="act_itm.name">
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
            <v-menu v-model="showMenu" :target="menuXY">
                <v-list density="compact">
                    <v-list-item @click="editAction"><v-list-item-title>Edit</v-list-item-title></v-list-item>
                    <v-list-item @click="runAction"><v-list-item-title>Run</v-list-item-title></v-list-item>
                    <v-divider></v-divider>
                    <v-list-item @click="deleteAction"><v-list-item-title>Delete</v-list-item-title></v-list-item>
                </v-list>
            </v-menu>
        </v-card-text>
    </v-card>
</template>

<script>
import { ax_api, ax_app } from '@/utils';

export default {
    data() {
        return {
            actions: [
                { name: 'Action 1', uuid: 'uuid1', status: 0 }
            ],
            action_types: [
                { name: 'Action Type 1', type: 'action.type.1' }
            ],

            selectedItemUUID: null,
            showMenu: false,
            menuXY: [0, 0],
            current_context: null,
        };
    },
    mounted() {
        this.emitter.on('action-refresh-request', this.handleActionRequest);
        this.emitter.on('action_type-refresh-request', this.handleActionTypeRequest);
    },
    methods: {
        handleActionRequest(context_uuid) {
            ax_app.get(`/${context_uuid}/actions`).then(response => {
                this.actions = response.data['actions'];
                this.current_context = context_uuid;
            }).catch(error => {
                console.error("There was an error fetching action list:", error);
            });
        },
        handleActionTypeRequest() {
            ax_app.get('/types/action').then(response => {
                this.action_types = response.data['action_types'];
            }).catch(error => {
                console.error("There was an error fetching action type list:", error);
            });
        },
        addAction(action_type) {
            ax_app.post(`/${this.current_context}/actions`, {
                action_config: {
                    type: action_type.type,
                    name: action_type.name, // this is actually ignored
                }
            }).then(response => {
                console.log(response.data['message']);
                this.actions.push({
                    name: action_type.name,
                    uuid: response.data['action_uuid'],
                    status: 0,
                });
            }).catch(error => {
                console.error("There was an error adding action:", error);
            });
        },
        updateAction(node, fire=false, context_uuid, action_uuid) {
            ax_app.put(`/${context_uuid}/actions/${action_uuid}`, {
                action_config: node
            }).then(response => {
                this.actions = this.actions.map(action => { // this seems make closure unnecessary
                    if (action.uuid === action_uuid) {
                        action.name = node.name;
                        action.status = 1;
                    }
                    return action;
                });
            }).catch(error => {
                console.error("There was an error updating action:", error);
            });
        },
        editAction() {
            ax_app.get(`/${this.current_context}/actions/${this.selectedItemUUID}`).then(response => {
                this.emitter.emit('edit-node', [response.data['action_config'], function(context_uuid, action_uuid, callback){
                    return (node, fire) => {
                        callback(node, fire, context_uuid, action_uuid);
                    }
                }(this.current_context, this.selectedItemUUID, this.updateAction)]);
            }).catch(error => {
                console.error("There was an error fetching action:", error);
            });
        },
        runAction() {
            ax_app.post(`/${this.current_context}/actions/${this.selectedItemUUID}`).then(response => {
                console.log(response.data['message']);
                if (response.data['data_updated']) {
                    this.emitter.emit('data-refresh-request', this.current_context);
                }
                this.actions = this.actions.map(action => {
                    if (action.uuid === this.selectedItemUUID) {
                        action.status = response.data['status'];
                    }
                    return action;
                });
                if (response.data['stats']) {
                    this.emitter.emit('show-stats-request', response.data['stats']);
                }
            }).catch(error => {
                console.error("There was an error running action:", error);
            });
        },
        deleteAction() {
            ax_app.delete(`/${this.current_context}/actions/${this.selectedItemUUID}`).then(response => {
                console.log(response.data['message']);
                this.actions = this.actions.filter(action => action.uuid !== this.selectedItemUUID);
            }).catch(error => {
                console.error("There was an error deleting action:", error);
            });
        },
        showContextMenu(event, action_uuid) {
            this.menuXY = [event.clientX, event.clientY];
            this.showMenu = true;
            this.selectedItemUUID = action_uuid;
        },
    }
}
</script>

<style scoped>
/* Add component-specific styles here */
</style>