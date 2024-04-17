<template>
  <div :class="classModifiers">
    <shortened-link
      class="shortened-links-list__link"
      v-for="item in items"
      :url="item.url"
      :source="item.source"
    >
    </shortened-link>
  </div>
</template>

<script src="./shortened-links-list.js"></script>
<style src="./shortened-links-list.scss" lang="scss"></style>
