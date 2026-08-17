// Backend origin, derived from whatever host the browser used to load this
// page — works unchanged whether that's "localhost" (same machine) or a LAN
// IP (phone on Wi-Fi), and needs no editing when the machine's IP changes.
export const API_ORIGIN = `http://${window.location.hostname}:8000`;
export const API_BASE_URL = `${API_ORIGIN}/api/v1`;
