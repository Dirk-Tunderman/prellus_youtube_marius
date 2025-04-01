/**
 * AI Models and Providers Registry
 *
 * This file serves as the central registry for all AI providers and models used in the application.
 * It follows the Configuration Registry pattern to centralize provider and model definitions.
 *
 * IMPORTANT: To add, remove, or modify providers and models, you only need to update this file.
 * All components will automatically use the updated information.
 *
 * HOW TO USE:
 *
 * 1. Adding a new provider:
 *    - Add a new object to the `providers` array with:
 *      - id: Unique identifier (used in API calls)
 *      - name: Display name
 *      - description: Description for the API key configuration page
 *
 * 2. Adding a new model:
 *    - Add a new object to the `models` array with:
 *      - value: Model identifier (used in API calls)
 *      - label: Display name
 *      - provider: The provider ID this model belongs to
 *
 * 3. Removing a provider or model:
 *    - Simply remove the corresponding object from the array
 *
 * 4. Modifying a provider or model:
 *    - Update the properties of the corresponding object
 *
 * EXAMPLE:
 *
 * // Adding a new provider
 * { id: "newprovider", name: "New Provider", description: "Description for New Provider." }
 *
 * // Adding a new model
 * { value: "new-model", label: "New Model", provider: "newprovider" }
 */

// Provider definitions
export const providers = [
  {
    id: "openai",
    name: "OpenAI",
    description: "Required for OpenAI models (GPT-4o).",
  },
  {
    id: "gemini",
    name: "Google Gemini",
    description:
      "Required for Google's Gemini models (Gemini 2.5 Pro, 2.0 Flash, etc.).",
  },
  {
    id: "anthropic",
    name: "Anthropic Claude",
    description:
      "Required for Anthropic's Claude models (Claude 3.7 Sonnet, 3.5 Haiku, etc.).",
  },
];

// Model definitions
export const models = [
  // OpenAI Models
  {
    value: "gpt-4o",
    label: "OpenAI GPT-4o",
    provider: "openai",
  },

  // Gemini Models
  {
    value: "gemini-2.5-pro-exp-03-25",
    label: "Google Gemini 2.5 Pro Exp",
    provider: "gemini",
  },
  {
    value: "gemini-2.0-flash",
    label: "Google Gemini 2.0 Flash",
    provider: "gemini",
  },
  {
    value: "gemini-2.0-flash-lite",
    label: "Google Gemini 2.0 Flash Lite",
    provider: "gemini",
  },

  // Anthropic Models
  {
    value: "claude-3-7-sonnet-20250219",
    label: "Anthropic Claude 3.7 Sonnet",
    provider: "anthropic",
  },
  {
    value: "claude-3-5-sonnet-20241022",
    label: "Anthropic Claude 3.5 Sonnet",
    provider: "anthropic",
  },
  {
    value: "claude-3-5-haiku-20241022",
    label: "Anthropic Claude 3.5 Haiku",
    provider: "anthropic",
  },
];

/**
 * Get a provider by its ID
 * @param {string} id - The provider ID
 * @returns {Object|undefined} The provider object or undefined if not found
 */
export const getProviderById = (id) =>
  providers.find((provider) => provider.id === id);

/**
 * Get all models for a specific provider
 * @param {string} providerId - The provider ID
 * @returns {Array} Array of model objects for the specified provider
 */
export const getModelsByProvider = (providerId) =>
  models.filter((model) => model.provider === providerId);

/**
 * Get all provider IDs
 * @returns {Array} Array of provider IDs
 */
export const getAllProviderIds = () => providers.map((provider) => provider.id);

/**
 * Get all unique provider IDs from the models array
 * @returns {Array} Array of unique provider IDs that have models
 */
export const getUniqueProviderIdsFromModels = () => [
  ...new Set(models.map((model) => model.provider)),
];
