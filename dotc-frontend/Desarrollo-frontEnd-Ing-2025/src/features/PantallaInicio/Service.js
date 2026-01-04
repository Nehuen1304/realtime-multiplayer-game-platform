import { getApiUrl } from '../../config/api.js';

/**
 * Sends a POST request to create a new game or resource.
 * @param {object} data - The data payload to send in the request body (e.g., player name, key).
 * @returns {Promise<object>} The JSON response body from the server.
 */
export const createPlayer = async (data) => {
  try {
    const response = await fetch(getApiUrl('/api/players'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // You might add an Authorization header here later
      },
      // Serialize the JS object 'data' into a JSON string for the body
      body: JSON.stringify(data), 
    });

    // Check if the response status is not successful (e.g., 4xx or 5xx)
    if (!response.ok) {
      // Throw an error with the status for better debugging in the calling component
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    // Parse the JSON body and return it
    const responseData = await response.json();
    return responseData;
    
  } catch (error) {
    // Log the error and re-throw a clearer error for the component to handle
    console.error("Error creating game:", error);
    throw new Error("Failed to connect to the game server or process the request.");
  }
};