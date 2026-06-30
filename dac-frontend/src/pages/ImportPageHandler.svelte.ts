import { ax_api } from "../utils/FetchObjects";
import type {
    ActionDecision,
    ActionReplacementItem,
    ImportApplyResp,
    ImportPreviewResp,
    ProjectConfig,
} from "../schema";

export const importState: {
    projectConfig: ProjectConfig | null;
    preview: ImportPreviewResp | null;
    decisions: ActionDecision[];
    rawFileContent: string;
    loading: boolean;
    errorMessage: string;
    successMessage: string;
} = $state({
    projectConfig: null,
    preview: null,
    decisions: [],
    rawFileContent: "",
    loading: false,
    errorMessage: "",
    successMessage: "",
});

function handleError(context: string, e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error(`Error in ${context}:`, e);
    importState.errorMessage = msg;
    importState.loading = false;
}

export function parseProjectFile(content: string): ProjectConfig | null {
    let parsed: any;
    try {
        parsed = JSON.parse(content);
    } catch {
        importState.errorMessage = "Invalid JSON file.";
        return null;
    }
    if (!parsed.dac || typeof parsed.dac !== "object") {
        importState.errorMessage =
            "Invalid project file: missing top-level 'dac' key.";
        return null;
    }
    const actions = parsed.dac?.actions?.length || 0;
    const contexts = parsed.dac?.contexts?.length || 0;
    const title = parsed.dac_web?.title || "(unnamed)";
    importState.successMessage = `Loaded project "${title}" (${contexts} contexts, ${actions} actions).`;

    return parsed as ProjectConfig;
}

function buildDecisions(
    replacements: ActionReplacementItem[],
): ActionDecision[] {
    return replacements
        .filter(
            (r) =>
                r.status === "resolved" || r.status === "unresolved",
        )
        .map((r) => ({
            action_index: r.action_index,
            action_uuid: r.action_uuid,
            approved: r.status === "resolved",
        }));
}

export async function runImportPreview() {
    const config = importState.projectConfig;
    if (!config) {
        importState.errorMessage = "No project config loaded.";
        return;
    }
    importState.loading = true;
    importState.errorMessage = "";
    importState.successMessage = "";
    try {
        const resp = await ax_api.post<ImportPreviewResp>(
            "/projects/import-preview",
            { config },
        );
        importState.preview = resp.data;
        importState.decisions = buildDecisions(
            resp.data.replacements,
        );
        importState.successMessage =
            `Preview complete: ${resp.data.summary.resolved} resolved, ` +
            `${resp.data.summary.unresolved} unresolved, ` +
            `${resp.data.summary.unchanged} unchanged.`;
    } catch (e) {
        handleError("importPreview", e);
    } finally {
        importState.loading = false;
    }
}

export function toggleDecision(index: number) {
    importState.decisions = importState.decisions.map((d) =>
        d.action_index === index ? { ...d, approved: !d.approved } : d,
    );
}

export function updateOverrideReplacement(
    actionIndex: number,
    jsonStr: string,
) {
    let parsed: Record<string, any> | undefined;
    try {
        parsed = JSON.parse(jsonStr);
    } catch {
        parsed = undefined;
    }
    importState.decisions = importState.decisions.map((d) => {
        if (d.action_index !== actionIndex) return d;
        return {
            ...d,
            override_replacement: parsed,
        };
    });
}

export async function runImportApply(): Promise<ImportApplyResp | null> {
    const config = importState.projectConfig;
    if (!config) {
        importState.errorMessage = "No project config to import.";
        return null;
    }
    importState.loading = true;
    importState.errorMessage = "";
    try {
        const resp = await ax_api.post<ImportApplyResp>(
            "/projects/import-apply",
            {
                config,
                decisions: importState.decisions,
                title: config.dac_web?.title || "",
            },
        );
        importState.successMessage = `Project "${resp.data.title || resp.data.project_id.slice(-8)}" imported successfully.`;
        return resp.data;
    } catch (e) {
        handleError("importApply", e);
        return null;
    } finally {
        importState.loading = false;
    }
}

export function resetImportState() {
    importState.projectConfig = null;
    importState.preview = null;
    importState.decisions = [];
    importState.rawFileContent = "";
    importState.loading = false;
    importState.errorMessage = "";
    importState.successMessage = "";
}
