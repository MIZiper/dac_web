import { createRouter } from "sv-router";
import HomePage from "./pages/HomePage.svelte";
import MainPage from "./pages/MainPage.svelte";
import YamlEditor from "./lib/YamlEditor.svelte";

export const { p, navigate, isActive, route } = createRouter({
    '/': HomePage,
    '/projects/:id': MainPage,
    '/dev-test': YamlEditor,
})
