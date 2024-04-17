export default {
  props: {
    modelValue: {},
    variant: {
      type: String,
      default: "primary",
    },
    size: {
      type: String,
      default: "medium",
    },
    type: {
      type: String,
      default: "text",
    },
    placeholder: {
      type: String,
      default: "",
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    classModifiers() {
      return {
        "z-input": true,
        [`z-input--${this.size}`]: this.size,
        [`z-input--${this.variant}`]: this.variant,
      };
    },
  },
};
