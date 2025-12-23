import axios from "axios";

const app_prefix = "/app";
const api_prefix = "/api";
const mpl_prefix = "/mpl";

export const FIG_NUM = 1;
export const SESSID_KEY = "dac-sess_id";
export const GCK_ID = 'global';
export const DEFAULT_NAME = '[New Context]';
export const app_mpl = `${app_prefix}${mpl_prefix}`; // /app/mpl
export const api_mpl = `${api_prefix}${mpl_prefix}`; // /api/mpl

export const ax_api = axios.create({
    baseURL: api_prefix,
    responseType: "json",
    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
});

export const ax_app = axios.create({
    baseURL: app_prefix,
    responseType: "json",
    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
});