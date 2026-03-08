<script lang="ts">
  import { Router } from "sv-router";
  import { router } from "./router";
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
  setContext("router", router);
  import logo from "./assets/logo.png";
</script>

<Styles />

<main>
  <Navbar style="background-color:whitesmoke;">
    <NavbarBrand target="_blank">
      <img src={logo} alt="DAC logo" height="36px"/>
      DAC analysis frame
    </NavbarBrand>
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
