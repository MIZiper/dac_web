<template>
    <v-menu v-model="menu" :close-on-content-click="false" location="bottom">
        <template v-slot:activator="{ props }">
            <v-btn title="Save project" v-bind="props">
                <v-icon>mdi-content-save</v-icon>
            </v-btn>
        </template>

        <v-card width="370">
            <v-row class="ma-0">
                <v-text-field :append-inner-icon="signature_visible ? 'mdi-eye-off' : 'mdi-eye'"
                    :type="signature_visible ? 'text' : 'password'" density="compact" placeholder="Enter your signature"
                    variant="outlined" @click:append-inner="signature_visible = !signature_visible" class="ma-1"
                    hide-details="auto" v-model="signature"></v-text-field>
                <v-btn class="ma-1" color="primary" @click="saveProject()">
                    Save
                </v-btn>
            </v-row>
            <v-card-text>
                <b>Save and signature</b> <br />
                One analysis project can only be overwritten with same signature.
                If signature not matching, a new project id will be created. <br />
                Signature is hashed, no raw value stored.
                <br /> <br />
                <b>Publish</b> maintains featured projects,
                which can be loaded by welcome screen browsing.
                Publish is not mandatory for saving.
            </v-card-text>

            <v-divider></v-divider>

            <v-text-field density="compact" placeholder="Publishing name" variant="outlined" class="ma-1"
                hide-details="auto" v-model="publish_name"></v-text-field>
            <v-btn color="primary" variant="text" block :disabled="nok4publish" @click="saveProject(publish_name)">
                Save & Publish
            </v-btn>
        </v-card>
    </v-menu>
</template>

<script>
import { ax_api } from '@/utils';
import Hashes from 'jshashes';
import { project_prefix } from '@/utils';

const sha1 = new Hashes.SHA1();

export default {
    data: () => ({
        menu: false,
        signature_visible: false,

        publish_name: "",
        signature: "",
    }),
    computed: {
        signature_hash() {
            return sha1.hex(this.signature);
        },
        nok4publish() {
            return !this.publish_name; // `|| !this.signature` to force signature input
        }
    },
    methods: {
        saveProject(publish_name = "") {
            let pathname = window.location.pathname;
            let project_id = "";

            if (pathname.startsWith(project_prefix)) {
                project_id = pathname.substring(project_prefix.length);
            }

            let data = {
                signature: this.signature_hash,
                project_id: project_id,
            }
            if (publish_name !== "") {
                data["publish_name"] = publish_name
            }

            ax_api.post("/save", data).then(response => {
                console.log(response.data['message']);
                window.history.replaceState(null, null, project_prefix + response.data['project_id']);
                this.menu = false;
            }).catch(error => {
                console.error("There was an error saving project:", error);
            })
        }
    }
}
</script>