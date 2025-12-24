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
        currentScenario,
        onSwitchScenario,
    }: {
        scenarios: ScenarioItem[];
        currentScenario: ScenarioItem | null;
        onSwitchScenario: (s: ScenarioItem) => void;
    } = $props();
</script>

<Dropdown nav inNavbar>
    <DropdownToggle caret nav>
        {currentScenario === null ? "Scenario X" : currentScenario.name}
    </DropdownToggle>
    <DropdownMenu>
        {#each scenarios as scenario}
            <DropdownItem
                onclick={(e) => {
                    if (scenario.name !== currentScenario?.name) {
                        onSwitchScenario(scenario);
                    }
                }}>{scenario.name}</DropdownItem
            >
        {/each}
    </DropdownMenu>
</Dropdown>
