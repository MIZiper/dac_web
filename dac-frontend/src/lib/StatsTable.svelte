<script lang="ts">
    import {
        Modal,
        ModalBody,
        ModalHeader,
        Table,
    } from "@sveltestrap/sveltestrap";

    let title: string = $state("");
    let headers: Record<string, string[]> = $state({});
    let data: any[][] = $state([]);
    let isOpen: boolean = $state(false);

    function toggle() {
        isOpen = !isOpen;
    }

    export function set(
        newTitle: string,
        newHeaders: Record<string, string[]>,
        newData: any[][],
    ) {
        title = newTitle;
        headers = newHeaders;
        data = newData;
        isOpen = true;
    }
</script>

<Modal bind:isOpen {toggle} size="xl">
    <ModalHeader>{title}</ModalHeader>
    <ModalBody>
        <div class="x-scroll">
            <Table bordered>
                <thead>
                    <tr>
                        <th>#</th>
                        {#each headers["col"] as colname}
                            <th>{colname}</th>
                        {/each}
                    </tr>
                </thead>
                <tbody>
                    {#each data as row, r_idx}
                        <tr>
                            <th scope="row">{headers["row"][r_idx]}</th>
                            {#each row as cell}
                                <td>{cell}</td>
                            {/each}
                        </tr>
                    {/each}
                </tbody>
            </Table>
        </div>
    </ModalBody>
</Modal>

<style>
    .x-scroll {
        overflow-x: auto;
    }
</style>
