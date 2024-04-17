import { defineStore } from "pinia";
import { ls, KEYS } from "@/services/storage";

const HISTORY_ITEMS_TO_STORE_SIZE = 3;

export const useShortenerStore = defineStore("shortener", {
  state: () => ({
    historyLinks: ls.get(KEYS.SHORTENED_LINKS_HISTORY, []),
  }),
  actions: {
    updateHistory(item) {
      const current = ls.get(KEYS.SHORTENED_LINKS_HISTORY, []);
      const itemDoesNotExistInStorage =
        current.filter((i) => i.url === item.url).length === 0;

      if (itemDoesNotExistInStorage) {
        this.historyLinks = [item, ...this.historyLinks].slice(
          0,
          HISTORY_ITEMS_TO_STORE_SIZE
        );
        ls.set(KEYS.SHORTENED_LINKS_HISTORY, this.historyLinks);
      }
    },
  },
});
