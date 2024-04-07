import axios from "axios";

const base_url = "http://localhost:5000/"

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