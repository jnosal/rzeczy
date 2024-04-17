<template>
  <button :class="classModifiers" :disabled="disabled">
    <slot></slot>
  </button>
</template>

<script src="./z-button.js"></script>
<style src="./z-button.scss" lang="scss"></style>
