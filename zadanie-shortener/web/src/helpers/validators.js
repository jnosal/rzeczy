export const isValidUrl = (urlString) => {
  const urlRegex =
    /^(?:(?:https?|ftp):\/\/)?(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)+[^\s]*$/i;
  return urlRegex.test(urlString);
};
