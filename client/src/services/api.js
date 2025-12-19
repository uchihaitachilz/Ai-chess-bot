/**
 * API service for communicating with the backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Send a move to the backend and get the engine's response.
 * 
 * @param {string} fen - Current board position in FEN notation
 * @param {string} move - Move in UCI format (e.g., "e2e4")
 * @returns {Promise<Object>} Response with engineMove, evaluation, and commentary
 */
export async function sendMove(fen, move) {
  const response = await fetch(`${API_BASE_URL}/api/move`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      fen,
      move,
    }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to process move')
  }

  return await response.json()
}

