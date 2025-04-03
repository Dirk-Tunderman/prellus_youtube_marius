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
 * @param {string} dateInput - Date string in various formats
 * @returns {string} - Formatted date string
 */
export const formatDate = (dateInput) => {
  if (!dateInput) return "Unknown date";

  try {
    console.log("Formatting date input:", dateInput, "Type:", typeof dateInput);
    
    // If it's already in a formatted string like "April 01, 2025 14:42"
    // that includes month name, day, and year, just return it
    if (typeof dateInput === 'string' && 
        /[A-Za-z]+\s\d+,?\s\d{4}/.test(dateInput)) {
      console.log("Detected pre-formatted date string, returning as-is");
      return dateInput;
    }
    
    // If it's a timestamp object string from the API: "{'start': 0.06, 'end': 1958.419}"
    if (typeof dateInput === 'string' && 
        dateInput.includes("'start'") && 
        dateInput.includes("'end'")) {
      console.log("Detected timestamp object string");
      
      // In this case, let's extract the date from the project ID if available
      const projectId = document.querySelector('[data-project-id]')?.getAttribute('data-project-id');
      console.log("Project ID from DOM:", projectId);
      
      if (projectId && projectId.includes('_') && projectId.split('_').length >= 3) {
        // Extract date parts from the project ID
        const parts = projectId.split('_');
        if (parts.length >= 3) {
          const datePart = parts[1]; // YYYYMMDD
          const timePart = parts[2]; // HHMMSS
          
          if (datePart.length === 8 && timePart.length === 6) {
            const year = datePart.substring(0, 4);
            const month = datePart.substring(4, 6);
            const day = datePart.substring(6, 8);
            
            const hour = timePart.substring(0, 2);
            const minute = timePart.substring(2, 4);
            
            const date = new Date(`${year}-${month}-${day}T${hour}:${minute}:00`);
            if (!isNaN(date.getTime())) {
              const formatted = date.toLocaleString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              });
              console.log("Formatted date from project ID:", formatted);
              return formatted;
            }
          }
        }
      }
      
      return "Date not available";
    }
    
    // Handle ISO date strings and other formats
    const date = new Date(dateInput);

    // Check if date is valid
    if (isNaN(date.getTime())) {
      console.error("Invalid date parsed from:", dateInput);
      return "Invalid date";
    }

    // Format: March 30, 2025 14:30
    const formatted = date.toLocaleString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
    console.log("Formatted standard date:", formatted);
    return formatted;
  } catch (error) {
    console.error("Error formatting date:", error, "Input was:", dateInput);
    return "Error formatting date";
  }
};
