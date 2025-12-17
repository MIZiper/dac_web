<script lang="ts">
    import { Icon, ListGroup, ListGroupItem } from "@sveltestrap/sveltestrap";
    import type { ActionItem } from "../schema";

    let actions: ActionItem[] = $state([]);
</script>

<ListGroup>
    {#each actions as action (action.uuid)}
    <ListGroupItem>
        <Icon name=""></Icon>
        {action.name}
    </ListGroupItem>
    {/each}
</ListGroup>