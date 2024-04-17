import { defineStore } from "pinia";

export const useLoaderStore = defineStore("loader", {
  state: () => ({
    loaderCounter: 0,
  }),
  actions: {
    incrLoaderCounter() {
      this.loaderCounter += 1;
    },
    decrLoaderCounter() {
      this.loaderCounter -= 1;
    },
  },
});
