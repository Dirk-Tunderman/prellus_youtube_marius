import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/**
 * Extract YouTube ID from various YouTube URL formats
 *
 * @param {string} url - YouTube URL
 * @returns {string|null} - YouTube video ID or null if not valid
 */
export const extractYoutubeId = (url) => {
  if (!url) return null;

  // Match for standard YouTube URLs
  // Examples:
  // - https://www.youtube.com/watch?v=dQw4w9WgXcQ
  // - https://youtu.be/dQw4w9WgXcQ
  // - https://youtube.com/watch?v=dQw4w9WgXcQ&feature=share
  const regExp =
    /^.*(?:(?:youtu\.be\/|v\/|vi\/|u\/\w\/|embed\/|shorts\/)|(?:(?:watch)?\?v(?:i)?=|\&v(?:i)?=))([^#\&\?]*).*/;
  const match = url.match(regExp);

  return match && match[1] ? match[1] : null;
};

/**
 * Format ISO date string to a more readable format
 *
 * @param {string} isoDate - ISO date string
 * @returns {string} - Formatted date string
 */
export const formatDate = (isoDate) => {
  if (!isoDate) return "Unknown date";

  try {
    const date = new Date(isoDate);

    // Check if date is valid
    if (isNaN(date.getTime())) {
      return "Invalid date";
    }

    // Format: March 30, 2025 14:30
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch (error) {
    console.error("Error formatting date:", error);
    return "Error formatting date";
  }
};
