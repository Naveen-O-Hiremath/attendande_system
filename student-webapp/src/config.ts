// Backend origin. Must be this machine's LAN IP (not "localhost") so a phone
// on the same Wi-Fi, browsing to this webapp, can also reach the API.
// Update if the machine's IP changes networks.
export const API_ORIGIN = 'http://192.168.1.5:8000';
export const API_BASE_URL = `${API_ORIGIN}/api/v1`;
