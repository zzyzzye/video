// Token management functions
const TOKEN_KEY = 'video_token';
const REFRESH_TOKEN_KEY = 'video_refresh_token';

// Get token from localStorage
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

// Set token in localStorage
export function setToken(token) {
  return localStorage.setItem(TOKEN_KEY, token);
}

// Remove token from localStorage
export function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// Get refresh token from localStorage
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

// Set refresh token in localStorage
export function setRefreshToken(token) {
  return localStorage.setItem(REFRESH_TOKEN_KEY, token);
} 