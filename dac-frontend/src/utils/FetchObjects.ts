import axios from "axios";
import type { DACErrorInfo, DACErrorDetail } from "../schema";

export const app_prefix = "/app";
export const api_prefix = "/api";
const mpl_prefix = "/mpl";

export const FIG_NUM = 1;
export const SESSID_KEY = "dac-sess_id";
export const GCK_ID = 'global';
export const DEFAULT_NAME = '[New Context]';
export const app_mpl = `${app_prefix}${mpl_prefix}`; // /app/mpl
export const api_mpl = `${api_prefix}${mpl_prefix}`; // /api/mpl

let _getToken: (() => string | null) | null = null;

export function setAuthTokenProvider(provider: () => string | null) {
    _getToken = provider;
}

export const ax_api = axios.create({
    baseURL: api_prefix,
    responseType: "json",
    timeout: 30000,
    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
});

export const ax_app = axios.create({
    baseURL: app_prefix,
    responseType: "json",
    timeout: 30000,
    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
});

[ax_api, ax_app].forEach((instance) => {
    instance.interceptors.request.use((config) => {
        if (_getToken) {
            const token = _getToken();
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    });

    instance.interceptors.response.use(
        (response) => response,
        (error) => {
            const dacInfo: DACErrorInfo = {
                code: error.response?.status || 0,
                message: error.message || "Unknown error",
                detail: undefined,
            };

            const data = error.response?.data;
            if (data && typeof data === "object") {
                if (data.message) {
                    dacInfo.message = data.message;
                }
                if (data.code !== undefined) {
                    dacInfo.code = data.code;
                }
                if (data.detail && typeof data.detail === "object") {
                    dacInfo.detail = {
                        traceback: data.detail.traceback,
                        stderr: data.detail.stderr,
                        endpoint: data.detail.endpoint || error.config?.url,
                        timestamp: data.detail.timestamp,
                    } as DACErrorDetail;
                }
            }

            error._dacInfo = dacInfo;
            return Promise.reject(error);
        },
    );
});
