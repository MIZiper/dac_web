<template>
    <v-card variant="flat" :class="{ 'fullscreen-component': isFullscreen }">
        <v-fab v-if="figure" location="top right" absolute variant="text" title="Toggle fullscreen"
            @click="toggleFullscreen">
            <v-icon>{{ isFullscreen ? 'mdi-fullscreen-exit' : 'mdi-fullscreen' }}</v-icon>
        </v-fab>
        <v-fab v-if="!isFullscreen && figure" location="top left" absolute variant="text" title="Auto resize"
            @click="autoScaleCanvas">
            <v-icon>mdi-refresh-auto</v-icon>
        </v-fab>
        <div id="figure">
            <img v-if="!figure" src="https://placehold.co/1000x600?text=Loading+matplotlib" />
        </div>
    </v-card>
</template>

<script>
import { mpl_urn, FIG_NUM, SESSID_KEY } from '@/utils';
import { VFab } from 'vuetify/labs/VFab';

export default {
    components: {
        VFab,
    },
    data() {
        return {
            isFullscreen: false,
            figure: null,
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
            this.autoScaleCanvas();
        },
        autoScaleCanvas() {
            if (!this.figure) return;
            
            if (this.isFullscreen) {
                this.figure._resize_canvas(window.innerWidth, window.innerHeight * 0.9, true);
            } else {
                this.figure._resize_canvas(window.innerWidth * 0.66, window.innerHeight * 0.7, true);
            }
        },
        initMpl(sess_id) {
            let query_str = `${SESSID_KEY}=${sess_id}`;

            ['mpl.css'].forEach(function (name) { // ['page.css', 'boilerplate.css', 'fbm.css', ]
                let link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = `${mpl_urn}/_static/css/${name}?${query_str}`;
                document.head.appendChild(link);
            });

            function ondownload(figure, format) {
                window.open(`${mpl_urn}/${figure.id}/download.${format}?${query_str}`, '_blank');
            };

            let script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = `${mpl_urn}/js/mpl.js?${query_str}`;
            script.onload = () => {
                var websocket_type = mpl.get_websocket_type();
                var websocket = new websocket_type(`${mpl_urn}/${FIG_NUM}/ws?${query_str}`);

                var fig = new mpl.figure(FIG_NUM, websocket, ondownload, document.getElementById("figure"));
                this.figure = fig;

                // the mpl.figure() create toolbar but not link to server resources
                const widgetImages = document.querySelectorAll("button.mpl-widget img");
                widgetImages.forEach((img) => {
                    var fname = img.src.split("/").pop();
                    var fname_2x = img.srcset.split("/").pop();
                    img.src = `${mpl_urn}/_images/${fname}?${query_str}`;
                    img.srcset = `${mpl_urn}/_images/${fname_2x}?${query_str}`;
                });
            };
            document.body.appendChild(script);
            window.addEventListener('resize', this.autoScaleCanvas);
        },
    },
    mounted() {
        this.emitter.on('mpl-init-request', this.initMpl);
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