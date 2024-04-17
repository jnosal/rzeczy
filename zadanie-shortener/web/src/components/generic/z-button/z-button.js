export default {
  props: {
    variant: {
      type: String,
      default: "primary",
    },
    size: {
      type: String,
      default: "medium",
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    classModifiers() {
      return {
        "z-button": true,
        [`z-button--${this.size}`]: this.size,
        [`z-button--${this.variant}`]: this.variant,
      };
    },
  },
};
