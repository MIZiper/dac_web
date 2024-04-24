import axios from "axios";

const host_port = "localhost:5000";

export const FIG_NUM = 1;
export const mpl_urn = host_port + "/app/mpl";
export const SESSID_KEY = "dac-sess_id";

export const ax_router = axios.create({
    baseURL: `http://${host_port}`,
    responseType: "json",
    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
});

export const ax_app = axios.create({
    baseURL: `http://${host_port}/app`,
    responseType: "json",
    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
});