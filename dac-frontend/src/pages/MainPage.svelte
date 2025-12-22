<script lang="ts">
    import { Col, Row } from "@sveltestrap/sveltestrap";
    import ContextList from "../lib/ContextList.svelte";
    import DataList from "../lib/DataList.svelte";
    import ActionList from "../lib/ActionList.svelte";
    import YamlEditor from "../lib/YamlEditor.svelte";
    import MplCanvas from "../lib/MplCanvas.svelte";
    import ScenarioList from "../lib/ScenarioList.svelte";

    import { navTeleport } from "../utils/NavibarSnippet.svelte";
    import { route } from "../router";
    route.getParams("/projects/:id");
    const project_id = route.params.id;

    let yaml_code: string = $state("");
    function saveYamlHandler() {}
    function fireYamlHandler() {}

    $effect(() => {
        navTeleport.snippet = contextMenuSnippet;

        return () => {
            navTeleport.snippet = null;
        };
    });
</script>

{#snippet contextMenuSnippet()}
    <ScenarioList />
{/snippet}

<Row>
    <Col>
        <ContextList />
        <Row>
            <Col>
                <DataList />
            </Col>
            <Col>
                <ActionList />
            </Col>
        </Row>
        <YamlEditor
            value={yaml_code}
            onSave={saveYamlHandler}
            onFire={fireYamlHandler}
        />
    </Col>
    <Col xs="auto">
        <MplCanvas mplSite="" />
    </Col>
</Row>
