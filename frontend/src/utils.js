import axios from "axios";

const host_port = "localhost:5000";
export const site_prefix = ""; // "/dac"; //
const app_prefix = "/app"; // ""; //
const mpl_prefix = "/mpl";

export const FIG_NUM = 1;
export const SESSID_KEY = "dac-sess_id";
export const mpl_urn = `${host_port}${site_prefix}${app_prefix}${mpl_prefix}`; // http://localhost:5000/dac/app/mpl

export const ax_router = axios.create({
    baseURL: `http://${host_port}${site_prefix}`, // http://localhost:5000/dac
    responseType: "json",
    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
});

export const ax_app = axios.create({
    baseURL: `http://${host_port}${site_prefix}${app_prefix}`, // http://localhost:5000/dac/app
    responseType: "json",
    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
});