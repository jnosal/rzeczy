import { useLoaderStore } from "@/stores/loader";

const interceptorResponseSuccess = (response) => {
  const { config } = response;

  if (config.loadingGlobalStarted) {
    const loader = useLoaderStore();
    loader.decrLoaderCounter();
  }
  return response;
};

const interceptorResponseError = (error) => {
  if (error.config.loadingGlobalStarted) {
    const loader = useLoaderStore();
    loader.decrLoaderCounter();
  }
  return Promise.reject(error);
};

export { interceptorResponseSuccess, interceptorResponseError };
