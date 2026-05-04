<script lang="ts">
  import { Router } from "sv-router";
  import { router } from "./router";
  import { navTeleport } from "./utils/NavibarSnippet.svelte";
  import { keycloakService } from "./utils/KeycloakService.svelte";

  import {
    Nav,
    Navbar,
    NavbarBrand,
    NavItem,
    NavLink,
    Styles,
  } from "@sveltestrap/sveltestrap";
  import { setContext, onMount } from "svelte";
  setContext("router", router);
  import logo from "./assets/logo.png";

  onMount(() => {
    keycloakService.init();
  });
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
      {#if keycloakService.enabled}
        {#if keycloakService.authenticated}
          <NavItem>
            <NavLink disabled>{keycloakService.username}</NavLink>
          </NavItem>
          <NavItem>
            <NavLink href="#"
              onclick={(e: Event) => { e.preventDefault(); keycloakService.logout(); }}>
              Logout
            </NavLink>
          </NavItem>
        {:else}
          <NavItem>
            <NavLink href="#"
              onclick={(e: Event) => { e.preventDefault(); keycloakService.login(); }}>
              Login
            </NavLink>
          </NavItem>
        {/if}
      {/if}
    </Nav>
  </Navbar>

  <Router />
</main>

<style>
</style>
