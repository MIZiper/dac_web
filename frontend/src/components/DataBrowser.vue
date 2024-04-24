<template>
    <v-card>
        <v-card-title>Data</v-card-title>
        <v-card-text class="pt-0 pl-2 pr-0">
            <v-list density="compact">
                <v-list-item v-for="dt_itm in data_items" :key="dt_itm.uuid">
                    <v-list-item-title>{{ dt_itm.name }}</v-list-item-title>
                    <v-list-item-subtitle>{{ dt_itm.type.split('.').pop() }}</v-list-item-subtitle>
                </v-list-item>
            </v-list>
        </v-card-text>
    </v-card>
</template>

<script>
import { ax_router, ax_app } from '@/utils';

export default {
    data() {
        return {
            data_items: [
                { name: "Data 1", uuid: "uuid1", type: "mod.data_type_1" }
            ],
        }
    },
    mounted() {
        this.emitter.on('data-refresh-request', this.handleDataRequest);
    },
    methods: {
        handleDataRequest(context_uuid) {
            ax_app.get(`/${context_uuid}/data`).then(response => {
                this.data_items = response.data['data'];
            }).catch(error => {
                console.error("There was an error fetching data list:", error);
            });
        }
    }
}
</script>

<style scoped>
/* Add component-specific styles here */
</style>