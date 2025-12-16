<script lang="ts">
    import { yaml } from "@codemirror/lang-yaml";
    import CodeMirror from "svelte-codemirror-editor";

    let value = "";
</script>

<CodeMirror bind:value lang={yaml()} />