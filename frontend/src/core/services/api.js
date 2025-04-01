import axios from "axios";
import { toast } from "sonner";

// API URL
const API_URL = "http://localhost:5001/api";

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 5000, // 5 seconds timeout
});

// Helper function to handle API requests with consistent error handling
export const apiRequest = async (requestFn) => {
  try {
    console.log("[API] Making API request...");
    const response = await requestFn();
    console.log("[API] Request successful:", response.config.url);
    console.log("[API] Response status:", response.status);
    console.log("[API] Response data:", response.data);
    return response.data;
  } catch (error) {
    console.error("[API] Request failed:", error);
    console.error("[API] Error details:", {
      message: error.message,
      status: error.response?.status,
      data: error.response?.data,
      url: error.config?.url,
    });
    // Use toast from components/ui/sonner for error notifications
    toast.error(`API Error: ${error.response?.data?.message || error.message}`);
    throw error;
  }
};

export default api;
