import axios from "axios";

// API Base URL - using localhost for development
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Create axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(
      `🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`
    );
    return config;
  },
  (error) => {
    console.error("❌ Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.config.url}`, response.status);
    return response;
  },
  (error) => {
    console.error("❌ Response Error:", error.response?.status, error.message);
    return Promise.reject(error);
  }
);

// ============================================
// API FUNCTIONS
// ============================================

/**
 * Get Inventory Forecast
 * @param {number} limit - Number of products to fetch (default: 10)
 * @returns {Promise} API response with forecast data
 */
export const getInventoryForecast = async (limit = 10) => {
  try {
    const response = await api.get("/api/v1/inventory/forecast", {
      params: { limit },
    });
    return response.data;
  } catch (error) {
    console.error("Failed to fetch inventory forecast:", error);
    throw error;
  }
};

/**
 * Get Forecast for Specific Product
 * @param {string} productId - Product ID to fetch forecast for
 * @returns {Promise} API response with product forecast
 */
export const getProductForecast = async (productId) => {
  try {
    const response = await api.get("/api/v1/inventory/forecast", {
      params: { product_id: productId },
    });
    return response.data;
  } catch (error) {
    console.error("Failed to fetch product forecast:", error);
    throw error;
  }
};

/**
 * Calculate COD Risk Score
 * @param {Object} orderData - Order data for risk assessment
 * @returns {Promise} API response with risk score
 */
export const checkRiskScore = async (orderData) => {
  try {
    const response = await api.post("/api/v1/risk-score", orderData);
    return response.data;
  } catch (error) {
    console.error("Failed to check risk score:", error);
    throw error;
  }
};

/**
 * Health Check
 * @returns {Promise} API health status
 */
export const healthCheck = async () => {
  try {
    const response = await api.get("/health");
    return response.data;
  } catch (error) {
    console.error("Health check failed:", error);
    throw error;
  }
};

export default api;
