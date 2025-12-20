import { useState, useEffect } from 'react'
import ChessBoard from './components/ChessBoard'
import Commentary from './components/Commentary'
import PlayerInfo from './components/PlayerInfo'
import ImproveWithTushi from './components/ImproveWithTushi'
import { Chess } from 'chess.js'

function App() {
  const [playerColor, setPlayerColor] = useState(null) // 'w' or 'b', null means not selected
  const [game, setGame] = useState(new Chess())
  const [fen, setFen] = useState(game.fen())
  const [commentary, setCommentary] = useState('')
  const [evaluation, setEvaluation] = useState(null)
  const [prevEvaluation, setPrevEvaluation] = useState(null) // Track previous evaluation for improvement tips
  const [lastPlayerMove, setLastPlayerMove] = useState(null) // Track last player move
  const [badMoveCount, setBadMoveCount] = useState(0) // Counter for bad moves to show tips every 2-3 moves
  const [gameOver, setGameOver] = useState(false)
  const [capturedWhitePieces, setCapturedWhitePieces] = useState([])
  const [capturedBlackPieces, setCapturedBlackPieces] = useState([])
  const [premove, setPremove] = useState(null) // Store premove: { from, to }

  // Track captured pieces by comparing current board to starting position
  useEffect(() => {
    const updateCapturedPieces = () => {
      try {
        const currentGame = new Chess(fen)
        const board = currentGame.board()
        
        // Starting piece counts
        const initialCounts = {
          'P': 8, 'R': 2, 'N': 2, 'B': 2, 'Q': 1, // White
          'p': 8, 'r': 2, 'n': 2, 'b': 2, 'q': 1, // Black
        }
        
        // Count pieces currently on board
        const currentCounts = {
          'P': 0, 'R': 0, 'N': 0, 'B': 0, 'Q': 0,
          'p': 0, 'r': 0, 'n': 0, 'b': 0, 'q': 0,
        }
        
        for (let row = 0; row < 8; row++) {
          for (let col = 0; col < 8; col++) {
            const piece = board[row][col]
            if (piece && piece.type !== 'k') { // King is never captured
              const pieceKey = piece.color === 'w' ? piece.type.toUpperCase() : piece.type.toLowerCase()
              if (currentCounts.hasOwnProperty(pieceKey)) {
                currentCounts[pieceKey]++
              }
            }
          }
        }
        
        // Calculate captured pieces
        const whiteCaptured = [] // Pieces captured BY white (black pieces that are missing)
        const blackCaptured = [] // Pieces captured BY black (white pieces that are missing)
        
        // Check for missing white pieces (captured by black)
        Object.keys(initialCounts).forEach(piece => {
          if (piece === piece.toUpperCase()) { // White piece
            const missing = initialCounts[piece] - (currentCounts[piece] || 0)
            if (missing > 0) {
              for (let i = 0; i < missing; i++) {
                whiteCaptured.push(piece.toLowerCase()) // Store as lowercase for consistency
              }
            }
          }
        })
        
        // Check for missing black pieces (captured by white)
        Object.keys(initialCounts).forEach(piece => {
          if (piece === piece.toLowerCase()) { // Black piece
            const missing = initialCounts[piece] - (currentCounts[piece] || 0)
            if (missing > 0) {
              for (let i = 0; i < missing; i++) {
                blackCaptured.push(piece) // Already lowercase
              }
            }
          }
        })
        
        setCapturedWhitePieces(whiteCaptured)
        setCapturedBlackPieces(blackCaptured)
      } catch (error) {
        console.error('Error tracking captured pieces:', error)
        setCapturedWhitePieces([])
        setCapturedBlackPieces([])
      }
    }
    
    updateCapturedPieces()
  }, [fen])

  // Check if it's player's turn
  const isPlayerTurn = () => {
    if (!playerColor) return false
    const currentGame = new Chess(fen)
    return currentGame.turn() === playerColor
  }

  // Initialize game with player color
  const startGame = async (color) => {
    try {
      setPlayerColor(color)
      const newGame = new Chess()
      setGame(newGame)
      const startFen = newGame.fen()
      setFen(startFen)
      setCommentary('')
      setEvaluation(null)
      setPrevEvaluation(null)
      setLastPlayerMove(null)
      setBadMoveCount(0)
      setGameOver(false)
      setCapturedWhitePieces([])
      setCapturedBlackPieces([])
      setPremove(null)

      // If player is black, engine moves first
      if (color === 'b') {
        // Small delay to ensure state is updated
        await new Promise(resolve => setTimeout(resolve, 100))
        console.log('Player chose black, requesting engine (white) first move with FEN:', startFen)
        try {
          await makeEngineMove(startFen)
        } catch (error) {
          console.error('Error getting engine first move:', error)
          setCommentary(`Error: ${error.message}`)
        }
      }
    } catch (error) {
      console.error('Error starting game:', error)
      setCommentary(`Error starting game: ${error.message}`)
    }
  }

  // Execute premove if it exists and it's now the player's turn
  useEffect(() => {
    if (premove && !gameOver && playerColor) {
      const currentGame = new Chess(fen)
      const playerTurn = currentGame.turn() === playerColor
      
      if (playerTurn) {
        const { from, to } = premove
        const moves = currentGame.moves({ square: from, verbose: true })
        const foundMove = moves.find(m => m.from === from && m.to === to)
        
        // Validate that premove is still legal
        if (foundMove) {
          setPremove(null) // Clear premove before executing
          // Execute the premove - construct move string properly
          let moveString = `${from}${to}`
          if (foundMove.promotion) {
            moveString += foundMove.promotion
          }
          
          // Validate move string before executing
          if (moveString && moveString.length >= 4 && moveString.length <= 5) {
            handleMove(moveString)
          } else {
            console.error('Invalid premove string:', moveString, 'from:', from, 'to:', to)
            setPremove(null)
          }
        } else {
          // Premove is no longer valid, clear it
          setPremove(null)
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fen, premove, gameOver, playerColor])

  // Make engine move (helper function) - for engine's first move when player is black
  const makeEngineMove = async (currentFen) => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    
    console.log('makeEngineMove called with FEN:', currentFen, 'sending empty move for engine first move')
    
    try {
      const requestBody = {
        fen: currentFen,
        move: '', // Empty move means engine goes first (for initial move when player is black)
      }
      
      console.log('Sending engine first move request:', requestBody)
      
      const response = await fetch(`${apiUrl}/api/move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        // Try to get error details from response
        let errorMessage = 'Failed to get engine move'
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
          console.error('Backend error response:', errorData)
          console.error('Full error detail:', errorData.detail)
        } catch (e) {
          console.error('Error parsing error response:', e)
          errorMessage = `HTTP ${response.status}: ${response.statusText}`
        }
        console.error('Throwing error with message:', errorMessage)
        throw new Error(errorMessage)
      }

      const data = await response.json()
      
      if (!data.engineMove) {
        throw new Error('Engine did not return a move')
      }

      setCommentary(data.commentary || '')
      setPrevEvaluation(null) // No previous evaluation for first move
      setEvaluation(data.evaluation || null)
      setLastPlayerMove(null) // No player move yet

      const engineGame = new Chess(currentFen)
      engineGame.move(data.engineMove)
      setGame(engineGame)
      setFen(engineGame.fen())

      if (engineGame.isGameOver()) {
        setGameOver(true)
        if (engineGame.isCheckmate()) {
          setCommentary(prev => prev || 'Checkmate! Game over.')
        } else if (engineGame.isDraw()) {
          setCommentary(prev => prev || 'Draw! Game over.')
        }
      }
    } catch (error) {
      console.error('Engine move error:', error)
      setCommentary(`Error: ${error.message}`)
      // Don't set game over on error - allow retry or manual reset
    }
  }

  const handleMove = async (move) => {
    // ABSOLUTE FIRST CHECK - reject immediately if move is falsy or empty
    if (!move) {
      console.error('handleMove BLOCKED: null/undefined move:', move, 'playerColor:', playerColor)
      setCommentary('Error: Cannot process empty move')
      return { valid: false }
    }

    if (gameOver) {
      console.log('handleMove BLOCKED: game is over')
      return { valid: false }
    }

    // Strict validation - move must be a non-empty string
    if (typeof move !== 'string') {
      console.error('handleMove BLOCKED: non-string move:', typeof move, move)
      setCommentary('Error: Move must be a string')
      return { valid: false }
    }

    const trimmedMove = move.trim()
    if (trimmedMove === '' || trimmedMove.length < 4) {
      console.error('handleMove BLOCKED: empty or too short move:', trimmedMove, 'original:', move)
      setCommentary('Error: Move cannot be empty')
      return { valid: false }
    }

    // Use trimmed move
    move = trimmedMove

    console.log('handleMove accepted move:', move, 'playerColor:', playerColor, 'isPlayerTurn:', isPlayerTurn())

    // Move should be in UCI format (e.g., "e2e4" or "e2e4q" for promotion)
    // UCI format: from_square + to_square + optional_promotion (e.g., "e2e4", "e7e8q")
    const moveLower = move.toLowerCase().trim()
    if (!/^[a-h][1-8][a-h][1-8][qnrb]?$/.test(moveLower)) {
      console.error('Move does not match UCI format:', move, 'normalized:', moveLower)
      setCommentary(`Error: Move format invalid. Move: "${move}"`)
      return { valid: false }
    }

    try {
      // Check if it's the player's turn
      if (!isPlayerTurn()) {
        console.error('Attempted to make move when it is not player turn:', {
          move,
          playerColor,
          currentTurn: new Chess(fen).turn(),
          fen
        })
        setCommentary('Error: It is not your turn')
        return { valid: false }
      }

      // Validate move locally first
      const gameCopy = new Chess(fen)
      const moveObj = gameCopy.move(move)
      
      if (!moveObj) {
        console.error('Move is not legal:', move, 'for position:', fen)
        setCommentary(`Error: Move "${move}" is not legal`)
        return { valid: false }
      }

      // Clear any premove when executing a move
      if (premove) {
        setPremove(null)
      }

      // Update game state IMMEDIATELY with player's move (no waiting)
      const newGame = new Chess(fen)
      newGame.move(move)
      setGame(newGame)
      setFen(newGame.fen())
      
      // CRITICAL: Final validation right before sending - absolutely prevent empty moves
      const finalMove = move.trim()
      if (!finalMove || finalMove === '' || finalMove.length < 4) {
        console.error('CRITICAL: Attempted to send invalid move to backend:', {
          originalMove: move,
          trimmedMove: finalMove,
          moveType: typeof move,
          fen,
          playerColor
        })
        setCommentary('Error: Cannot send empty or invalid move')
        return { valid: false }
      }

      // Ensure move matches UCI format one more time
      if (!/^[a-h][1-8][a-h][1-8][qnrb]?$/.test(finalMove.toLowerCase())) {
        console.error('CRITICAL: Move fails UCI format check before sending:', finalMove)
        setCommentary(`Error: Invalid move format: "${finalMove}"`)
        return { valid: false }
      }

      // Now make backend call in the background (non-blocking)
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      
      // Log the request for debugging
      console.log('Sending move to backend:', { 
        fen, 
        move: finalMove, 
        originalMove: move,
        playerColor,
        timestamp: new Date().toISOString()
      })
      
      // Use finalMove to ensure we never send empty string
      const requestBody = {
        fen: fen, // Original FEN before player's move
        move: finalMove, // Player's move in UCI format - use validated move
      }
      
      // Final safety check on request body
      if (!requestBody.move || requestBody.move.trim() === '') {
        console.error('CRITICAL: Request body has empty move!', requestBody)
        setCommentary('Error: Move validation failed')
        return { valid: false }
      }

      // Execute the fetch with one final validation
      (async () => {
        try {
          // One more check inside the async function
          const requestMove = requestBody.move.trim()
          if (!requestMove || requestMove.length < 4) {
            throw new Error(`Invalid move in request: "${requestMove}"`)
          }

          const requestPayload = {
            fen: requestBody.fen,
            move: requestMove
          }

          console.log('Making API request with payload:', requestPayload)
          
          const response = await fetch(`${apiUrl}/api/move`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestPayload),
          })
          
          if (!response.ok) {
            try {
              const errorData = await response.json()
              const errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`
              console.error('Move error:', errorMessage, 'Move sent:', requestMove, 'FEN:', requestPayload.fen)
              throw new Error(errorMessage)
            } catch (parseError) {
              const errorMessage = `Failed to process move: ${response.status} ${response.statusText}`
              console.error('Error parsing error response:', parseError, 'Move sent:', requestMove, 'FEN:', requestPayload.fen)
              throw new Error(errorMessage)
            }
          }

          const data = await response.json()
          
          // Store previous evaluation BEFORE updating (critical for correct calculation)
          const prevEval = evaluation
          const currentEval = data.evaluation
          
          // Show commentary when it arrives
          setCommentary(data.commentary || '')
          setEvaluation(currentEval !== null ? currentEval : null) // Update to new evaluation
          setPrevEvaluation(prevEval !== null ? prevEval : null) // Store previous evaluation
          
          // Check if this was a bad move for improvement tips
          if (currentEval !== null && prevEval !== null) {
            // Calculate evaluation change from player's perspective
            // Evaluation from backend is always from white's perspective
            // For white: positive eval is good, so if eval drops, it's bad
            // For black: negative eval is good, so we need to flip the perspective
            let playerPrevEval = prevEval
            let playerCurrentEval = currentEval
            
            if (playerColor === 'b') {
              // Flip evaluation for black player (negative is good for black)
              playerPrevEval = -prevEval
              playerCurrentEval = -currentEval
            }
            
            // Calculate change from player's perspective
            const evalChange = playerCurrentEval - playerPrevEval
            
            // If evaluation dropped significantly from player's perspective, it's a bad move
            // Lower threshold to -0.3 to catch more bad moves
            const isBadMove = evalChange < -0.3
            
            console.log('Move evaluation check:', {
              move,
              playerColor,
              prevEval,
              currentEval,
              evalChange,
              isBadMove,
              badMoveCount: badMoveCount
            })
            
            if (isBadMove) {
              // Show tips immediately for every bad move
              console.log('Bad move detected! Showing tips immediately', { move, evalChange })
              setLastPlayerMove(move) // Store the bad move for tips
              setBadMoveCount(prev => prev + 1) // Track count for reference
            } else {
              setLastPlayerMove(null)
              // Reset counter on good moves
              setBadMoveCount(0)
            }
          } else {
            console.log('Cannot check bad move - missing evaluation:', { currentEval, prevEval })
            setLastPlayerMove(null)
          }
          
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
        } catch (error) {
          console.error('Move error:', error)
          console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            move: requestBody.move,
            fen: requestBody.fen,
            playerColor: playerColor
          })
          // Show full error message
          const errorMsg = error.message || String(error) || 'Unknown error occurred'
          setCommentary(`Error: ${errorMsg}`)
        }
      })()

      return { valid: true }
    } catch (error) {
      console.error('Move validation error:', error)
      return { valid: false }
    }
  }

  const resetGame = () => {
    setPlayerColor(null) // Reset to color selection
    const newGame = new Chess()
    setGame(newGame)
    setFen(newGame.fen())
    setCommentary('')
    setEvaluation(null)
    setPrevEvaluation(null)
    setLastPlayerMove(null)
    setGameOver(false)
    setCapturedWhitePieces([])
    setCapturedBlackPieces([])
    setPremove(null)
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Clean Header Banner with Animation */}
        <div className="bg-gradient-to-r from-purple-500 via-purple-600 to-pink-500 rounded-lg shadow-2xl mb-6 py-8 px-6 animate-pulse hover:animate-none transition-all duration-300 hover:shadow-purple-500/50 hover:scale-[1.02]">
          <div className="text-center">
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-3 tracking-tight animate-fade-in drop-shadow-lg whitespace-nowrap overflow-hidden">
              <span className="inline-block animate-bounce" style={{ animationDelay: '0s' }}>T</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.1s' }}>U</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.2s' }}>S</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.3s' }}>H</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.4s' }}>I</span>
              {' '}
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.5s' }}>A</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.6s' }}>I</span>
              {' '}
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.7s' }}>C</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.8s' }}>H</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '0.9s' }}>E</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '1.0s' }}>S</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '1.1s' }}>S</span>
              {' '}
              <span className="inline-block animate-bounce" style={{ animationDelay: '1.2s' }}>B</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '1.3s' }}>O</span>
              <span className="inline-block animate-bounce" style={{ animationDelay: '1.4s' }}>T</span>
            </h1>
            <p className="text-white text-lg md:text-xl font-medium animate-fade-in-delay drop-shadow-md">
              Play against Tushar Anand
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Commentary Panel - Left */}
          <div className="lg:col-span-3 lg:order-1">
            <Commentary
              commentary={commentary}
              evaluation={evaluation}
              playerColor={playerColor}
            />
          </div>

          {/* Chess Board - Center (wider) */}
          <div className="lg:col-span-6 lg:order-2">
            <div className="bg-white rounded-lg shadow-2xl p-4 md:p-6">
              {/* Color Selection Screen */}
              {!playerColor ? (
                <div className="flex flex-col items-center justify-center py-8 sm:py-12">
                  <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-4 sm:mb-6">Choose Your Color</h2>
                  <div className="flex gap-4 sm:gap-6">
                    <button
                      onClick={() => startGame('w')}
                      className="px-6 sm:px-8 py-3 sm:py-4 bg-white border-4 border-gray-300 rounded-lg shadow-lg hover:border-purple-500 hover:shadow-xl transition-all duration-200 flex flex-col items-center gap-2 sm:gap-3 hover:scale-105"
                    >
                      <div className="text-4xl sm:text-6xl">♔</div>
                      <span className="font-bold text-gray-800 text-sm sm:text-base whitespace-nowrap">Play as White</span>
                      <span className="text-xs sm:text-sm text-gray-600">You move first</span>
                    </button>
                    <button
                      onClick={() => startGame('b')}
                      className="px-6 sm:px-8 py-3 sm:py-4 bg-gray-800 border-4 border-gray-600 rounded-lg shadow-lg hover:border-purple-500 hover:shadow-xl transition-all duration-200 flex flex-col items-center gap-2 sm:gap-3 hover:scale-105"
                    >
                      <div className="text-4xl sm:text-6xl">♚</div>
                      <span className="font-bold text-white text-sm sm:text-base whitespace-nowrap">Play as Black</span>
                      <span className="text-xs sm:text-sm text-gray-400">Engine moves first</span>
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  {/* Opponent - Top (always opposite color) */}
                  <div className="mb-3">
                    <PlayerInfo
                      username="TUSHI (Giga Chicken)"
                      avatar="/tushi.jpg"
                      capturedPieces={playerColor === 'w' ? capturedWhitePieces : capturedBlackPieces}
                      isWhite={playerColor === 'b'}
                      isOpponent={true}
                    />
                  </div>

                  <ChessBoard
                    position={fen}
                    onMove={handleMove}
                    gameOver={gameOver}
                    premove={premove}
                    setPremove={setPremove}
                    isPlayerTurn={isPlayerTurn()}
                    playerColor={playerColor}
                  />

                  {/* Player - Bottom */}
                  <div className="mt-3">
                    <PlayerInfo
                      username="You (Giga Dummy)"
                      capturedPieces={playerColor === 'w' ? capturedBlackPieces : capturedWhitePieces}
                      isWhite={playerColor === 'w'}
                      isOpponent={false}
                    />
                  </div>
                </>
              )}
              
              <div className="mt-4 flex justify-center gap-4">
                <button
                  onClick={resetGame}
                  className="px-6 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all duration-200 font-semibold shadow-md hover:shadow-lg hover:scale-105 active:scale-95"
                >
                  New Game
                </button>
                {gameOver && (
                  <span className="px-6 py-2.5 bg-gray-200 rounded-lg font-semibold text-gray-800">
                    Game Over
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Improve with TUSHI Panel - Right */}
          <div className="lg:col-span-3 lg:order-3">
            <ImproveWithTushi
              playerMove={lastPlayerMove}
              evaluation={evaluation}
              prevEvaluation={prevEvaluation}
              isBadMove={lastPlayerMove !== null && evaluation !== null && prevEvaluation !== null}
              playerColor={playerColor}
            />
          </div>
        </div>
        
        {/* Footer */}
        <div className="mt-8 mb-4 text-center">
          <p className="text-white/80 text-sm">
            Made with <span className="text-red-500 animate-pulse">❤️</span> by <span className="font-semibold">Aarush</span>
          </p>
        </div>
      </div>
    </div>
  )
}

export default App

