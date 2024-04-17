const KEYS = {
  SHORTENED_LINKS_HISTORY: "shortened-links-history",
};

const storage = (storage) => {
  const prefixKey = (name) => `zadanie-${name}`;

  const set = (key, value, ttlSeconds = null) => {
    const expiresAt = ttlSeconds
      ? (new Date().getTime() + ttlSeconds * 1000) / 1
      : null;
    const data = {
      value,
      expiresAt,
    };
    try {
      storage.setItem(prefixKey(key), JSON.stringify(data));
    } catch (e) {
      console.error(e);
    }
  };

  const get = (key, defaultValue = null, returnExpiresAt = false) => {
    try {
      const data = JSON.parse(storage.getItem(prefixKey(key)));
      if (data !== null) {
        if (data.expiresAt !== null && data.expiresAt < new Date().getTime()) {
          del(key);
        } else {
          if (returnExpiresAt) {
            return data;
          }
          return data.value;
        }
      }
    } catch (e) {
      del(key);
    }
    return defaultValue;
  };

  const del = (key) => {
    try {
      storage.removeItem(prefixKey(key));
    } catch (e) {
      console.error(e);
    }
  };

  return {
    set,
    get,
    del,
  };
};

const ls = storage(window.localStorage);
const ss = storage(window.sessionStorage);

export { ls, ss, KEYS };
