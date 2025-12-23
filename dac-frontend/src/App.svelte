<script lang="ts">
  import { Router } from "sv-router";
  import "./router.ts";
  import { navTeleport } from "./utils/NavibarSnippet.svelte";

  import {
    Nav,
    Navbar,
    NavbarBrand,
    NavItem,
    NavLink,
    Styles,
  } from "@sveltestrap/sveltestrap";
</script>

<Styles />

<main>
  <Navbar style="background-color:whitesmoke;">
    <NavbarBrand>DAC analysis frame</NavbarBrand>
    <Nav>
      {#if navTeleport.snippet}
        {@render navTeleport.snippet()}
      {/if}
      <NavItem>
        <NavLink href="/projects/new">New Project</NavLink>
      </NavItem>
    </Nav>
  </Navbar>

  <Router />
</main>

<style>
</style>
