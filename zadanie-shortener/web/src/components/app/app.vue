<template>
  <div class="app">
    <app-loader v-if="isLoading"></app-loader>
    <router-view v-slot="{ Component }">
      <transition name="z-transition-fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script src="./app.js"></script>
<style src="./app.scss" lang="scss"></style>
