/**
 * DesktopBridge — unified API for web ↔ desktop app communication.
 *
 * Supports multiple backends:
 *   - "qt":        QWebEngineView (console.log bridge + window.__desktopBridgeReceive)
 *   - "pywebview": pywebview subprocess (window.pywebview.api + window.__desktopBridgeReceive)
 *   - "none":      running standalone in a regular browser
 *
 * Usage:
 *
 *   import { desktopBridge } from "../utils/desktopBridge";
 *
 *   onMount(() => { desktopBridge.waitForReady(); });
 *
 *   desktopBridge.sendMessage("loadConfig", { projectId, title, configJson });
 *
 *   const unsub = desktopBridge.onMessage("receiveConfig", (data) => {
 *       // handle config received from desktop
 *   });
 *   // later: unsub();
 */

export interface BridgeMessage {
    type: string;
    [key: string]: any;
}

type MessageHandler = (data: BridgeMessage) => void;
type BackendType = "qt" | "pywebview" | "none";

class DesktopBridgeClient {
    // State
    ready = $state(false);
    type: BackendType = $state("none");

    private _handlers = new Map<string, Set<MessageHandler>>();
    private _readyPromise: Promise<void> | null = null;
    private _readyResolve: (() => void) | null = null;
    private _checkTimer: ReturnType<typeof setInterval> | null = null;

    // ── Initialisation ────────────────────────────────────────────────

    /**
     * Wait until the bridge is detected and ready.
     * Safe to call multiple times; only detects once.
     */
    waitForReady(): Promise<void> {
        if (this.ready) return Promise.resolve();
        if (this._readyPromise) return this._readyPromise;

        this._readyPromise = new Promise((resolve) => {
            this._readyResolve = resolve;
        });

        // Try immediate detection
        this._detect();

        // Poll for injected bridges (they may appear after page load)
        if (!this.ready) {
            this._checkTimer = setInterval(() => this._detect(), 200);
        }

        return this._readyPromise;
    }

    // ── Messaging ──────────────────────────────────────────────────────

    /**
     * Send a typed message to the desktop application.
     */
    sendMessage(type: string, data: Record<string, any> = {}): void {
        const payload = { type, ...data };

        if (this.type === "qt") {
            const msg = JSON.stringify({
                action: "message",
                type,
                data: payload,
            });
            console.log("DAC_BRIDGE:" + msg);
        } else if (this.type === "pywebview") {
            const api = (window as any).pywebview?.api;
            if (api?.sendToDesktop) {
                api.sendToDesktop(JSON.stringify(payload));
            }
        }
    }

    /**
     * Register a handler for incoming messages of a specific type.
     * Returns an unsubscribe function.
     */
    onMessage(type: string, handler: MessageHandler): () => void {
        if (!this._handlers.has(type)) {
            this._handlers.set(type, new Set());
        }
        this._handlers.get(type)!.add(handler);
        return () => {
            this._handlers.get(type)?.delete(handler);
        };
    }

    // ── Internals ──────────────────────────────────────────────────────

    private _detect(): void {
        // Detect pywebview bridge
        if (typeof (window as any).pywebview?.api?.sendToDesktop === "function") {
            this._setReady("pywebview");
            return;
        }

        // Detect Qt bridge (injected by desktop app after page load)
        if (typeof (window as any).dacDesktop?.loadConfig === "function") {
            this._setReady("qt");
            return;
        }

        // Also check for the unified receive function
        if (typeof (window as any).dacDesktop?.receive === "function") {
            this._setReady("qt");
            return;
        }
    }

    private _setReady(type: BackendType): void {
        if (this.ready) return;
        this.ready = true;
        this.type = type;
        this._setupReceiver();

        if (this._checkTimer) {
            clearInterval(this._checkTimer);
            this._checkTimer = null;
        }
        if (this._readyResolve) {
            this._readyResolve();
            this._readyResolve = null;
        }
    }

    private _setupReceiver(): void {
        // __desktopBridgeReceive is called by both Qt and pywebview bridges
        const win = window as any;
        if (win.__desktopBridgeReceive) return; // already set up

        win.__desktopBridgeReceive = (data: BridgeMessage) => {
            const msgType = data?.type;
            if (!msgType) return;
            const handlers = this._handlers.get(msgType);
            if (handlers) {
                for (const handler of handlers) {
                    try {
                        handler(data);
                    } catch (e) {
                        console.error("DesktopBridge handler error:", e);
                    }
                }
            }
        };

        // Backward compat: wire up legacy window.desktopReceiveConfig
        win.desktopReceiveConfig = function (title: string, configJson: string) {
            win.__desktopBridgeReceive({
                type: "receiveConfig",
                title,
                configJson,
            });
        };
    }
}

/** Singleton bridge client */
export const desktopBridge = new DesktopBridgeClient();
