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
            <!--
            <v-img src="https://via.placeholder.com/800x600" contain></v-img>
            -->
            <div id="figure"></div>
        </v-card-text>
    </v-card>
</template>

<script>
import { mpl_urn, FIG_NUM } from '@/utils';

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
    },
    mounted() {
        ['page', 'boilerplate', 'fbm', 'mpl'].forEach(function (name) {
            let link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = "http://" + mpl_urn + '/_static/css/' + name + '.css';
            document.head.appendChild(link);
        });
        
        function ondownload(figure, format) {
            window.open("http://" + mpl_urn + "/" + figure.id + '/download.' + format, '_blank');
        };

        let script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = "http://" + mpl_urn + '/js/mpl.js';
        script.onload = () => {
            var websocket_type = mpl.get_websocket_type();
            var websocket = new websocket_type("ws://" + mpl_urn + "/" + FIG_NUM + "/ws");

            var fig = new mpl.figure(FIG_NUM, websocket, ondownload, document.getElementById("figure"));

            // the mpl.figure() create toolbar but not link to server resources
            const widgetImages = document.querySelectorAll("button.mpl-widget img");
            widgetImages.forEach((img) => {
                var fname = img.src.split("/").pop();
                img.src = "http://" + mpl_urn + "/_images/" + fname;
            });
        };
        document.body.appendChild(script);
    },
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