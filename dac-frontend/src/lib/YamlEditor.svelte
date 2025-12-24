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
        value,
        onSave,
        onFire,
    }: { value: string; onSave: () => void; onFire: () => void } = $props();
</script>

<Card>
    <CardHeader>
        <Row>
            <Col>
                <CardTitle>YAML Editor</CardTitle>
            </Col>
            <Col xs="auto" class="pe-1">
                <Button>Save</Button>
            </Col>
            <Col xs="auto" class="ps-1">
                <Button>Save & Run</Button>
            </Col>
        </Row>
    </CardHeader>
    <CardBody class="p-0">
        <CodeMirror bind:value lang={yaml()} />
    </CardBody>
</Card>
