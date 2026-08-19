// Backend origin, derived from whatever host the browser used to load this
// page — works unchanged whether that's "localhost" (same machine) or a LAN
// IP (phone on Wi-Fi), and needs no editing when the machine's IP changes.
//
// "localhost" is normalized to 127.0.0.1: on Windows, "localhost" can
// resolve to the IPv6 loopback first, which an unrelated process/container
// may also occupy on this port. 127.0.0.1 is unambiguous IPv4 and always
// reaches this backend.
const host = window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
export const API_ORIGIN = `http://${host}:8000`;
export const API_BASE_URL = `${API_ORIGIN}/api/v1`;
