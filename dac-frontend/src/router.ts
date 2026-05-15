import { createRouter } from "sv-router";
import HomePage from "./pages/HomePage.svelte";
import MainPage from "./pages/MainPage.svelte";
import YamlEditor from "./lib/YamlEditor.svelte";
import DesktopPage from "./pages/DesktopPage.svelte";

export const router = createRouter({
    '/': HomePage,
    '/projects/:id': MainPage,
    '/desktop': DesktopPage,
    '/dev-test': YamlEditor,
})
