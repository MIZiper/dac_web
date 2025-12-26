<script lang="ts">
    import { yaml } from "@codemirror/lang-yaml";
    import {
        Button,
        Card,
        CardBody,
        CardFooter,
        CardHeader,
        CardTitle,
        Col,
        Row,
    } from "@sveltestrap/sveltestrap";
    import CodeMirror from "svelte-codemirror-editor";

    let {
        value = $bindable(),
        onSave,
        onFire,
        boundNode,
    }: {
        value: string;
        onSave: () => void;
        onFire: () => void;
        boundNode: any;
    } = $props();
</script>

<Card>
    <CardHeader>
        <Row>
            <Col>
                <CardTitle>YAML Editor</CardTitle>
            </Col>
            <Col xs="auto" class="pe-1">
                <Button disabled={!boundNode} onclick={onSave}>Save</Button>
            </Col>
            <Col xs="auto" class="ps-1">
                <Button
                    disabled={!boundNode || !("status" in boundNode)}
                    onclick={onFire}>Save & Run</Button
                >
            </Col>
        </Row>
    </CardHeader>
    <CardBody class="p-0">
        <CodeMirror bind:value lang={yaml()} />
    </CardBody>
</Card>
