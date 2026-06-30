<script lang="ts">
    import { getContext, onMount } from "svelte";
    import {
        Alert,
        Badge,
        Button,
        Card,
        CardBody,
        CardHeader,
        CardTitle,
        Col,
        Row,
        Spinner,
        Table,
    } from "@sveltestrap/sveltestrap";
    import CodeMirror from "svelte-codemirror-editor";
    import { json } from "@codemirror/lang-json";

    import {
        importState,
        parseProjectFile,
        runImportPreview,
        runImportApply,
        toggleDecision,
        updateOverrideReplacement,
        resetImportState,
    } from "./ImportPageHandler.svelte";
    import type { ActionDecision, ActionReplacementItem } from "../schema";

    const router = getContext<{
        navigate: (path: string, opts?: any) => void;
    }>("router");

    let dragOver = $state(false);
    let editingIndex = $state<number | null>(null);
    let editJsonText = $state("");

    onMount(() => {
        resetImportState();
    });

    function handleFileSelect(event: Event) {
        const target = event.target as HTMLInputElement;
        const file = target.files?.[0];
        if (file) readFile(file);
        target.value = "";
    }

    function handleDrop(event: DragEvent) {
        event.preventDefault();
        dragOver = false;
        const file = event.dataTransfer?.files?.[0];
        if (file) readFile(file);
    }

    function readFile(file: File) {
        importState.errorMessage = "";
        importState.successMessage = "";
        const reader = new FileReader();
        reader.onload = () => {
            const content = reader.result as string;
            importState.rawFileContent = content;
            importState.projectConfig = parseProjectFile(content);
            importState.preview = null;
            importState.decisions = [];
        };
        reader.onerror = () => {
            importState.errorMessage = "Failed to read file.";
        };
        reader.readAsText(file);
    }

    function handleDragOver(event: DragEvent) {
        event.preventDefault();
        dragOver = true;
    }

    function handleDragLeave() {
        dragOver = false;
    }

    function startEdit(replacement: ActionReplacementItem) {
        editingIndex = replacement.action_index;
        editJsonText = JSON.stringify(
            replacement.replacement || replacement.original || {},
            null,
            2,
        );
    }

    function saveEdit() {
        if (editingIndex !== null) {
            updateOverrideReplacement(editingIndex, editJsonText);
        }
        editingIndex = null;
        editJsonText = "";
    }

    function cancelEdit() {
        editingIndex = null;
        editJsonText = "";
    }

    async function handleApply() {
        const result = await runImportApply();
        if (result) {
            router.navigate(`/projects/${result.project_id}`);
        }
    }

    function statusBadgeColor(status: string): string {
        switch (status) {
            case "resolved":
                return "success";
            case "unresolved":
                return "warning";
            default:
                return "secondary";
        }
    }

</script>

