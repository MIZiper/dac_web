<script lang="ts">
    import {
        Button,
        Col,
        Dropdown,
        DropdownMenu,
        DropdownToggle,
        Input,
        Row,
    } from "@sveltestrap/sveltestrap";
    import { keycloakService } from "../utils/KeycloakService.svelte";

    let signature = $state("");
    let isOpen = $state(false);

    let {
        onSaveProject,
        projectTitle = "",
    }: {
        onSaveProject: (
            hashed_signature: string,
            title: string,
            saveAs: boolean,
        ) => void;
        projectTitle?: string;
    } = $props();

    let title = $state("");

    $effect(() => {
        title = projectTitle;
    });

    function doSave(saveAs: boolean) {
        if (onSaveProject) {
            onSaveProject(
                keycloakService.enabled ? "" : signature,
                title,
                saveAs,
            );
        }
        isOpen = false;
    }
</script>

<Dropdown direction="start" nav inNavbar bind:isOpen>
    <DropdownToggle caret nav>Save</DropdownToggle>
    <DropdownMenu>
        <div style="margin: 5px;">
            {#if keycloakService.enabled}
                {#if keycloakService.authenticated}
                    <p>
                        Signed in as <b>{keycloakService.username}</b>
                    </p>
                {:else}
                    <Button
                        color="primary"
                        onclick={() => keycloakService.login()}
                    >
                        Login to save
                    </Button>
                {/if}
            {:else}
                <Input
                    type="password"
                    placeholder="Enter your signature"
                    bind:value={signature}
                />
            {/if}

            <p class="mt-2" style="width: 400px; text-wrap-mode: wrap;">
                {#if keycloakService.enabled}
                    <b>Save and identity</b> <br />
                    One analysis project can only be overwritten by the same user.
                    If you are not the original creator, a new project id will be
                    created.
                {:else}
                    <b>Save and signature</b> <br />
                    One analysis project can only be overwritten with same signature.
                    If signature not matching, a new project id will be created.
                    <br />
                    Signature is hashed, no raw value stored.
                {/if}
            </p>
            {#if !keycloakService.enabled || keycloakService.authenticated}
                <Row>
                    <Col>
                        <Input placeholder="Project title" bind:value={title} />
                    </Col>
                    <Col xs="auto" class="px-0">
                        <Button color="primary" onclick={() => doSave(false)}
                            >Save</Button
                        >
                    </Col>
                    <Col xs="auto">
                        <Button color="secondary" onclick={() => doSave(true)}
                            >Save As</Button
                        >
                    </Col>
                </Row>
            {/if}
        </div>
    </DropdownMenu>
</Dropdown>
