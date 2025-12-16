<script lang="ts">
  import { Router } from "sv-router";
  import "./router.ts";

  import {
    Nav,
    Navbar,
    NavbarBrand,
    NavItem,
    Styles,
  } from "@sveltestrap/sveltestrap";
</script>

<Styles />

<main>
  <Navbar style="background-color:whitesmoke;">
    <NavbarBrand>DAC analysis frame</NavbarBrand>
    <Nav>
      <NavItem>Save &amp; Publish</NavItem>
    </Nav>
  </Navbar>

  <Router />
</main>

<style>
</style>
