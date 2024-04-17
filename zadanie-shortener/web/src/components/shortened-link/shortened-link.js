export default {
  props: {
    source: {
      type: String,
      required: false,
    },
    url: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      copied: false,
      timeout: null,
    };
  },
  methods: {
    async copyToClipboard() {
      try {
        await navigator.clipboard.writeText(this.url);
        this.copied = true;
        setTimeout(() => {
          this.copied = false;
        }, 2500);
      } catch (err) {
        console.error(err);
      }
    },
  },
  beforeUnmount() {
    if (this.timeout) {
      clearTimeout(this.timeout);
    }
  },
};
