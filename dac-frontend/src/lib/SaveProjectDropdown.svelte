<script lang="ts">
    import {
        Button,
        Col,
        Dropdown,
        DropdownItem,
        DropdownMenu,
        DropdownToggle,
        Input,
        Label,
        Row,
    } from "@sveltestrap/sveltestrap";

    let signature = $state("");
    let publish_name = $state("");
    let isOpen = $state(false);

    let {
        onSaveProject,
    }: {
        onSaveProject: (hashed_signature: string, publish_name: string) => void;
    } = $props();
    function saveProject() {
        if (onSaveProject) {
            onSaveProject(signature, "");
        }
        isOpen = false;
    }
    function publishProject() {
        if (onSaveProject) {
            onSaveProject(signature, publish_name);
        }
        isOpen = false;
    }
</script>

<Dropdown direction="start" nav inNavbar bind:isOpen>
    <DropdownToggle caret nav>Save</DropdownToggle>
    <DropdownMenu>
        <div style="margin: 5px;">
            <Row>
                <Col>
                    <Input
                        type="password"
                        placeholder="Enter your signature"
                        bind:value={signature}
                    />
                </Col>
                <Col xs="auto">
                    <Button onclick={saveProject}>Save</Button>
                </Col>
            </Row>
            <p style="width: 400px; text-wrap-mode: wrap;">
                <b>Save and signature</b> <br />
                One analysis project can only be overwritten with same signature.
                If signature not matching, a new project id will be created.
                <br />
                Signature is hashed, no raw value stored.
                <br /> <br />
                <b>Publish</b> maintains featured projects, which can be loaded by
                welcome screen browsing. Publish is not mandatory for saving.
            </p>
            <Row>
                <Col>
                    <Input
                        placeholder="Publishing name"
                        bind:value={publish_name}
                    />
                </Col>
                <Col xs="auto">
                    <Button
                        disabled={publish_name === ""}
                        onclick={publishProject}>Save & Publish</Button
                    >
                </Col>
            </Row>
        </div>
    </DropdownMenu>
</Dropdown>
