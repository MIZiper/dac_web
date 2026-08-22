import { createRouter } from "sv-router";
import HomePage from "./pages/HomePage.svelte";
import MainPage from "./pages/MainPage.svelte";
import YamlEditor from "./lib/YamlEditor.svelte";
import DesktopPage from "./pages/DesktopPage.svelte";
import ImportPage from "./pages/ImportPage.svelte";
import AdminPage from "./pages/AdminPage.svelte";

export const router = createRouter({
    '/': HomePage,
    '/projects/:id': MainPage,
    '/desktop': DesktopPage,
    '/import': ImportPage,
    '/admin': AdminPage,
    '/dev-test': YamlEditor,
})
