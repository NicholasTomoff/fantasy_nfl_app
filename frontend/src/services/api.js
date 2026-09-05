import axios from "axios";

// Read from Vite environment or fallback to relative "/api"
const API_BASE = import.meta.env.VITE_API_BASE_URL || "";


// Use API_BASE for fetch calls
export const apiFetch = async (endpoint, options = {}) => {
  const token = localStorage.getItem("token"); // Or from your auth context/provider

  const fullUrl = `${API_BASE}${endpoint}`;
  console.log(`🌐 FETCH: ${fullUrl}`);

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  console.log("📤 Headers:", headers);

  const res = await fetch(fullUrl, {
    ...options,
    headers,
  });

  return res;
};



// Axios instance with baseURL set to relative /api path
const axiosInstance = axios.create({
  baseURL: API_BASE,
});

// Automatically attach token if available
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// -------------------- API FUNCTIONS --------------------

export const fetchPlayersByPosition = async (position) => {
  try {
    const response = await axiosInstance.get(`/api/players/${position}`);
    return response.data.players;
  } catch (error) {
    console.error("Error fetching players:", error);
    return [];
  }
};

export const getLeagueDetails = async (id) => {
  const response = await axiosInstance.get(`/api/leagues/${id}`);
  return response.data;
};

export const joinLeague = async (id) => {
  const response = await axiosInstance.post(`/api/leagues/${id}/join`);
  return response.data;
};

// -------------------- SEASON CHECK-IN --------------------
// league_members stays the permanent roster (history is preserved even for
// members who sit a season out); these endpoints drive per-season "are you in?".

export const getSeasonRoster = async (leagueId, seasonYear) => {
  const response = await axiosInstance.get(
    `/api/leagues/${leagueId}/season/${seasonYear}/roster`
  );
  return response.data;
};

export const setMySeasonStatus = async (leagueId, seasonYear, status) => {
  const response = await axiosInstance.post(
    `/api/leagues/${leagueId}/season/${seasonYear}/me`,
    { status }
  );
  return response.data;
};

export const setMemberSeasonStatus = async (leagueId, seasonYear, userId, status) => {
  const response = await axiosInstance.post(
    `/api/leagues/${leagueId}/season/${seasonYear}/member/${userId}/status`,
    { status }
  );
  return response.data;
};

export const openSeason = async (leagueId, seasonYear) => {
  const response = await axiosInstance.post(
    `/api/leagues/${leagueId}/season/${seasonYear}/open`
  );
  return response.data;
};

export const generateInviteLink = async (id) => {
  try {
    const response = await axiosInstance.post(`/api/invites/generate-invite/${id}`);
    return response.data;
  } catch (error) {
    console.error("generateInviteLink error:", error.response || error.message || error);
    throw error;
  }
};
