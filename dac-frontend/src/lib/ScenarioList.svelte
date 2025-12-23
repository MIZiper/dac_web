<script lang="ts">
    import {
        Dropdown,
        DropdownItem,
        DropdownMenu,
        DropdownToggle,
    } from "@sveltestrap/sveltestrap";
    import type { ScenarioItem } from "../schema";

    let {
        scenarios,
        currentScenario = $bindable(),
    }: {
        scenarios: ScenarioItem[];
        currentScenario: ScenarioItem | null;
    } = $props();
</script>

<Dropdown nav inNavbar>
    <DropdownToggle caret nav>
        {currentScenario === null ? "Scenario X" : currentScenario.name}
    </DropdownToggle>
    <DropdownMenu>
        {#each scenarios as scenario}
            <DropdownItem onclick={(e) => (currentScenario = scenario)}
                >{scenario.name}</DropdownItem
            >
        {/each}
    </DropdownMenu>
</Dropdown>
