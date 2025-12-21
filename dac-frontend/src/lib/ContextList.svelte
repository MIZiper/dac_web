<script lang="ts">
    import {
        Card,
        CardBody,
        CardHeader,
        CardTitle,
        Input,
    } from "@sveltestrap/sveltestrap";
    import type { DataItem } from "../schema";

    let contexts: DataItem[] = $state([]);
</script>

<Card>
    <CardHeader><CardTitle>Context</CardTitle></CardHeader>
    <CardBody>
        <Input type="select">
            {#each contexts as context (context.uuid)}
                <option>{context.name}</option>
            {/each}
        </Input>
    </CardBody>
</Card>
