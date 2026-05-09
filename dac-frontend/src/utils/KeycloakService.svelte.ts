import { setAuthTokenProvider } from "./FetchObjects";
import type KeycloakType from "keycloak-js";

let _kc: KeycloakType | null = null;
let _initialized = false;
let _initPromise: Promise<void> | null = null;

export const keycloakService: {
    enabled: boolean;
    authenticated: boolean;
    username: string | null;
    userId: string | null;
    token: string | null;
    init: () => Promise<void>;
    login: () => Promise<void>;
    logout: () => Promise<void>;
} = $state({
    enabled: false,
    authenticated: false,
    username: null,
    userId: null,
    token: null,

    async init() {
        if (_initialized) return;
        if (_initPromise) return _initPromise;

        _initPromise = (async () => {
            try {
                const resp = await fetch("/api/auth/status");
                const config = (await resp.json()) as {
                    keycloak_enabled: boolean;
                    keycloak_url: string;
                    keycloak_realm: string;
                    keycloak_client_id: string;
                };

                if (!config.keycloak_enabled) {
                    keycloakService.enabled = false;
                    _initialized = true;
                    return;
                }

                const Keycloak = (await import("keycloak-js")).default;
                _kc = new Keycloak({
                    url: config.keycloak_url,
                    realm: config.keycloak_realm,
                    clientId: config.keycloak_client_id,
                });

                try {
                    const authenticated = await _kc.init({
                        onLoad: "check-sso",
                        silentCheckSsoRedirectUri:
                            window.location.origin + "/silent-check-sso.html",
                    });

                    keycloakService.enabled = true;
                    keycloakService.authenticated = authenticated;
                    if (authenticated && _kc.tokenParsed) {
                        keycloakService.username =
                            _kc.tokenParsed.given_name || _kc.tokenParsed.preferred_username || null;
                        keycloakService.userId = _kc.tokenParsed.sub || null;
                    }
                } catch {
                    keycloakService.enabled = true;
                    keycloakService.authenticated = false;
                }

                keycloakService.token = _kc?.token || null;
                setAuthTokenProvider(() => _kc?.token || null);

                _initialized = true;
            } catch (e) {
                console.error("Keycloak init failed:", e);
                keycloakService.enabled = false;
                _initialized = true;
            }
        })();

        return _initPromise;
    },

    async login() {
        if (!_kc) return;
        await _kc.login({ redirectUri: window.location.href });
    },

    async logout() {
        if (!_kc) return;
        await _kc.logout({ redirectUri: window.location.href });
    },
});
