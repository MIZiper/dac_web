import { createRouter } from "sv-router";
import HomePage from "./pages/HomePage.svelte";
import MainPage from "./pages/MainPage.svelte";

export const { p, navigate, isActive, route } = createRouter({
    '/': HomePage,
    '/dev-test': MainPage,
})
