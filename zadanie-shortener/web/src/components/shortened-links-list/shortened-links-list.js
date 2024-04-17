import shortenedLink from "@/components/shortened-link/shortened-link.vue";

export default {
  components: { shortenedLink },
  props: {
    items: {
      type: Array,
      required: true,
    },
  },
  computed: {
    classModifiers() {
      return {
        "shortened-links-list": true,
        "shortened-links-list--one": this.items.length === 1,
      };
    },
  },
};
