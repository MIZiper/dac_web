<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import {
    Button,
    Table,
    Badge,
    Modal,
    ModalHeader,
    ModalBody,
    ModalFooter,
    Spinner,
    Row,
    Col,
  } from "@sveltestrap/sveltestrap";
  import { ax_api } from "../utils/FetchObjects";

  interface SessionInfo {
    sess_id: string;
    pid: number | null;
    owner_user_id: string | null;
    project_id: string | null;
    conn_str: string | null;
    created_at: string;
    uptime_seconds: number;
    cpu_percent: number | null;
    memory_rss_mb: number | null;
    returncode: number | null;
    status: string;
  }

  interface SessionLogs {
    sess_id: string;
    stdout: string;
    stderr: string;
    log_file_stdout: string | null;
    log_file_stderr: string | null;
  }

  let sessions: SessionInfo[] = $state([]);
  let total: number = $state(0);
  let loading: boolean = $state(true);
  let error: string | null = $state(null);

  let logModalOpen: boolean = $state(false);
  let logData: SessionLogs | null = $state(null);
  let logSessId: string = $state("");
  let terminateConfirm: string | null = $state(null);

  let refreshInterval: ReturnType<typeof setInterval> | null = null;

  async function fetchSessions() {
    try {
      const resp = await ax_api.get("/admin/sessions");
      sessions = resp.data.sessions;
      total = resp.data.total;
      error = null;
    } catch (e: any) {
      sessions = [];
      total = 0;
      error = e._dacInfo?.message || "Failed to fetch sessions";
    } finally {
      loading = false;
    }
  }

  async function terminateSession(sessId: string) {
    try {
      await ax_api.post(`/admin/sessions/${sessId}/term`);
      terminateConfirm = null;
      await fetchSessions();
    } catch (e: any) {
      error = e._dacInfo?.message || "Failed to terminate session";
    }
  }

  async function viewLogs(sessId: string) {
    logSessId = sessId;
    logData = null;
    logModalOpen = true;
    try {
      const resp = await ax_api.get(`/admin/sessions/${sessId}/logs`);
      logData = resp.data;
    } catch (e: any) {
      logData = {
        sess_id: sessId,
        stdout: "",
        stderr: e._dacInfo?.message || "Failed to fetch logs",
        log_file_stdout: null,
        log_file_stderr: null,
      };
    }
  }

  function formatUptime(seconds: number): string {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}h ${m}m ${s}s`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  }

  function formatTime(iso: string): string {
    if (!iso) return "-";
    return new Date(iso).toLocaleString();
  }

  function statusBadgeColor(status: string): string {
    if (status === "running") return "success";
    if (status.startsWith("exited")) return "secondary";
    if (status === "zombie") return "warning";
    return "dark";
  }

  const runningCount = $derived(sessions.filter(
    (s) => s.status === "running"
  ).length);

  $effect(() => {
    const el = document.getElementById("log-stdout");
    if (el) el.scrollTop = el.scrollHeight;
  });

  onMount(() => {
    fetchSessions();
    refreshInterval = setInterval(fetchSessions, 5000);
  });

  onDestroy(() => {
    if (refreshInterval) clearInterval(refreshInterval);
  });
</script>

<div class="container-fluid p-3">
  <Row class="mb-3 align-items-center">
    <Col>
      <h3>Admin Dashboard</h3>
    </Col>
    <Col md="auto">
      <Button color="primary" onclick={fetchSessions} disabled={loading}>
        {#if loading}
          <Spinner size="sm" /> Loading
        {:else}
          Refresh
        {/if}
      </Button>
    </Col>
  </Row>

  {#if error}
    <div class="alert alert-danger alert-dismissible fade show" role="alert">
      {error}
      <button type="button" class="btn-close" aria-label="Dismiss" onclick={() => error = null}></button>
    </div>
  {/if}

  <Row class="mb-3">
    <Col md="3">
      <div class="card text-bg-light">
        <div class="card-body text-center">
          <h5 class="card-title">Total Sessions</h5>
          <h2>{total}</h2>
        </div>
      </div>
    </Col>
    <Col md="3">
      <div class="card text-bg-success">
        <div class="card-body text-center">
          <h5 class="card-title">Running</h5>
          <h2>{runningCount}</h2>
        </div>
      </div>
    </Col>
    <Col md="3">
      <div class="card text-bg-warning">
        <div class="card-body text-center">
          <h5 class="card-title">Exited / Zombie</h5>
          <h2>{total - runningCount}</h2>
        </div>
      </div>
    </Col>
  </Row>

  <Table bordered hover responsive size="sm">
    <thead>
      <tr>
        <th>Sess ID</th>
        <th>PID</th>
        <th>Owner</th>
        <th>Project</th>
        <th>Uptime</th>
        <th>CPU %</th>
        <th>Memory</th>
        <th>Created</th>
        <th>Status</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {#if sessions.length === 0 && !loading}
        <tr>
          <td colspan="10" class="text-center text-muted py-4">
            No active sessions
          </td>
        </tr>
      {/if}
      {#each sessions as s (s.sess_id)}
        <tr class={s.status !== "running" ? "table-secondary" : ""}>
          <td>
            <code title={s.sess_id}>{s.sess_id.slice(0, 12)}</code>
            {#if s.conn_str}
              <br /><small class="text-muted">{s.conn_str}</small>
            {/if}
          </td>
          <td>{s.pid ?? "-"}</td>
          <td>{s.owner_user_id ?? "-"}</td>
          <td>
            {#if s.project_id}
              <a href={`/projects/${s.project_id}`} target="_blank" class="text-decoration-none"
                >{s.project_id.slice(0, 12)}</a
              >
            {:else}
              -
            {/if}
          </td>
          <td>{formatUptime(s.uptime_seconds)}</td>
          <td>
            {#if s.cpu_percent != null}
              {s.cpu_percent}%
            {:else}
              -
            {/if}
          </td>
          <td>
            {#if s.memory_rss_mb != null}
              {s.memory_rss_mb} MB
            {:else}
              -
            {/if}
          </td>
          <td>{formatTime(s.created_at)}</td>
          <td>
            <Badge color={statusBadgeColor(s.status)}>{s.status}</Badge>
            {#if s.returncode != null}
              <br /><small class="text-muted">rc={s.returncode}</small>
            {/if}
          </td>
          <td>
            <div class="d-flex gap-1">
              {#if s.status === "running"}
                <Button color="danger" size="sm" onclick={() => terminateConfirm = s.sess_id}>
                  Terminate
                </Button>
              {/if}
              <Button color="secondary" size="sm" onclick={() => viewLogs(s.sess_id)}>
                Logs
              </Button>
            </div>
          </td>
        </tr>
      {/each}
    </tbody>
  </Table>

  {#if loading && sessions.length === 0}
    <div class="text-center py-5">
      <Spinner />
      <p class="text-muted mt-2">Loading sessions...</p>
    </div>
  {/if}
</div>

<!-- Terminate confirmation modal -->
<Modal isOpen={terminateConfirm != null} toggle={() => terminateConfirm = null}>
  <ModalHeader toggle={() => terminateConfirm = null}>Confirm Termination</ModalHeader>
  <ModalBody>
    <p>Are you sure you want to terminate session <code>{terminateConfirm?.slice(0, 12)}</code>?</p>
    <p class="text-danger">This will kill the subprocess and clean up all resources.</p>
  </ModalBody>
  <ModalFooter>
    <Button color="secondary" onclick={() => terminateConfirm = null}>Cancel</Button>
    <Button color="danger" onclick={() => terminateConfirm && terminateSession(terminateConfirm)}>
      Terminate
    </Button>
  </ModalFooter>
</Modal>

<!-- Logs modal -->
<Modal
  isOpen={logModalOpen}
  toggle={() => logModalOpen = false}
  size="xl"
>
  <ModalHeader toggle={() => logModalOpen = false}>
    Session Logs: <code>{logSessId.slice(0, 12)}</code>
    {#if logData?.log_file_stdout}
      <br /><small class="text-muted">File: {logData.log_file_stdout}</small>
    {/if}
  </ModalHeader>
  <ModalBody>
    <ul class="nav nav-tabs" id="logTabs" role="tablist">
      <li class="nav-item" role="presentation">
        <button class="nav-link active" id="stdout-tab" data-bs-toggle="tab"
          data-bs-target="#stdout-pane" type="button" role="tab">
          STDOUT
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" id="stderr-tab" data-bs-toggle="tab"
          data-bs-target="#stderr-pane" type="button" role="tab">
          STDERR
        </button>
      </li>
    </ul>
    <div class="tab-content mt-2" id="logTabsContent" style="max-height: 60vh; overflow-y: auto;">
      <div class="tab-pane fade show active" id="stdout-pane" role="tabpanel">
        <pre class="bg-light p-2 rounded small">{logData?.stdout || "(empty)"}</pre>
      </div>
      <div class="tab-pane fade" id="stderr-pane" role="tabpanel">
        <pre class="bg-light p-2 rounded small">{logData?.stderr || "(empty)"}</pre>
      </div>
    </div>
  </ModalBody>
  <ModalFooter>
    <Button color="secondary" onclick={() => logModalOpen = false}>Close</Button>
  </ModalFooter>
</Modal>
