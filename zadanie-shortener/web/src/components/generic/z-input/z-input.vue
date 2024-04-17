<template>
  <div :class="classModifiers">
    <div class="z-input__label" v-if="!!$slots.label">
      <slot name="label"></slot>
    </div>
    <div class="z-input__box">
      <input
        class="z-input__input"
        :placeholder="placeholder"
        :type="type"
        :value="modelValue"
        :disabled="disabled"
        @input="$emit('update:modelValue', $event.target.value)"
      />
    </div>
  </div>
</template>

<script src="./z-input.js"></script>
<style src="./z-input.scss" lang="scss"></style>
