import { mapActions, mapState } from "pinia";
import shortenedLink from "@/components/shortened-link/shortened-link.vue";
import shortenedLinksList from "@/components/shortened-links-list/shortened-links-list.vue";
import zButton from "@/components/generic/z-button/z-button.vue";
import zInput from "@/components/generic/z-input/z-input.vue";
import { useShortenerStore } from "@/stores/shortener";
import api from "@/services/api";
import { isValidUrl } from "@/helpers/validators";

export default {
  components: {
    shortenedLink,
    shortenedLinksList,
    zButton,
    zInput,
  },
  data() {
    return {
      result: null,
      fields: {
        link: null,
      },
    };
  },
  computed: {
    ...mapState(useShortenerStore, ["historyLinks"]),
    isValid() {
      return !!this.fields.link && isValidUrl(this.fields.link);
    },
  },
  methods: {
    ...mapActions(useShortenerStore, ["updateHistory"]),
    async shortenLink() {
      const payload = {
        url: this.fields.link,
      };
      const data = await api.shortener.postShortenUrl(payload);
      this.result = data.result;
      this.updateHistory({
        source: this.fields.link,
        url: this.result,
      });
    },
  },
};
