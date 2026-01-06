<script lang="ts">
  import { Router } from "sv-router";
  import { route } from "./router";
  import { navTeleport } from "./utils/NavibarSnippet.svelte";

  import {
    Nav,
    Navbar,
    NavbarBrand,
    NavItem,
    NavLink,
    Styles,
  } from "@sveltestrap/sveltestrap";
  import { setContext } from "svelte";
  setContext("route", route);
</script>

<Styles />

<main>
  <Navbar style="background-color:whitesmoke;">
    <NavbarBrand target="_blank">DAC analysis frame</NavbarBrand>
    <Nav>
      {#if navTeleport.snippet}
        {@render navTeleport.snippet()}
      {/if}
      <NavItem>
        <NavLink href="/projects/new" target="_blank">New Project</NavLink>
      </NavItem>
    </Nav>
  </Navbar>

  <Router />
</main>

<style>
</style>
