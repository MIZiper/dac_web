<script lang="ts">
    import {
        Alert,
        Button,
        Col,
        Progress,
        Row,
        Toast,
    } from "@sveltestrap/sveltestrap";
    import ContextList from "../lib/ContextList.svelte";
    import DataList from "../lib/DataList.svelte";
    import ActionList from "../lib/ActionList.svelte";
    import YamlEditor from "../lib/YamlEditor.svelte";
    import MplCanvas from "../lib/MplCanvas.svelte";
    import ScenarioList from "../lib/ScenarioList.svelte";

    import { navTeleport } from "../utils/NavibarSnippet.svelte";
    import {
        app_prefix,
        ax_api,
        ax_app,
        GCK_ID,
        SESSID_KEY,
    } from "../utils/FetchObjects";

    import {
        initAnalysis,
        appdata,
        switchScenario,
        switchContext,
        getActionConfig,
        deleteAction,
        addAction,
        updateAction,
        updateContext,
        deleteContext,
        getContextConfig,
        getCurrentData,
        getCurrentActions,
        addContext,
        statusMap,
    } from "./MainPageHandler.svelte";
    import { getContext, onMount, onDestroy } from "svelte";
    import YAML from "yaml";
    import type { ActionItem, DataItem } from "../schema";
    import { taskHolder } from "../tasks/TaskRouter.svelte";
    import StatsTable from "../lib/StatsTable.svelte";
    import SaveProjectDropdown from "../lib/SaveProjectDropdown.svelte";
    import { keycloakService } from "../utils/KeycloakService.svelte";

    let loading = $state(0);
    let message = $state("");
    let toastIsOpen = $state(false);

    let tblRef: { set: (title: string, headers: Record<string, string[]>, data: (string | number)[][]) => void } | undefined = $state();

    const router = getContext<{ route: { getParams: (p: string) => void; params: { id: string } }; navigate: (p: string, opts?: any) => void }>("router");
    router.route.getParams("/projects/:id");
    let project_id = router.route.params.id;

    let config_in: Record<string, any> = $state({});
    let onTaskDone: ((c: Record<string, any> | null) => void) | null =
        $state(null);

    let yaml_code: string = $state("");
    let yamled_node: ActionItem | DataItem | null = $state(null);

    $effect(() => {
        if (appdata.errorMessage) {
            message = appdata.errorMessage;
            toastIsOpen = true;
            appdata.errorMessage = '';
        }
    });

    async function saveYamlHandler() {
        let conf;
        try {
            conf = YAML.parse(yaml_code);
        } catch (e) {
            message = `Invalid YAML: ${e instanceof Error ? e.message : e}`;
            toastIsOpen = true;
            return;
        }
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

    async function saveProjectHandler(
        hashed_signature: string,
        title: string,
        saveAs: boolean,
    ) {
        loading = 50;
        try {
            const res = await ax_api.post("/save", {
                signature: hashed_signature,
                project_id: saveAs ? "new" : project_id,
                title: title,
            });
            if (res.status == 200) {
                let fin_project_id = res.data["project_id"];
                router.navigate("/projects/:id", {
                    params: {
                        id: fin_project_id,
                    },
                    replace: true,
                });
                project_id = fin_project_id;
            }
        } catch (e) {
            message = `Save failed: ${e instanceof Error ? e.message : e}`;
            toastIsOpen = true;
            console.error("save failed", e);
        } finally {
            loading = 0;
        }
    }

    let sess_id = $state("");
    let activeSSE: Set<EventSource> = $state(new Set());
    let cleanupAnalysis: (() => void) | null = null;

    $effect(() => {
        navTeleport.snippet = contextMenuSnippet;

        return () => {
            navTeleport.snippet = null;
        };
    });

    onMount(async () => {
        loading = 100;
        try {
            if (project_id === "new") {
                const res = await ax_api.post("/new");
                if (res.status == 200) {
                    sess_id = res.data[SESSID_KEY];
                    cleanupAnalysis = await initAnalysis(sess_id);
                } else {
                    message = `Failed to create session: ${res.status}`;
                    toastIsOpen = true;
                }
            } else {
                const res = await ax_api.post("/load", { project_id: project_id });
                if (res.status == 200) {
                    sess_id = res.data[SESSID_KEY];
                    cleanupAnalysis = await initAnalysis(sess_id);
                } else {
                    message = `Project not found (${res.status})`;
                    toastIsOpen = true;
                }
            }
        } catch (e) {
            message = `Failed to initialize: ${e instanceof Error ? e.message : e}`;
            toastIsOpen = true;
            console.error("init failed", e);
        }
        loading = 0;
    });

    onDestroy(() => {
        activeSSE.forEach((es) => es.close());
        activeSSE.clear();
        if (cleanupAnalysis) {
            cleanupAnalysis();
        }
    });

    async function runAction(
        context: DataItem,
        action: ActionItem,
        quick_str: string = "",
    ) {
        const query_str = `${SESSID_KEY}=${sess_id}${quick_str}`;
        const es = new EventSource(
            `${app_prefix}/${context.uuid}/actions/${action.uuid}/run?${query_str}`,
        );
        activeSSE.add(es);

        es.addEventListener("started", () => {
            loading = 100;
        });
        es.addEventListener("progress", (e) => {
            try {
                const [i, n] = JSON.parse(e.data);
                loading = (i / n) * 100;
            } catch (err) {
                console.error("Failed to parse progress event data", err);
            }
        });
        es.addEventListener("stats", (e) => {
            try {
                const { title, headers, data } = JSON.parse(e.data);
                if (tblRef) {
                    tblRef.set(title, headers, data);
                }
            } catch (err) {
                console.error("Failed to parse stats event data", err);
            }
        });
        es.addEventListener("completed", (e) => {
            try {
                const [data_updated, action_status] = JSON.parse(e.data);
                action.status = statusMap.get(action_status) || "Failed";
                if (data_updated && appdata.currentContext) {
                    getCurrentData(appdata.currentContext).then();
                }
            } catch (err) {
                console.error("Failed to parse completed event data", err);
            }
            loading = 0;
            activeSSE.delete(es);
            es.close();
        });
        es.addEventListener("message", (e) => {
            try {
                const msg = JSON.parse(e.data);
                message = msg;
                toastIsOpen = true;
            } catch (err) {
                console.error("Failed to parse message event data", err);
            }
        });
        es.onerror = () => {
            message = "Connection to analysis server lost";
            toastIsOpen = true;
            loading = 0;
            activeSSE.delete(es);
            es.close();
        };
    }
</script>

{#snippet contextMenuSnippet()}
    <SaveProjectDropdown onSaveProject={saveProjectHandler} />
    <ScenarioList
        scenarios={appdata.scenarios}
        currentScenario={appdata.currentScenario}
        onSwitchScenario={(s) => switchScenario(s).then(() => {})}
    />
{/snippet}

<Progress style="height:4px" value={loading} animated />
{#if keycloakService.enabled && !keycloakService.authenticated}
    <Alert color="warning" class="mb-0 py-2 text-center">
        You are not logged in. You can view and run analyses, but <b>saving is disabled</b>.
        <button class="btn btn-link btn-sm p-0 ms-2" onclick={() => keycloakService.login()}>Login now</button>
    </Alert>
{/if}
<div id="toast-holder">
    <Toast autohide body header="Message" bind:isOpen={toastIsOpen}>
        {message}
    </Toast>
</div>

<Row class="mt-1">
    <Col class="pe-1" style="max-width: 490px;">
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
                <DataList
                    data={appdata.data}
                    availableQuickActions={appdata.availableQuickActions}
                    onQuickAction={(d, q) => {
                        let fakeAction: ActionItem = {
                            name: q.action_name,
                            uuid: "quick",
                            status: "New",
                            type_path: q.action_path,
                        };
                        if (appdata.currentContext) {
                            runAction(
                                appdata.currentContext,
                                fakeAction,
                                `&data_uuid=${d.uuid}&idx=${q.idx}`,
                            ).then();
                        }
                    }}
                />
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

<StatsTable bind:this={tblRef} />

<style>
    #toast-holder {
        position: fixed;
        right: 10px;
        bottom: 10px;
        z-index: 9999;
    }
</style>
