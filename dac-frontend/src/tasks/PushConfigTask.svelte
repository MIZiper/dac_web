<script lang="ts">
    import {
        Badge,
        Button,
        Input,
        Modal,
        ModalBody,
        ModalFooter,
        ModalHeader,
    } from "@sveltestrap/sveltestrap";
    import { getContext, onMount } from "svelte";
    import type { TaskBaseProps } from "./TaskRouter.svelte";
    import type { DataItem } from "../schema";
    import { ax_api } from "../utils/FetchObjects";

    let {
        config_in,
        onTaskDone,
        availableData = [],
    }: TaskBaseProps = $props();

    const router: any = getContext("router");
    const projectId: string = router.route.getParams("/projects/:id")?.id || "new";

    let isOpen = $state(false);
    let error = $state("");
    let loading = $state(false);
    let query = $state("");
    let candidates = $state<any[]>([]);
    let selectedNodeId = $state("");
    let selectedTitle = $state("");
    let selectedData = $state("");
    let mode = $state("a");
    let tcUiUrl = $state("");

    interface CandidateData {
        qname: string;
        name: string;
        typePath: string;
    }

    function collectData(nodes: DataItem[]): CandidateData[] {
        const result: CandidateData[] = [];
        for (const node of nodes) {
            if (
                node.type_path === "dac.modules.timedata.TimeData" ||
                node.type_path === "dac.modules.nvh.data.FreqDomainData"
            ) {
                result.push({
                    qname: node.qualified_name || node.name,
                    name: node.name,
                    typePath: node.type_path,
                });
            }
            if (node.children?.length) result.push(...collectData(node.children));
        }
        return result;
    }

    const dataOptions = $derived(collectData(availableData));

    async function loadConfig() {
        try {
            const res = await ax_api.get("/config");
            tcUiUrl = res.data?.external_system_ui_url || "";
        } catch {
            tcUiUrl = "";
        }
    }

    async function search() {
        loading = true;
        error = "";
        try {
            const res = await ax_api.get("/tc/push-candidates", {
                params: { q: query, page_size: 30 },
            });
            candidates = res.data?.items || [];
        } catch (e: any) {
            error = e?.response?.data?.message || e?.message || "Failed to search TC";
        } finally {
            loading = false;
        }
    }

    function chooseCandidate(item: any) {
        selectedNodeId = item.id;
        selectedTitle = item.title;
    }

    function save() {
        if (!selectedData) {
            error = "Select a data node";
            return;
        }
        if (!selectedNodeId) {
            error = "Select a TC item";
            return;
        }
        if (!projectId || projectId === "new") {
            error = "Save the project before pushing results";
            return;
        }
        const selected = dataOptions.find((item) => item.qname === selectedData);
        const payload: Record<string, any> = {
            target_node_id: selectedNodeId,
            target_title: selectedTitle,
            source_id: projectId,
            mode,
        };
        if (selected?.typePath === "dac.modules.nvh.data.FreqDomainData") {
            payload.spectra = [selectedData];
        } else {
            payload.channels = [selectedData];
        }
        isOpen = false;
        onTaskDone(payload);
    }

    onMount(() => {
        isOpen = true;
        const configured = config_in["channels"] || config_in["spectra"];
        selectedData = Array.isArray(configured)
            ? String(configured[0] || "")
            : String(configured || "");
        selectedNodeId = String(config_in["target_node_id"] || "");
        selectedTitle = String(config_in["target_title"] || "");
        mode = String(config_in["mode"] || "a");
        loadConfig();
        search();
    });
</script>

<Modal {isOpen} size="lg">
    <ModalHeader>Push data to TC</ModalHeader>
    <ModalBody>
        {#if projectId === "new"}
            <div class="alert alert-warning py-2 small">
                Save this project first; pushed results need a project id.
            </div>
        {/if}

        <label class="form-label" for="push-data-node">Data node</label>
        <select id="push-data-node" class="form-select mb-3" bind:value={selectedData}>
            <option value="" disabled>-- choose TimeData or FreqDomainData --</option>
            {#each dataOptions as option (option.qname)}
                <option value={option.qname}>
                    {option.name} ({option.typePath.split(".").pop()})
                </option>
            {/each}
        </select>

        <label class="form-label" for="push-mode">Append mode</label>
        <select id="push-mode" class="form-select mb-3" bind:value={mode}>
            <option value="a">Append — keep contributions from other projects</option>
            <option value="w">Replace — overwrite the item content</option>
        </select>

        <label class="form-label" for="push-tc-query">TC target</label>
        <div class="d-flex gap-2 mb-2">
            <Input
                id="push-tc-query"
                placeholder="Search TC items"
                bind:value={query}
                onkeydown={(e) => { if (e.key === "Enter") search(); }}
            />
            <Button color="secondary" onclick={search} disabled={loading}>Search</Button>
            {#if tcUiUrl}
                <a
                    class="btn btn-outline-primary"
                    href={`${tcUiUrl.replace(/\/$/, "")}/new?type=SourceItem.v00`}
                    target="_blank"
                    rel="noreferrer"
                >
                    Create in TC
                </a>
            {/if}
        </div>

        {#if selectedNodeId}
            <div class="alert alert-info py-2 small mb-2">
                Selected: <strong>{selectedTitle || selectedNodeId}</strong>
            </div>
        {/if}
        {#if error}
            <div class="alert alert-danger py-2 small mb-2">{error}</div>
        {/if}

        {#if candidates.length}
            <div class="list-group">
                {#each candidates as candidate}
                    <button
                        type="button"
                        class="list-group-item list-group-item-action py-1"
                        class:active={candidate.id === selectedNodeId}
                        onclick={() => chooseCandidate(candidate)}
                    >
                        <span class="fw-semibold">{candidate.title}</span>
                        {#if candidate.data_type}
                            <Badge class="text-bg-secondary ms-2">{candidate.data_type}</Badge>
                        {/if}
                        <span class="small text-muted ms-2">{candidate.status}</span>
                        {#if candidate.frozen}
                            <Badge class="text-bg-warning ms-2">frozen</Badge>
                        {/if}
                    </button>
                {/each}
            </div>
        {:else if !loading}
            <p class="small text-muted mb-0">No pushable TC items found.</p>
        {/if}
    </ModalBody>
    <ModalFooter>
        <Button color="primary" onclick={save} disabled={loading}>Save</Button>
        <Button
            color="secondary"
            onclick={() => {
                isOpen = false;
                onTaskDone(null);
            }}>Cancel</Button>
    </ModalFooter>
</Modal>
