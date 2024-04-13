<template>
    <v-card>
        <v-row class="ma-0">
            <v-card-title>Context</v-card-title>
            <v-spacer></v-spacer>
            <v-menu>
                <template v-slot:activator="{ props }">
                    <v-btn variant="text" v-bind="props" title="Current context">
                        <v-icon>mdi-dots-horizontal-circle</v-icon>
                    </v-btn>
                </template>
                <v-list density="compact">
                    <v-list-item v-if="current_context !== GCK_ID" @click="editContext(current_context)">
                        <v-list-item-title>Edit</v-list-item-title>
                    </v-list-item>
                    <v-list-item disabled @click="runContext(current_context)">
                        <v-list-item-title>Run all</v-list-item-title>
                    </v-list-item>
                    <v-divider></v-divider>
                    <v-list-item v-if="current_context !== GCK_ID" @click="deleteContext(current_context)">
                        <v-list-item-title>Delete</v-list-item-title>
                    </v-list-item>
                </v-list>
            </v-menu>
            <v-menu>
                <template v-slot:activator="{ props }">
                    <v-btn variant="text" v-bind="props" title="Add context">
                        <v-icon>mdi-plus-circle</v-icon>
                    </v-btn>
                </template>
                <v-list density="compact">
                    <template v-for="ctx_cls in context_types" :key="ctx_cls.type">
                        <v-list-subheader v-if="typeof ctx_cls === 'string'">{{ ctx_cls }}</v-list-subheader>
                        <v-list-item v-else @click="addContext(ctx_cls.type)">
                            <v-list-item-title>{{ ctx_cls.name }}</v-list-item-title>
                        </v-list-item>
                    </template>
                </v-list>
            </v-menu>
        </v-row>
        <v-card-text class="pb-0 pt-0">
            <v-select v-model="current_context" :item-props="itemProps" :items="context_keys" item-title="name" item-value="uuid"
                density="compact" label="Select a context" @update:model-value="handleContextChange"></v-select>
        </v-card-text>
    </v-card>
</template>

<script>
import { ax_base, ax_project } from '@/utils';
const GCK_ID = 'global';
const DEFAULT_NAME = '[New Context]';

export default {
    data() {
        return {
            current_context: null,
            context_keys: [
                { name: 'Context 1', uuid: 'uuid1', type: 'mod.context_type_1' }
            ],
            context_types: [
                { name: 'Context Type 1', type: 'mod.context_type_1' }
            ],

            GCK_ID: GCK_ID,
        };
    },
    mounted() {
        this.emitter.on('context-refresh-request', this.handleContextRequest);
        this.emitter.on('context_type-refresh-request', this.handleContextTypeRequest);
    },
    methods: {
        itemProps(item) {
            return {
                'subtitle': item.type.split('.').pop(),
            };
        },
        handleContextRequest() {
            ax_project.get('contexts').then(response => {
                this.context_keys = response.data['contexts'];
                this.current_context = response.data['current_context'];

                this.emitter.emit('action-refresh-request', this.current_context);
                this.emitter.emit('data-refresh-request', this.current_context);
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
        handleContextChange(context_uuid) {
            ax_project.post('contexts/' + context_uuid, {}).then(response => {
                console.log(response.data['message']);

                this.emitter.emit('data-refresh-request', this.current_context);
                this.emitter.emit('action-refresh-request', this.current_context);
                this.emitter.emit('action_type-refresh-request');
            }).catch(error => {
                console.error("There was an error switching context:", error);
            });
        },
        addContext(context_type) {
            if (this.context_keys.find(
                context => (context.type === context_type) && (context.name === DEFAULT_NAME)
            )) {
                console.log("Context already exists");
                return;
            }

            ax_project.post('contexts', {
                context_config: {
                    type: context_type,
                    name: DEFAULT_NAME,
                }
            }).then(response => {
                console.log(response.data['message']);
                this.context_keys.push({
                    name: DEFAULT_NAME,
                    uuid: response.data['context_uuid'],
                    type: context_type,
                });
            }).catch(error => {
                console.error("There was an error adding context:", error);
            });
        },
        updateContext(node, fire=false, context_uuid) {
            ax_project.put('contexts/' + context_uuid, {
                context_config: node
            }).then(response => {
                this.context_keys = this.context_keys.map(context => {
                    if (context.uuid === context_uuid) {
                        context.name = node.name;
                    }
                    return context;
                });
            }).catch(error => {
                console.error("There was an error updating context:", error);
            });
        },
        editContext() {
            ax_project.get('contexts/' + this.current_context).then(response => {
                this.emitter.emit('edit-node', [response.data['context_config'], function(context_uuid, callback){
                    return (node, fire) => {
                        callback(node, fire, context_uuid);
                    }
                }(this.current_context, this.updateContext)]);
            }).catch(error => {
                console.error("There was an error fetching context:", error);
            });
        },
        runContext() {
        },
        deleteContext() {
            ax_project.delete('contexts/' + this.current_context).then(response => {
                console.log(response.data['message']);
                this.context_keys = this.context_keys.filter(context => context.uuid !== this.current_context);
                this.current_context = GCK_ID;
                
                this.emitter.emit('action-refresh-request', this.current_context);
                this.emitter.emit('data-refresh-request', this.current_context);
            }).catch(error => {
                console.error("There was an error deleting context:", error);
           });
        }
    }
}
</script>

<style scoped>
/* Add component-specific styles here */
</style>