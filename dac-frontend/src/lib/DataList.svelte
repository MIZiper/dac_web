<script lang="ts">
    import {
        Card,
        CardBody,
        CardHeader,
        CardTitle,
        ListGroup,
        ListGroupItem,
    } from "@sveltestrap/sveltestrap";
    import type { DataItem } from "../schema";

    let data: DataItem[] = $state([]);
</script>

<Card>
    <CardHeader>
        <CardTitle>Data</CardTitle>
    </CardHeader>
    <CardBody>
        <ListGroup>
            {#each data as datum (datum.uuid)}
                <ListGroupItem>
                    {datum.name}
                </ListGroupItem>
            {/each}
        </ListGroup>
    </CardBody>
</Card>

<!-- Menu -->
