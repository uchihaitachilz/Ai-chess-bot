import { useState } from 'react'
import ChessBoard from './components/ChessBoard'
import Commentary from './components/Commentary'
import { Chess } from 'chess.js'

function App() {
  const [game, setGame] = useState(new Chess())
  const [fen, setFen] = useState(game.fen())
  const [commentary, setCommentary] = useState('')
  const [evaluation, setEvaluation] = useState(null)
  const [gameOver, setGameOver] = useState(false)

  const handleMove = async (move) => {
    if (gameOver) return

    try {
      // Validate move locally first
      const gameCopy = new Chess(fen)
      const moveObj = gameCopy.move(move)
      
      if (!moveObj) {
        return { valid: false }
      }

      // Update game state IMMEDIATELY with player's move (no waiting)
      const newGame = new Chess(fen)
      newGame.move(move)
      setGame(newGame)
      setFen(newGame.fen())
      
      // Now make backend call in the background (non-blocking)
      fetch('http://localhost:8000/api/move', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fen: fen,
          move: move,
        }),
      })
      .then(response => {
        if (!response.ok) {
          return response.json().then(error => {
            throw new Error(error.detail || 'Failed to process move')
          })
        }
        return response.json()
      })
      .then(data => {
        // Show commentary when it arrives
        setCommentary(data.commentary || '')
        setEvaluation(data.evaluation || null)
        
        // Apply engine move after a short delay to animate it
        if (data.engineMove) {
          setTimeout(() => {
            const engineGame = new Chess(newGame.fen())
            engineGame.move(data.engineMove)
            setGame(engineGame)
            setFen(engineGame.fen())
            
            // Check if game is over after engine move
            if (engineGame.isGameOver()) {
              setGameOver(true)
              if (engineGame.isCheckmate()) {
                setCommentary('Fried the chicken! 🔥🐓 Checkmate! That\'s why you are the dummy!')
              } else if (engineGame.isDraw()) {
                setCommentary('Draw! Game over, kid.')
              }
            }
          }, 300) // Small delay to show player's move first
        }
      })
      .catch(error => {
        console.error('Move error:', error)
        setCommentary(`Error: ${error.message}`)
      })

      return { valid: true }
    } catch (error) {
      console.error('Move validation error:', error)
      return { valid: false }
    }
  }

  const resetGame = () => {
    const newGame = new Chess()
    setGame(newGame)
    setFen(newGame.fen())
    setCommentary('')
    setEvaluation(null)
    setGameOver(false)
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Clean Header Banner with Animation */}
        <div className="bg-gradient-to-r from-purple-500 via-purple-600 to-pink-500 rounded-lg shadow-2xl mb-6 py-8 px-6 animate-pulse hover:animate-none transition-all duration-300 hover:shadow-purple-500/50 hover:scale-[1.02]">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-3 tracking-tight animate-fade-in drop-shadow-lg">
              <span className="inline-block animate-bounce" style={{ animationDelay: '0s' }}>T</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.1s' }}>U</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.2s' }}>S</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.3s' }}>H</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.4s' }}>I</span>
              {' '}
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.5s' }}>C</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.6s' }}>H</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.7s' }}>E</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.8s' }}>S</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.9s' }}>S</span>
              {' '}
              <span className="inline-block animate-bounce" style={{ animationDelay: '1.0s' }}>B</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '1.1s' }}>O</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '1.2s' }}>T</span>
            </h1>
            <p className="text-white text-lg md:text-xl font-medium animate-fade-in-delay drop-shadow-md">
              Play against Tushar Anand
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Commentary Panel - Show First */}
          <div className="lg:col-span-1 lg:order-1">
            <Commentary
              commentary={commentary}
              evaluation={evaluation}
            />
          </div>

          {/* Chess Board */}
          <div className="lg:col-span-2 lg:order-2">
            <div className="bg-white rounded-lg shadow-2xl p-4 md:p-6">
              <ChessBoard
                position={fen}
                onMove={handleMove}
                gameOver={gameOver}
              />
              
              <div className="mt-4 flex justify-center gap-4">
                <button
                  onClick={resetGame}
                  className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-semibold"
                >
                  New Game
                </button>
                {gameOver && (
                  <span className="px-6 py-2 bg-gray-200 rounded-lg font-semibold text-gray-800">
                    Game Over
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

