import { useLoaderStore } from "@/stores/loader";

const interceptorRequestSetup = (config) => {
  const loader = useLoaderStore();
  loader.incrLoaderCounter();
  config.loadingGlobalStarted = true;
  return config;
};

const interceptorRequestError = (error) => {
  return Promise.reject(error);
};

export { interceptorRequestSetup, interceptorRequestError };
