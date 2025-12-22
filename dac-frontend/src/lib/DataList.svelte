<script lang="ts">
    import {
        Button,
        Card,
        CardBody,
        CardHeader,
        CardTitle,
        Col,
        Icon,
        ListGroup,
        ListGroupItem,
        Row,
    } from "@sveltestrap/sveltestrap";
    import type { DataItem } from "../schema";

    let data: DataItem[] = $state([]);
</script>

<Card>
    <CardHeader>
        <Row>
<Col>
            <CardTitle>Data</CardTitle>
</Col>
<Col xs="auto">
    <Button><Icon name="trash" /></Button>
</Col>
        </Row>
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
