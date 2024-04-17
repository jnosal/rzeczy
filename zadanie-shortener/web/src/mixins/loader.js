import { mapActions, mapState } from "pinia";
import { useLoaderStore } from "@/stores/loader";
import appLoader from "@/components/app/components/app-loader/app-loader.vue";

export default {
  components: {
    appLoader,
  },
  computed: {
    ...mapState(useLoaderStore, ["loaderCounter"]),
    isLoading() {
      return this.loaderCounter > 0;
    },
  },
  methods: {
    ...mapActions(useLoaderStore, ["incrLoaderCounter", "decrLoaderCounter"]),
    loadingStart() {
      this.incrLoaderCounter();
    },
    loadingEnd() {
      setTimeout(() => {
        this.decrLoaderCounter();
      }, 100);
    },
  },
};
