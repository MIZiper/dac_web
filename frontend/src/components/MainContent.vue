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
            <div id="figure"></div>
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

<!--

      /* This is a callback that is called when the user saves
         (downloads) a file.  Its purpose is really to map from a
         figure and file format to a url in the application. */
         function ondownload(figure, format) {
        window.open('download.' + format, '_blank');
      };

      function ready(fn) {
        if (document.readyState != "loading") {
          fn();
        } else {
          document.addEventListener("DOMContentLoaded", fn);
        }
      }

      ready(
        function() {
          /* It is up to the application to provide a websocket that the figure
             will use to communicate to the server.  This websocket object can
             also be a "fake" websocket that underneath multiplexes messages
             from multiple figures, if necessary. */
          var websocket_type = mpl.get_websocket_type();
          var websocket = new websocket_type("%(ws_uri)sws");

          // mpl.figure creates a new figure on the webpage.
          var fig = new mpl.figure(
              // A unique numeric identifier for the figure
              %(fig_id)s,
              // A websocket object (or something that behaves like one)
              websocket,
              // A function called when a file type is selected for download
              ondownload,
              // The HTML element in which to place the figure
              document.getElementById("figure"));
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