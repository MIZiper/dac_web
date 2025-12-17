<script lang="ts">
    import { ListGroup, ListGroupItem } from "@sveltestrap/sveltestrap";
    import type { DataItem } from "../schema";

    let data: DataItem[] = $state([]);
</script>

<ListGroup>
    {#each data as datum (datum.uuid)}
        <ListGroupItem>
            {datum.name}
        </ListGroupItem>
    {/each}
</ListGroup>

<!-- Menu -->