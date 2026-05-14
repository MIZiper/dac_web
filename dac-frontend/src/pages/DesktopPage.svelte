<script lang="ts">
    import { onMount } from "svelte";
    import { ax_api } from "../utils/FetchObjects";
    import { desktopBridge } from "../utils/desktopBridge.svelte";
    import type { BridgeMessage } from "../utils/desktopBridge.svelte";
    import {
        Card, CardBody, CardSubtitle, CardText, CardTitle,
        Col, Row, Spinner, Alert, Button, Badge,
    } from "@sveltestrap/sveltestrap";
    import type { ProjectItem, ProjectListResponse } from "../schema";

    let projects: ProjectItem[] = $state([]);
    let total = $state(0);
    let currentPage = $state(1);
    let pageSize = $state(10);
    let loading = $state(true);
    let currentProjectId: string | null = $state(null);
    let currentTitle: string | null = $state(null);
    let statusMsg = $state("");
    let statusVariant: string = $state("info");
    let saveEnabled = $state(false);
    let savedConfig: string | null = $state(null);

    function setStatus(msg: string, variant = "info") {
        statusMsg = msg;
        statusVariant = variant;
    }

    // ── Send config to desktop app ──────────────────────────────────

    function sendToDesktop(projectId: string, title: string, config: any) {
        if (!desktopBridge.ready) {
            setStatus("Desktop bridge not available", "danger");
            return;
        }
        currentProjectId = projectId;
        currentTitle = title;
        saveEnabled = false;
        savedConfig = null;
        try {
            const configJson = JSON.stringify(config);
            desktopBridge.sendMessage("loadConfig", {
                projectId,
                title,
                configJson,
            });
            setStatus(`Sent "${title}" to desktop for local analysis.`, "success");
        } catch (e: any) {
            setStatus(`Bridge error: ${e.message}`, "danger");
        }
    }

    // ── API calls ───────────────────────────────────────────────────

    async function downloadAndSend(projectId: string) {
        setStatus("Downloading project config...", "info");
        try {
            const resp = await ax_api.get(`/projects/${projectId}/export`);
            const data = resp.data;
            const config = data.config;
            const title = data.title || projectId.slice(0, 8) + "...";
            sendToDesktop(projectId, title, {
                config,
                title,
                creator_name: data.creator_name,
                version: data.version,
            });
        } catch (e: any) {
            setStatus(
                `Download failed: ${e.response?.data?.detail || e.message}`,
                "danger",
            );
        }
    }

    async function saveBackToServer() {
        if (!savedConfig || !currentProjectId) return;
        setStatus("Saving to server...", "info");
        try {
            const parsed = JSON.parse(savedConfig);
            const body: any = {
                config: parsed.config || parsed,
                title: currentTitle || "",
                project_id: currentProjectId,
            };
            const resp = await ax_api.post("/projects/import", body);
            setStatus(`Saved! Project ID: ${resp.data.project_id}`, "success");
            saveEnabled = false;
        } catch (e: any) {
            setStatus(
                `Save failed: ${e.response?.data?.detail || e.message}`,
                "danger",
            );
        }
    }

    async function fetchProjects() {
        loading = true;
        try {
            const resp = await ax_api.get<ProjectListResponse>("/projects", {
                params: { page: currentPage, page_size: pageSize },
            });
            projects = resp.data.projects;
            total = resp.data.total;
        } catch {
            projects = [];
            total = 0;
        } finally {
            loading = false;
        }
    }

    // ── Effects & lifecycle ─────────────────────────────────────────

    $effect(() => {
        void currentPage;
        fetchProjects();
    });

    const totalPages = $derived(Math.ceil(total / pageSize) || 1);

    function formatDate(iso: string): string {
        return new Date(iso).toLocaleString();
    }

    onMount(() => {
        document.title = "Desktop DAC Bridge";

        // Listen for config sent back from desktop for saving
        const unsubReceive = desktopBridge.onMessage(
            "receiveConfig",
            (msg: BridgeMessage) => {
                const title = msg.title as string;
                const configJson = msg.configJson as string;
                setStatus("Received config from desktop, saving...", "info");
                currentTitle = title;
                savedConfig = configJson;
                saveEnabled = true;
            },
        );

        // Wait for the bridge to be ready
        desktopBridge.waitForReady().then(() => {
            setStatus("Connected to desktop application.", "success");
        });

        return () => {
            unsubReceive();
        };
    });
</script>

<div class="container-fluid p-4">
    <h3 class="mb-2">
        DAC Desktop Bridge
        {#if desktopBridge.ready}
            <Badge color="success" pill>Connected ({desktopBridge.type})</Badge>
        {:else}
            <Badge color="secondary" pill>Waiting for desktop...</Badge>
        {/if}
    </h3>

    {#if statusMsg}
        <Alert color={statusVariant} class="py-2 mb-3" dismissible>
            {statusMsg}
        </Alert>
    {/if}

    {#if saveEnabled && savedConfig}
        <div class="mb-3 p-3 border rounded bg-light">
            <strong>{currentTitle}</strong> updated locally.
            <Button color="primary" size="sm" class="ms-3" onclick={saveBackToServer}>
                Save Back to Server
            </Button>
        </div>
    {/if}

    <h5 class="mb-3">Projects</h5>

    {#if loading}
        <div class="text-center py-5"><Spinner /></div>
    {:else if projects.length === 0}
        <p class="text-muted text-center py-5">No projects found.</p>
    {:else}
        <Row>
            {#each projects as p (p.id)}
                <Col sm="6" lg="4" class="mb-3">
                    <Card class="project-card h-100 shadow-sm">
                        <CardBody>
                            <CardTitle>
                                {p.title || p.id.slice(0, 8) + "..."}
                            </CardTitle>
                            <CardSubtitle class="mb-2">
                                {#if p.creator_name}
                                    {p.creator_name}
                                {:else}
                                    <span class="text-muted">&mdash;</span>
                                {/if}
                            </CardSubtitle>
                            <CardText class="text-muted small">
                                {formatDate(p.created_at)}
                            </CardText>
                            <Button
                                color="outline-primary"
                                size="sm"
                                onclick={() => downloadAndSend(p.id)}
                                disabled={!desktopBridge.ready}
                            >
                                Open in Desktop
                            </Button>
                        </CardBody>
                    </Card>
                </Col>
            {/each}
        </Row>

        <div class="d-flex justify-content-between align-items-center mt-2">
            <small class="text-muted">
                Showing {(currentPage - 1) * pageSize + 1}&ndash;{Math.min(currentPage * pageSize, total)} of {total}
            </small>
            <nav>
                <ul class="pagination pagination-sm mb-0">
                    <li class="page-item {currentPage <= 1 ? 'disabled' : ''}">
                        <button class="page-link" disabled={currentPage <= 1}
                            onclick={() => currentPage--}>&laquo;</button>
                    </li>
                    {#each Array(totalPages) as _, i}
                        {@const pn = i + 1}
                        <li class="page-item {pn === currentPage ? 'active' : ''}">
                            <button class="page-link" onclick={() => currentPage = pn}>{pn}</button>
                        </li>
                    {/each}
                    <li class="page-item {currentPage >= totalPages ? 'disabled' : ''}">
                        <button class="page-link" disabled={currentPage >= totalPages}
                            onclick={() => currentPage++}>&raquo;</button>
                    </li>
                </ul>
            </nav>
        </div>
    {/if}
</div>

<style>
    :global(.project-card:hover) {
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.1) !important;
    }
</style>
