<template>
    <v-card>
        <v-card-title>Object Browser</v-card-title>
        <v-card-text>
            <v-list dense>
                <v-list-item v-for="(item, index) in objectList" :key="index">
                    <v-list-item-icon>
                        <v-icon>mdi-folder</v-icon>
                    </v-list-item-icon>
                    <v-list-item-content>
                        <v-list-item-title>{{ item }}</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
            </v-list>
        </v-card-text>
    </v-card>
</template>

<script>
export default {
    data() {
        return {
            objectList: ['Object 1', 'Object 2', 'Object 3'],
        }
    }
}
</script>

<style scoped>
/* Add component-specific styles here */
</style>