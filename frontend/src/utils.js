import axios from "axios";

const app_prefix = "/app";
const api_prefix = "/api";
const mpl_prefix = "/mpl";
export const project_prefix = "/projects/";

export const FIG_NUM = 1;
export const SESSID_KEY = "dac-sess_id";
export const mpl_urn = `${app_prefix}${mpl_prefix}`; // /app/mpl

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