<script lang="ts">
    import { Icon } from "@sveltestrap/sveltestrap";
    import { onMount } from "svelte";
    import {
        api_mpl,
        app_mpl,
        FIG_NUM,
        SESSID_KEY,
    } from "../utils/FetchObjects";
    import { scale } from "svelte/transition";

    // const api_mpl = `/mpl`; // for dev
    // const app_mpl = `/mpl`; // for dev

    let { sess_id = "" } = $props();

    let figure: any = $state();
    let isFullscreen: boolean = $state(false);

    function initMpl() {
        const query_str = `${SESSID_KEY}=${sess_id}`;

        ["mpl.css"].forEach((file) => {
            const link = document.createElement("link");
            link.rel = "stylesheet";
            link.href = `${api_mpl}/_static/css/${file}`;
            document.head.appendChild(link);
        });

        function ondownload(figure, format) {
            window.open(
                `${app_mpl}/${figure.id}/download.${format}?${query_str}`,
                "_blank",
            );
        }

        const script = document.createElement("script");
        script.src = `${api_mpl}/js/mpl.js`;
        script.onload = () => {
            let websocket_type = window.mpl.get_websocket_type();
            let websocket = new websocket_type(
                `${app_mpl}/${FIG_NUM}/ws?${query_str}`,
            );

            figure = new window.mpl.figure(
                FIG_NUM,
                websocket,
                ondownload,
                document.getElementById("figure"),
            );
            const widgetImages = document.querySelectorAll(
                "button.mpl-widget img",
            );
            widgetImages.forEach((img) => {
                const fname = img.src.split("/").pop();
                const fname_2x = img.srcset.split("/").pop();
                img.src = `${api_mpl}/_images/${fname}`;
                img.srcset = `${api_mpl}/_images/${fname_2x}`;
            });
        };
        document.body.appendChild(script);
        window.addEventListener("resize", autoScaleCanvas);
    }
    function autoScaleCanvas() {
        if (!figure) return;

        if (isFullscreen) {
            figure._resize_canvas(
                window.innerWidth,
                window.innerHeight * 0.9,
                true,
            );
        } else {
            figure._resize_canvas(
                window.innerWidth * 0.66,
                window.innerHeight * 0.7,
                true,
            );
        }
    }
    function toggleFullscreen() {
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
        isFullscreen = !isFullscreen;
        autoScaleCanvas();
    }

    $effect(() => {
        if (sess_id !== "") {
            initMpl();
        }
    });
</script>

<div id="mpl-container" class={isFullscreen ? "fullscreen-component" : ""}>
    {#if figure}
        <div id="fullscreen-btn">
            <Icon
                onclick={toggleFullscreen}
                name={isFullscreen ? "fullscreen-exit" : "arrows-fullscreen"}
                title="Toggle fullscreen"
            />
        </div>
    {/if}
    {#if !isFullscreen && figure}
        <div id="autoscale-btn">
            <Icon
                onclick={autoScaleCanvas}
                name="arrow-clockwise"
                title="Auto resize"
            />
        </div>
    {/if}
    <div id="figure"></div>
    {#if !figure}
        <img out:scale={{duration: 500}}
            src="https://placehold.co/1000x600?text=Loading+matplotlib"
            alt="Mpl placeholder"
        />
    {/if}
</div>

<style>
    #mpl-container {
        position: relative;
        /* min-width: 1000px; */
    }
    #fullscreen-btn {
        position: absolute;
        top: 4px;
        right: 8px;
    }
    #autoscale-btn {
        position: absolute;
        top: 4px;
        left: 8px;
    }
    #fullscreen-btn:hover,
    #autoscale-btn:hover {
        color: orange;
        cursor: pointer;
    }
    #mpl-container.fullscreen-component {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        z-index: 9999;
    }
</style>
