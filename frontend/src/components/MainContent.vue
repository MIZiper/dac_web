<template>
    <v-card :class="{ 'fullscreen-component': isFullscreen }">
        <v-row class="ma-0">
            <v-card-title>Main Content</v-card-title>
            <v-spacer></v-spacer>
            <v-btn variant="text" title="Toggle fullscreen" @click="toggleFullscreen">
                <v-icon>{{ isFullscreen ? 'mdi-fullscreen-exit' : 'mdi-fullscreen' }}</v-icon>
            </v-btn>
        </v-row>
        <v-card-text class="pt-0">
            <v-img src="https://via.placeholder.com/800x600" contain></v-img>
        </v-card-text>
    </v-card>
</template>

<script>
export default {
    data() {
        return {
            isFullscreen: false,
        };
    },
    methods: {
        toggleFullscreen() {
            /*
            // https://stackoverflow.com/a/59499501
            var doc = window.document;
            var docEl = doc.documentElement;

            // Request full screen
            var requestFullScreen = docEl.requestFullscreen || docEl.mozRequestFullScreen || docEl.webkitRequestFullScreen || docEl.msRequestFullscreen;

            // Exit full screen
            var cancelFullScreen = doc.exitFullscreen || doc.mozCancelFullScreen || doc.webkitExitFullscreen || doc.msExitFullscreen;
            if (!doc.fullscreenElement && !doc.mozFullScreenElement && !doc.webkitFullscreenElement && !doc.msFullscreenElement) {
                requestFullScreen.call(docEl);
            }
            else {
                cancelFullScreen.call(doc);
            }
            */
            this.isFullscreen = !this.isFullscreen;
        },
    }
}
</script>

<style scoped>
.fullscreen-component {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 9999;
}
</style>