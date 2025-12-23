<script lang="ts">
    import { Col, Progress, Row } from "@sveltestrap/sveltestrap";
    import ContextList from "../lib/ContextList.svelte";
    import DataList from "../lib/DataList.svelte";
    import ActionList from "../lib/ActionList.svelte";
    import YamlEditor from "../lib/YamlEditor.svelte";
    import MplCanvas from "../lib/MplCanvas.svelte";
    import ScenarioList from "../lib/ScenarioList.svelte";

    import { navTeleport } from "../utils/NavibarSnippet.svelte";
    import { route } from "../router";
    import { ax_api, ax_app, SESSID_KEY } from "../utils/FetchObjects";

    import {
        initAnalysis,
        stateObjectPasser,
        switchScenario,
    } from "./MainPageHandler.svelte";
    import type { DataItem, ScenarioItem } from "../schema";
    import { onMount } from "svelte";

    let {
        data,
        actions,
        contexts,
        scenarios,
        availableContextTypes,
        availableActionTypes,
    } = stateObjectPasser();

    let loading = $state(0);
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

    onMount(async () => {
        loading = 100;
        if (project_id === "new") {
            const res = await ax_api.post("/new");
            if (res.status == 200) {
                sess_id = res.data[SESSID_KEY];
                await initAnalysis(sess_id);
            }
        } else {
            const res = await ax_api.post("/load", { project_id: project_id });
            if (res.status == 200) {
                sess_id = res.data[SESSID_KEY];
                await initAnalysis(sess_id);
            }
        }
        loading = 0;
    });
</script>

{#snippet contextMenuSnippet()}
    <ScenarioList {scenarios} bind:currentScenario />
{/snippet}

<Progress style="height:4px" value={loading} animated />

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
        <MplCanvas {sess_id} />
    </Col>
</Row>
