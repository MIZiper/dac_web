import axios from "axios";

const host_port = "localhost:5000";
const base_url = "http://" + host_port + "/"
export const FIG_NUM = 1;
export const mpl_urn = host_port + "/mpl"

export const ax_base = axios.create({
    baseURL: base_url,
    responseType: "json",
    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
});

export const ax_project = axios.create({
    baseURL: base_url, // + "projects/xxxx-yyyy-zzzz/"
    responseType: "json",
    headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
    },
});