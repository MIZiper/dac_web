<script lang="ts">
    import { yaml } from "@codemirror/lang-yaml";
    import {
        Button,
        Card,
        CardBody,
        CardFooter,
        CardHeader,
        CardTitle,
    } from "@sveltestrap/sveltestrap";
    import CodeMirror from "svelte-codemirror-editor";

    let {
        value,
        onSave,
        onFire,
    }: { value: string; onSave: () => void; onFire: () => void } = $props();
</script>

<Card>
    <CardHeader>
        <CardTitle>YAML Editor</CardTitle>
    </CardHeader>
    <CardBody>
        <CodeMirror bind:value lang={yaml()} />
    </CardBody>
    <CardFooter>
        <Button>Save</Button>
        <Button>Save & Run</Button>
    </CardFooter>
</Card>
