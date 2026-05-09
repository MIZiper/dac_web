<script lang="ts">
    import { getContext } from "svelte";
    import {
        Card,
        CardBody,
        CardSubtitle,
        CardText,
        CardTitle,
        Col,
        Pagination,
        Row,
        Spinner,
    } from "@sveltestrap/sveltestrap";
    import { ax_api } from "../utils/FetchObjects";
    import type { ProjectItem, ProjectListResponse } from "../schema";

    const router = getContext<{
        navigate: (path: string, opts?: any) => void;
    }>("router");

    let projects: ProjectItem[] = $state([]);
    let total = $state(0);
    let currentPage = $state(1);
    let pageSize = $state(10);
    let loading = $state(true);

    async function fetchProjects() {
        loading = true;
        try {
            const resp = await ax_api.get<ProjectListResponse>("/projects", {
                params: {
                    page: currentPage,
                    page_size: pageSize,
                },
            });
            projects = resp.data.projects;
            total = resp.data.total;
        } catch (e) {
            console.error("Failed to fetch projects:", e);
            projects = [];
            total = 0;
        } finally {
            loading = false;
        }
    }

    $effect(() => {
        void currentPage;
        fetchProjects();
    });

    function projectUrl(id: string): string {
        return `/projects/${id}`;
    }

    function formatDate(iso: string): string {
        const d = new Date(iso);
        return d.toLocaleString();
    }

    const totalPages = $derived(Math.ceil(total / pageSize) || 1);
</script>

<div class="home-page container-fluid p-4">
    <h3 class="mb-3">Projects</h3>

    {#if loading}
        <div class="text-center py-5">
            <Spinner />
        </div>
    {:else if projects.length === 0}
        <p class="text-muted text-center py-5">No projects found.</p>
    {:else}
        <Row>
            {#each projects as p (p.id)}
                <Col sm="6" lg="4" class="mb-3">
                    <Card class="project-card h-100 shadow-sm">
                        <CardBody>
                            <CardTitle>
                                <a
                                    href={projectUrl(p.id)}
                                    class="text-decoration-none"
                                >
                                    {p.title || p.id.slice(0, 8) + "..."}
                                </a>
                            </CardTitle>
                            <CardSubtitle class="mb-2">
                                {#if p.creator_name}
                                    {p.creator_name}
                                {:else}
                                    <span class="text-muted">&mdash;</span>
                                {/if}
                            </CardSubtitle>
                            <CardText class="text-muted small mb-1">
                                Created: {formatDate(p.created_at)}
                            </CardText>
                            <CardText class="text-muted small">
                                Updated: {formatDate(p.updated_at)}
                            </CardText>
                            <CardText class="text-muted mt-2">
                                <small>
                                    <code class="project-id">{p.id}</code>
                                </small>
                            </CardText>
                        </CardBody>
                    </Card>
                </Col>
            {/each}
        </Row>

        <div class="d-flex justify-content-between align-items-center mt-2">
            <small class="text-muted">
                Showing {(currentPage - 1) * pageSize + 1}{"\u2013"}{Math.min(currentPage * pageSize, total)} of {total}
            </small>
            <Pagination
                listClassName="mb-0"
                aria-label="Project pagination"
                size="sm"
            >
                <li class="page-item {currentPage <= 1 ? 'disabled' : ''}">
                    <button
                        class="page-link"
                        disabled={currentPage <= 1}
                        onclick={() => { if (currentPage > 1) currentPage--; }}>&laquo;</button
                    >
                </li>
                {#each Array(totalPages) as _, i}
                    {@const pn = i + 1}
                    <li class="page-item {pn === currentPage ? 'active' : ''}">
                        <button
                            class="page-link"
                            onclick={() => { currentPage = pn; }}>{pn}</button
                        >
                    </li>
                {/each}
                <li
                    class="page-item {currentPage >= totalPages ? 'disabled' : ''}"
                >
                    <button
                        class="page-link"
                        disabled={currentPage >= totalPages}
                        onclick={() => { if (currentPage < totalPages) currentPage++; }}>&raquo;</button
                    >
                </li>
            </Pagination>
        </div>
    {/if}
</div>

<style>
    :global(.project-card) {
        transition: box-shadow 0.2s ease;
    }
    :global(.project-card:hover) {
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.1) !important;
    }
    .project-id {
        font-size: 0.75rem;
        user-select: all;
    }
</style>
