import http from "@/services/http";

export default {
  async postShortenUrl(payload) {
    const { data } = await http.post("s/shorten", payload);
    return data;
  },
};
