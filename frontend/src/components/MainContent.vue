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
import { mpl_ws, mpl_js } from '@/utils';
import { io } from 'socket.io-client';

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
        ['page', 'boilerplate', 'fbm', 'mpl'].forEach(function(name){
            let link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = mpl_js.replace('mpl.js', '_static/css/' + name + '.css');
            document.head.appendChild(link);
        });
        let script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = mpl_js;
        document.body.appendChild(script);
        script.onload = () => {

        /* It is up to the application to provide a websocket that the figure
            will use to communicate to the server.  This websocket object can
            also be a "fake" websocket that underneath multiplexes messages
            from multiple figures, if necessary. */
        
        var websocket = io(mpl_ws);

        // mpl.figure creates a new figure on the webpage.
        var fig = new mpl.figure(
            // A unique numeric identifier for the figure
            1,
            // A websocket object (or something that behaves like one)
            websocket,
            // A function called when a file type is selected for download
            ondownload,
            // The HTML element in which to place the figure
            document.getElementById("figure")
        );

        };
    },
}

/* This is a callback that is called when the user saves
    (downloads) a file.  Its purpose is really to map from a
    figure and file format to a url in the application. */
function ondownload(figure, format) {
    window.open('download.' + format, '_blank');
};

</script>

<!--

function ready(fn) {
    if (document.readyState != "loading") {
        fn();
    } else {
        document.addEventListener("DOMContentLoaded", fn);
    }
}

ready(
    function() {
    }
);
-->

<style scoped>
.fullscreen-component {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 9999;
}
</style>