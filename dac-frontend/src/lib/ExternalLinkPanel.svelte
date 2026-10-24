<script lang="ts">
    import { Badge, Button, Input } from "@sveltestrap/sveltestrap";
    import { ax_api } from "../utils/FetchObjects";

    interface ExternalLink {
        provider: string;
        external_id: string;
        external_url: string;
        status: string;
        status_updated_at?: string | null;
        checked_at?: string | null;
        frozen: boolean;
    }

    let {
        projectId,
        onchange,
    }: {
        projectId: string;
        onchange?: (state: { linked: boolean; frozen: boolean; status?: string; url?: string }) => void;
    } = $props();

    let link = $state<ExternalLink | null>(null);
    let reachable = $state(true);
    let loading = $state(false);
    let error = $state("");
    let candidateQuery = $state("");
    let candidates = $state<any[]>([]);
    let selectedId = $state("");
    let pickerOpen = $state(false);

    function notify() {
        const frozen = !!link && (!reachable || link.frozen);
        onchange?.({
            linked: !!link,
            frozen,
            status: link?.status,
            url: link?.external_url,
        });
    }

    async function refresh() {
        if (!projectId || projectId === "new") {
            link = null;
            reachable = true;
            notify();
            return;
        }
        loading = true;
        error = "";
        try {
            const res = await ax_api.get(`/projects/${projectId}/external-link`);
            link = res.data.link || null;
            reachable = res.data.reachable !== false;
        } catch (e: any) {
            error = e?.response?.data?.detail || "Failed to load external link";
        } finally {
            loading = false;
            notify();
        }
    }

    async function search() {
        if (!projectId || projectId === "new") return;
        loading = true;
        error = "";
        try {
            const res = await ax_api.get(
                `/projects/${projectId}/external-link/candidates`,
                { params: { q: candidateQuery } },
            );
            candidates = res.data.items || [];
        } catch (e: any) {
            error = e?.response?.data?.detail || "Failed to search TC nodes";
        } finally {
            loading = false;
        }
    }

    async function linkNode(externalId: string) {
        if (!externalId.trim()) return;
        loading = true;
        error = "";
        try {
            const res = await ax_api.put(`/projects/${projectId}/external-link`, {
                external_id: externalId.trim(),
            });
            link = res.data.link || null;
            reachable = true;
            pickerOpen = false;
            selectedId = "";
            candidates = [];
        } catch (e: any) {
            error = e?.response?.data?.detail || "Failed to link TC node";
        } finally {
            loading = false;
            notify();
        }
    }

    async function unlink() {
        loading = true;
        error = "";
        try {
            await ax_api.delete(`/projects/${projectId}/external-link`);
            link = null;
            reachable = true;
        } catch (e: any) {
            error = e?.response?.data?.detail || "Failed to unlink TC node";
        } finally {
            loading = false;
            notify();
        }
    }

    $effect(() => {
        projectId;
        refresh();
    });
</script>

{#if projectId && projectId !== "new"}
    <div class="border rounded px-3 py-2 mb-2 bg-body-tertiary">
        <div class="d-flex flex-wrap align-items-center gap-2">
            <span class="small fw-semibold">TC catalog</span>
            {#if link}
                <Badge color={link.frozen ? "warning" : "secondary"}>{link.status}</Badge>
                {#if !reachable}
                    <Badge color="danger">state unavailable</Badge>
                {/if}
                <a href={link.external_url} target="_blank" rel="noreferrer" class="small">
                    Open in TC
                </a>
                <Button size="sm" color="outline-secondary" onclick={refresh} disabled={loading}>
                    Refresh
                </Button>
                <Button size="sm" color="outline-danger" onclick={unlink} disabled={loading || link.frozen}>
                    Unlink
                </Button>
            {:else}
                <span class="small text-muted">Not linked</span>
                <Button size="sm" color="outline-primary" onclick={() => { pickerOpen = !pickerOpen; }}>
                    Link TC node
                </Button>
            {/if}
            {#if error}<span class="small text-danger">{error}</span>{/if}
        </div>

        {#if pickerOpen && !link}
            <div class="mt-2">
                <div class="d-flex gap-2">
                    <Input
                        type="text"
                        placeholder="Search TC nodes by title"
                        bind:value={candidateQuery}
                        onkeydown={(e) => { if (e.key === "Enter") search(); }}
                    />
                    <Button color="secondary" onclick={search} disabled={loading}>Search</Button>
                </div>
                <div class="d-flex gap-2 mt-2">
                    <Input type="text" placeholder="Or paste TC node ID" bind:value={selectedId} />
                    <Button color="primary" onclick={() => linkNode(selectedId)} disabled={loading}>
                        Link
                    </Button>
                </div>
                {#if candidates.length}
                    <div class="list-group mt-2">
                        {#each candidates as candidate}
                            <button
                                type="button"
                                class="list-group-item list-group-item-action py-1"
                                onclick={() => linkNode(candidate.id)}
                            >
                                <span class="fw-semibold">{candidate.title}</span>
                                <span class="small text-muted ms-2">{candidate.status}</span>
                                {#if candidate.source_system}
                                    <span class="badge text-bg-warning ms-2">linked elsewhere</span>
                                {/if}
                            </button>
                        {/each}
                    </div>
                {/if}
            </div>
        {/if}
    </div>
{/if}
