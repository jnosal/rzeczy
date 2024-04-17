import axios from "axios";
import config from "@/config";
import {
  interceptorRequestSetup,
  interceptorRequestError,
} from "./interceptors/request";
import {
  interceptorResponseSuccess,
  interceptorResponseError,
} from "./interceptors/response";

const http = axios.create({ baseURL: config.apiUrl });

http.interceptors.request.use(interceptorRequestSetup, interceptorRequestError);
http.interceptors.response.use(
  interceptorResponseSuccess,
  interceptorResponseError
);

export default http;
