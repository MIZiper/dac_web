<script lang="ts">
    import {
        Button,
        Input,
        Modal,
        ModalBody,
        ModalFooter,
        ModalHeader,
    } from "@sveltestrap/sveltestrap";
    import type { TaskBaseProps } from "./TaskRouter.svelte";
    import { onMount } from "svelte";

    let { config_in, onTaskDone }: TaskBaseProps = $props();

    let isOpen = $state(false);
    let name = $state("");

    function onSave() {
        const config_out = { name: name };
        isOpen = false;
        onTaskDone(config_out);
    }

    onMount(() => {
        name = config_in["name"];
        isOpen = true;
    });
</script>

<Modal {isOpen}>
    <ModalHeader>Action Name Editor</ModalHeader>
    <ModalBody>
        <Input type="text" bind:value={name} />
    </ModalBody>
    <ModalFooter>
        <Button color="primary" onclick={onSave}>Ok</Button>
        <Button
            color="secondary"
            onclick={() => {
                isOpen = false;
                onTaskDone(null);
            }}>Cancel</Button
        >
    </ModalFooter>
</Modal>