<div class="import-page container-fluid p-4">
    <h3 class="mb-3">Import Project</h3>

    {#if importState.errorMessage}
        <Alert color="danger" dismissible>{importState.errorMessage}</Alert>
    {/if}
    {#if importState.successMessage}
        <Alert color="info" dismissible>{importState.successMessage}</Alert>
    {/if}

    <!-- Step 1: Upload -->
    <Card class="mb-4">
        <CardHeader>
            <CardTitle>1. Select project file</CardTitle>
        </CardHeader>
        <CardBody>
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div
                class="drop-zone text-center p-4 border rounded-3 {dragOver ? 'border-primary bg-light' : ''}"
                ondrop={handleDrop}
                ondragover={handleDragOver}
                ondragleave={handleDragLeave}
            >
                <p class="text-muted mb-2">
                    Drop a <code>.dac.json</code> file here, or click to select.
                </p>
                <input
                    type="file"
                    accept=".json"
                    class="d-none"
                    id="import-file-input"
                    onchange={handleFileSelect}
                />
                <label for="import-file-input" class="btn btn-outline-primary btn-sm">
                    Choose file
                </label>
            </div>
        </CardBody>
    </Card>

    <!-- Step 2: Preview -->
    {#if importState.projectConfig}
        <Card class="mb-4">
            <CardHeader>
                <CardTitle>2. Preview replacements</CardTitle>
            </CardHeader>
            <CardBody>
                {#if !importState.preview}
                    <p class="text-muted">
                        Project loaded. Click "Preview" to see which actions need
                        replacement.
                    </p>
                    <Button
                        color="primary"
                        onclick={runImportPreview}
                        disabled={importState.loading}
                    >
                        {#if importState.loading}
                            <Spinner size="sm" class="me-1" />Previewing...
                        {:else}
                            Preview replacements
                        {/if}
                    </Button>
                {/if}
            </CardBody>
        </Card>
    {/if}

    <!-- Step 3: Review & Apply -->
    {#if importState.preview && importState.preview.replacements.length > 0}
        {@const preview = importState.preview}
        {@const summary = preview.summary}
        <Card class="mb-4">
            <CardHeader>
                <Row>
                    <Col>
                        <CardTitle>3. Review & apply</CardTitle>
                    </Col>
                    <Col xs="auto">
                        <small class="text-muted">
                            {summary.total_actions} actions
                        </small>
                    </Col>
                </Row>
            </CardHeader>
            <CardBody>
                <div class="mb-3 d-flex gap-3">
                    <span>
                        <Badge color="success">{summary.resolved} resolved</Badge>
                    </span>
                    <span>
                        <Badge color="warning">{summary.unresolved} unresolved</Badge>
                    </span>
                    <span>
                        <Badge color="secondary">{summary.unchanged} unchanged</Badge>
                    </span>
                </div>

                <Table bordered size="sm" responsive class="align-middle">
                    <thead>
                        <tr>
                            <th style="width: 30%">Original Action</th>
                            <th style="width: 30%">Proposed Change</th>
                            <th style="width: 10%">Status</th>
                            <th style="width: 10%">Accept</th>
                            <th style="width: 20%">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each preview.replacements as item (item.action_index)}
                            <tr>
                                <td>
                                    <code class="small">{item.original._class_ || "(unknown)"}</code>
                                    <br />
                                    <small class="text-muted">
                                        {item.original.name || "—"}
                                    </small>
                                </td>
                                <td>
                                    {#if item.status === "unchanged"}
                                        <span class="text-muted small">No change needed</span>
                                    {:else if item.replacement}
                                        <code class="small">{item.replacement._class_ || "(unknown)"}</code>
                                    {:else}
                                        <span class="text-muted small">{item.summary}</span>
                                    {/if}
                                    {#if item.reason}
                                        <br />
                                        <small class="text-warning">{item.reason}</small>
                                    {/if}
                                </td>
                                <td>
                                    <Badge color={statusBadgeColor(item.status)}>
                                        {item.status}
                                    </Badge>
                                </td>
                                <td>
                                    {#if item.status !== "unchanged"}
                                        {@const d = importState.decisions.find(x => x.action_index === item.action_index)}
                                        <div class="form-check form-switch">
                                            <input
                                                class="form-check-input"
                                                type="checkbox"
                                                role="switch"
                                                id="accept-{item.action_index}"
                                                checked={d?.approved ?? false}
                                                onchange={() => toggleDecision(item.action_index)}
                                            />
                                        </div>
                                    {/if}
                                </td>
                                <td>
                                    {#if editingIndex === item.action_index}
                                        <div class="mb-2" style="height: 200px;">
                                            <div class="json-scroll">
                                                <CodeMirror
                                                    bind:value={editJsonText}
                                                    lang={json()}
                                                />
                                            </div>
                                        </div>
                                        <div class="d-flex gap-2">
                                            <Button
                                                color="success"
                                                size="sm"
                                                onclick={saveEdit}
                                            >
                                                Apply
                                            </Button>
                                            <Button
                                                color="secondary"
                                                size="sm"
                                                onclick={cancelEdit}
                                            >
                                                Cancel
                                            </Button>
                                        </div>
                                    {:else if item.status !== "unchanged" && item.replacement}
                                        <Button
                                            color="outline-secondary"
                                            size="sm"
                                            onclick={() => startEdit(item)}
                                        >
                                            Edit
                                        </Button>
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </Table>

                <div class="d-flex justify-content-end mt-3">
                    <Button
                        color="primary"
                        onclick={handleApply}
                        disabled={importState.loading}
                    >
                        {#if importState.loading}
                            <Spinner size="sm" class="me-1" />Importing...
                        {:else}
                            Apply &amp; Import
                        {/if}
                    </Button>
                </div>
            </CardBody>
        </Card>
    {/if}
</div>

<style>
    .drop-zone {
        cursor: pointer;
        transition: background-color 0.2s, border-color 0.2s;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .json-scroll {
        height: 200px;
        overflow-y: auto;
        border: 1px solid var(--bs-border-color, #dee2e6);
        border-radius: 0.25rem;
    }
</style>
