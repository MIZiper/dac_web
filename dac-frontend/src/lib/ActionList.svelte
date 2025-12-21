<script lang="ts">
    import {
        Card,
        CardBody,
        CardHeader,
        CardTitle,
        Icon,
        ListGroup,
        ListGroupItem,
    } from "@sveltestrap/sveltestrap";
    import type { ActionItem } from "../schema";

    let actions: ActionItem[] = $state([]);
</script>

<Card>
    <CardHeader>
        <CardTitle>Action</CardTitle>
    </CardHeader>
    <CardBody>
        <ListGroup>
            {#each actions as action (action.uuid)}
                <ListGroupItem>
                    <Icon name=""></Icon>
                    {action.name}
                </ListGroupItem>
            {/each}
        </ListGroup>
    </CardBody>
</Card>
