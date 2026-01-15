<script lang="ts">
    import { Col, Progress, Row } from "@sveltestrap/sveltestrap";
    import ContextList from "../lib/ContextList.svelte";
    import DataList from "../lib/DataList.svelte";
    import ActionList from "../lib/ActionList.svelte";
    import YamlEditor from "../lib/YamlEditor.svelte";
    import MplCanvas from "../lib/MplCanvas.svelte";
    import ScenarioList from "../lib/ScenarioList.svelte";

    import { navTeleport } from "../utils/NavibarSnippet.svelte";
    import { ax_api, ax_app, GCK_ID, SESSID_KEY } from "../utils/FetchObjects";

    import {
        initAnalysis,
        appdata,
        switchScenario,
        switchContext,
        getActionConfig,
        runAction,
        deleteAction,
        addAction,
        updateAction,
        updateContext,
        deleteContext,
        getContextConfig,
        getCurrentData,
        getCurrentActions,
        addContext,
    } from "./MainPageHandler.svelte";
    import { getContext, onMount } from "svelte";
    import YAML from "yaml";
    import type { ActionItem, DataItem } from "../schema";
    import { taskHolder } from "../tasks/TaskRouter.svelte";

    let loading = $state(0);
    const route = getContext("route");
    route.getParams("/projects/:id");
    const project_id = route.params.id;

    let config_in = $state({});
    let onTaskDone: ((c: Record<string, any> | null) => void) | null =
        $state(null);

    let yaml_code: string = $state("");
    let yamled_node: ActionItem | DataItem | null = $state(null);
    async function saveYamlHandler() {
        let conf = YAML.parse(yaml_code);
        if (yamled_node && appdata.currentContext) {
            if ("status" in yamled_node) {
                await updateAction(appdata.currentContext, yamled_node, conf);
            } else {
                await updateContext(yamled_node, conf);
            }
        }
    }
    async function fireYamlHandler() {
        await saveYamlHandler();
        if (appdata.currentContext && yamled_node && "status" in yamled_node)
            await runAction(appdata.currentContext, yamled_node);
    }

    let sess_id = $state("");

    $effect(() => {
        navTeleport.snippet = contextMenuSnippet;

        return () => {
            navTeleport.snippet = null;
        };
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
    <ScenarioList
        scenarios={appdata.scenarios}
        currentScenario={appdata.currentScenario}
        onSwitchScenario={(s) => switchScenario(s).then(() => {})}
    />
{/snippet}

<Progress style="height:4px" value={loading} animated />

<Row class="mt-1">
    <Col class="pe-1">
        <ContextList
            contexts={appdata.contexts}
            availableContextTypes={appdata.availableContextTypes}
            currentContext={appdata.currentContext}
            onSwitchContext={(c) => switchContext(c).then(() => {})}
            onDeleteContext={(c) => {
                deleteContext(c).then(() => {
                    let gc = appdata.contexts.find((c) => c.uuid === GCK_ID);
                    if (gc) {
                        appdata.currentContext = gc;
                        getCurrentData(gc).then();
                        getCurrentActions(gc).then();
                    }
                    if (yamled_node && yamled_node.uuid === c.uuid) {
                        yamled_node = null;
                        yaml_code = "";
                    }
                });
            }}
            onEditContext={(c) => {
                getContextConfig(c).then((conf) => {
                    yaml_code = YAML.stringify(conf);
                    yamled_node = c;
                });
            }}
            onAddContextType={(t) => {
                const c = appdata.currentContext;
                appdata.currentContext = null; // the select value unexpectedly get reset to global, so force change here.
                addContext(t).then(() => {
                    appdata.currentContext = c;
                });
            }}
        />
        <Row class="my-1">
            <Col class="pe-1">
                <DataList data={appdata.data} />
            </Col>
            <Col class="ps-1">
                <ActionList
                    actions={appdata.actions}
                    availableActionTypes={appdata.availableActionTypes}
                    onEditAction={(a) => {
                        if (appdata.currentContext) {
                            getActionConfig(appdata.currentContext, a).then(
                                (conf) => {
                                    yaml_code = YAML.stringify(conf);
                                    yamled_node = a;
                                },
                            );
                        }
                    }}
                    onRunAction={(a) => {
                        if (appdata.currentContext) {
                            runAction(appdata.currentContext, a).then();
                        }
                    }}
                    onDeleteAction={(a) => {
                        if (appdata.currentContext) {
                            deleteAction(appdata.currentContext, a).then(() => {
                                if (
                                    yamled_node &&
                                    yamled_node.uuid === a.uuid
                                ) {
                                    yamled_node = null;
                                    yaml_code = "";
                                }
                            });
                        }
                    }}
                    onAddActionType={(t) => {
                        if (appdata.currentContext) {
                            addAction(appdata.currentContext, t).then(
                                (new_action) => {
                                    // below not working because `new_action` has no config returned
                                    // if (new_action) {
                                    //     yamled_node = new_action;
                                    //     yaml_code = YAML.stringify();
                                    // }
                                },
                            );
                        }
                    }}
                    onTaskAction={(a, c) => {
                        if (appdata.currentContext) {
                            getActionConfig(appdata.currentContext, a).then(
                                (conf) => {
                                    config_in = conf;
                                    taskHolder.currentComponent = c;

                                    onTaskDone = ((a_, conf_) => {
                                        return (config_out) => {
                                            if (config_out) {
                                                yaml_code = YAML.stringify({
                                                    ...conf_,
                                                    ...config_out,
                                                });
                                                yamled_node = a_;
                                            }
                                            taskHolder.currentComponent = null;
                                            config_in = {};
                                            onTaskDone = null;
                                        };
                                    })(a, conf);
                                },
                            );
                        }
                    }}
                />
            </Col>
        </Row>
        <YamlEditor
            bind:value={yaml_code}
            boundNode={yamled_node}
            onSave={saveYamlHandler}
            onFire={fireYamlHandler}
        />
    </Col>
    <Col xs="auto" class="ps-1">
        <MplCanvas {sess_id} />
    </Col>
</Row>

{#if taskHolder.currentComponent && onTaskDone}
    <taskHolder.currentComponent {config_in} {onTaskDone} />
{/if}
