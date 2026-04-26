import type { Snippet } from "svelte";

export const navTeleport: {
    snippet: Snippet | null
} = $state({
    snippet: null
});