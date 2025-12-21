<div id="figure">

</div>

<script lang="ts">
    let {mplSite} = $props();

    let figure: any;

    function initMpl() {
        ['mpl.css'].forEach((file) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = `${mplSite}/static/css/${file}`;
            document.head.appendChild(link);
        });

        function ondownload(figure, format) {
            window.open(`${mplSite}/${figure.id}/download.${format}`, '_blank');
        };

        const script = document.createElement('script');
        script.src = `${mplSite}/static/js/mpl.js`;
        script.onload = () => {
            // @ts-ignore
            window.mpl.figure(figure);
        };
        document.body.appendChild(script);
    }

</script>

<style>
    #figure {
        min-height: 600px;
        min-width: 960px;
    }
</style>