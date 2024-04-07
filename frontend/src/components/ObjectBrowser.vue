<template>
    <v-card>
        <v-card-title>Data Browser</v-card-title>
        <v-card-text>
            <v-list density="compact">
                <v-list-item v-for="(item, index) in data_items" :key="index">
                    <v-list-item-title>{{ item[0] }}</v-list-item-title>
                </v-list-item>
            </v-list>
        </v-card-text>
    </v-card>
</template>

<script>
import {ax_base, ax_project} from '@/utils';

export default {
    data() {
        return {
            data_items: [
                ["Title 1", "Type 1"],
                ["Title 2", "Type 2"],
            ],
        }
    },
    mounted() {
        this.emitter.on('data-refresh-request', this.handleDataRequest);
    },
    methods: {
        handleDataRequest() {
            ax_project.get('types/data').then(response => {
                this.data_items = response.data['data'];
            }).catch(error => {
                console.error("There was an error fetching object list:", error);
            });
        }
    }
}
</script>

<style scoped>
/* Add component-specific styles here */
</style>