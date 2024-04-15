import axios from "axios";

const host_port = "localhost:5000";
const base_url = "http://" + host_port + "/"

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

export const mpl_ws = "ws://" + host_port + "/mpl";
export const mpl_js = base_url + "mpl/mpl.js";