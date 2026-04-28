<script lang="ts">
    import { getContext } from "svelte";
    import {
        Badge,
        Button,
        Nav,
        NavItem,
        Pagination,
        Spinner,
        Table,
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
    let publishedOnly = $state(false);

    async function fetchProjects() {
        loading = true;
        try {
            const resp = await ax_api.get<ProjectListResponse>("/projects", {
                params: {
                    page: currentPage,
                    page_size: pageSize,
                    published_only: publishedOnly,
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
        void publishedOnly;
        fetchProjects();
    });

    function openProject(id: string) {
        router.navigate("/projects/:id", { params: { id } });
    }

    function formatDate(iso: string): string {
        const d = new Date(iso);
        return d.toLocaleString();
    }

    const totalPages = $derived(Math.ceil(total / pageSize) || 1);
</script>

<div class="home-page container-fluid p-4">
    <h3 class="mb-3">Projects</h3>

    <Nav tabs class="mb-3">
        <NavItem>
            <button
                class="nav-link {!publishedOnly ? 'active' : ''}"
                onclick={() => { publishedOnly = false; currentPage = 1; }}>All</button
            >
        </NavItem>
        <NavItem>
            <button
                class="nav-link {publishedOnly ? 'active' : ''}"
                onclick={() => { publishedOnly = true; currentPage = 1; }}>Published</button
            >
        </NavItem>
    </Nav>

    {#if loading}
        <div class="text-center py-5">
            <Spinner />
        </div>
    {:else if projects.length === 0}
        <p class="text-muted text-center py-5">No projects found.</p>
    {:else}
        <Table bordered hover responsive size="sm">
            <thead>
                <tr>
                    <th>Title</th>
                    <th>Project ID</th>
                    <th>Created</th>
                    <th>Updated</th>
                </tr>
            </thead>
            <tbody>
                {#each projects as p (p.id)}
                    <tr
                        role="button"
                        tabindex="0"
                        class="project-row"
                        onclick={() => openProject(p.id)}
                        onkeydown={(e) => {
                            if (e.key === "Enter") openProject(p.id);
                        }}
                    >
                        <td>
                            {#if p.publish_title}
                                {p.publish_title}
                                {#if p.publish_status === "Approved"}
                                    <Badge color="success" class="ms-1">Approved</Badge>
                                {/if}
                            {:else}
                                <span class="text-muted">&mdash;</span>
                            {/if}
                        </td>
                        <td><code>{p.id.slice(0, 8)}...</code></td>
                        <td>{formatDate(p.created_at)}</td>
                        <td>{formatDate(p.updated_at)}</td>
                    </tr>
                {/each}
            </tbody>
        </Table>

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
    .project-row {
        cursor: pointer;
    }
    .project-row:hover {
        background-color: rgba(0, 0, 0, 0.04);
    }
    code {
        font-size: 0.8em;
    }
</style>
