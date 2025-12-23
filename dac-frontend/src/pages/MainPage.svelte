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

    import {
        data,
        actions,
        contexts,
        scenarios,
        availableContextTypes,
        availableActionTypes,
        switchScenario,
    } from "./MainPageHandler.svelte";
    import type { DataItem, ScenarioItem } from "../schema";

    route.getParams("/projects/:id");
    const project_id = route.params.id;

    let yaml_code: string = $state("");
    function saveYamlHandler() {}
    function fireYamlHandler() {}

    let sess_id = $state("");
    let currentContext: DataItem | null = $state(null);
    let currentScenario: ScenarioItem | null = $state(null);

    $effect(() => {
        navTeleport.snippet = contextMenuSnippet;

        return () => {
            navTeleport.snippet = null;
        };
    });
    $effect(() => {
        if (currentScenario) {
            switchScenario(currentScenario).then(() => {});
        }
    });
</script>

{#snippet contextMenuSnippet()}
    <ScenarioList {scenarios} bind:currentScenario />
{/snippet}

<Row class="mt-1">
    <Col class="pe-1">
        <ContextList {contexts} {availableContextTypes} bind:currentContext />
        <Row class="my-1">
            <Col class="pe-1">
                <DataList {data} />
            </Col>
            <Col class="ps-1">
                <ActionList {actions} {availableActionTypes} />
            </Col>
        </Row>
        <YamlEditor
            value={yaml_code}
            onSave={saveYamlHandler}
            onFire={fireYamlHandler}
        />
    </Col>
    <Col xs="auto" class="ps-1">
        <MplCanvas mplSite="" />
    </Col>
</Row>
