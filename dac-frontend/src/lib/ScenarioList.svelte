<script lang="ts">
    import {
        Dropdown,
        DropdownItem,
        DropdownMenu,
        DropdownToggle,
    } from "@sveltestrap/sveltestrap";
    import type { ScenarioItem } from "../schema";

    let currentScenario: ScenarioItem | null = $state(null);
    let scenarios: ScenarioItem[] = $state([]);
</script>

<Dropdown nav inNavbar>
    <DropdownToggle caret nav>
        {currentScenario === null ? "Scenario X" : currentScenario.name}
    </DropdownToggle>
    <DropdownMenu>
        {#each scenarios as scenario}
            <DropdownItem>{scenario.name}</DropdownItem>
        {/each}
    </DropdownMenu>
</Dropdown>
