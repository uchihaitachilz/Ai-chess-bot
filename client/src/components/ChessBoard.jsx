import { useState, useEffect } from 'react'
import { Chessboard } from 'react-chessboard'
import { Chess } from 'chess.js'

function ChessBoard({ position, onMove, gameOver, premove, setPremove, isPlayerTurn, playerColor = 'w' }) {
  const [moveFrom, setMoveFrom] = useState(null)
  const [optionSquares, setOptionSquares] = useState({})
  const [premoveSquares, setPremoveSquares] = useState({})

  // Update premove visual feedback
  useEffect(() => {
    if (premove) {
      setPremoveSquares({
        [premove.from]: {
          background: 'rgba(100, 200, 255, 0.4)',
        },
        [premove.to]: {
          background: 'rgba(100, 200, 255, 0.6)',
          borderRadius: '50%',
        },
      })
    } else {
      setPremoveSquares({})
    }
  }, [premove])

  // Get valid move squares for a piece
  function getMoveOptions(square) {
    const game = new Chess(position)
    const piece = game.get(square)
    
    // Only allow selecting your own pieces
    if (!piece || piece.color !== playerColor) {
      setOptionSquares({})
      return false
    }

    const moves = game.moves({
      square,
      verbose: true,
    })
    
    if (moves.length === 0) {
      setOptionSquares({})
      return false
    }

    const newSquares = {}
    moves.forEach((move) => {
      newSquares[move.to] = {
        background:
          game.get(move.to) &&
          game.get(move.to).color !== piece.color
            ? 'radial-gradient(circle, rgba(0,0,0,.1) 85%, transparent 85%)'
            : 'radial-gradient(circle, rgba(0,0,0,.1) 25%, transparent 25%)',
        borderRadius: '50%',
      }
    })
    
    newSquares[square] = {
      background: 'rgba(255, 255, 0, 0.4)',
    }
    
    setOptionSquares(newSquares)
    return true
  }

  // Get premove options - show all possible destination squares when selecting a player's piece
  function getPremoveOptions(square) {
    const game = new Chess(position)
    const piece = game.get(square)
    
    // Only allow premoving with player's pieces
    if (!piece || piece.color !== playerColor) {
      setOptionSquares({})
      return false
    }

    // For premoves, we'll be permissive and show all squares as possible destinations
    // The actual validation happens when the premove executes
    // Create a temporary game to get potential moves
    try {
      // Try to create a game state where it's white's turn to get valid moves
      // This is a workaround since chess.js doesn't allow moves when it's not your turn
      const allSquares = []
      for (let file = 'a'.charCodeAt(0); file <= 'h'.charCodeAt(0); file++) {
        for (let rank = 1; rank <= 8; rank++) {
          allSquares.push(String.fromCharCode(file) + rank)
        }
      }

      const newSquares = {}
      // Show all squares as potential premove destinations (user can click any)
      allSquares.forEach(sq => {
        if (sq !== square) {
          newSquares[sq] = {
            background: 'rgba(100, 200, 255, 0.3)',
            borderRadius: '50%',
          }
        }
      })
      
      newSquares[square] = {
        background: 'rgba(100, 200, 255, 0.5)',
      }
      
      setOptionSquares(newSquares)
      return true
    } catch (error) {
      setOptionSquares({})
      return false
    }
  }

  // Handle piece drag start
  function onSquareClick(square) {
    if (gameOver) return

    // If not player's turn, allow premove
    if (!isPlayerTurn) {
      if (!moveFrom) {
        // Try to select square for premove
        const hasOptions = getPremoveOptions(square)
        if (hasOptions) {
          setMoveFrom(square)
        }
        return
      }

      // If clicking the same square, deselect
      if (moveFrom === square) {
        setMoveFrom(null)
        setOptionSquares({})
        setPremove(null)
        return
      }

      // Try to set premove
      const premoveResult = setPremoveMove(moveFrom, square)
      
      if (!premoveResult || !premoveResult.valid) {
        // If premove failed, try selecting the new square
        const hasOptions = getPremoveOptions(square)
        if (hasOptions) {
          setMoveFrom(square)
        } else {
          setMoveFrom(null)
          setOptionSquares({})
          setPremove(null)
        }
      } else {
        // Premove successful, reset selection
        setMoveFrom(null)
        setOptionSquares({})
      }
      return
    }

    // Normal move logic (player's turn)
    // If no piece selected, try to select this square
    if (!moveFrom) {
      const hasOptions = getMoveOptions(square)
      if (hasOptions) {
        setMoveFrom(square)
      }
      return
    }

    // If clicking the same square, deselect
    if (moveFrom === square) {
      setMoveFrom(null)
      setOptionSquares({})
      return
    }

    // Try to make the move (non-blocking)
    const moveResult = makeMove(moveFrom, square)
    
    if (!moveResult || !moveResult.valid) {
      // If move failed, try selecting the new square
      const hasOptions = getMoveOptions(square)
      if (hasOptions) {
        setMoveFrom(square)
      } else {
        setMoveFrom(null)
        setOptionSquares({})
      }
    } else {
      // Move successful, reset selection
      setMoveFrom(null)
      setOptionSquares({})
    }
  }

  // Set premove (when it's not player's turn)
  function setPremoveMove(from, to) {
    const game = new Chess(position)
    const piece = game.get(from)
    
    // Only allow premoving with player's pieces
    if (!piece || piece.color !== playerColor) {
      return { valid: false }
    }

    // For premoves, we accept any move with player's piece
    // The actual validation happens when the premove executes
    // This allows users to premove freely, and invalid premoves will be rejected on execution
    if (setPremove) {
      setPremove({ from, to })
      return { valid: true }
    }
    return { valid: false }
  }

  // Make a move (non-blocking)
  function makeMove(from, to) {
    // Validate inputs
    if (!from || !to || typeof from !== 'string' || typeof to !== 'string') {
      console.error('Invalid move parameters:', { from, to })
      return { valid: false }
    }

    const game = new Chess(position)
    const moves = game.moves({ square: from, verbose: true })
    const foundMove = moves.find(
      (m) => m.from === from && m.to === to
    )

    // If it's a promotion, default to queen
    if (!foundMove) {
      // Check if it's a pawn promotion
      const piece = game.get(from)
      if (piece && piece.type === 'p') {
        if ((piece.color === 'w' && to[1] === '8') || 
            (piece.color === 'b' && to[1] === '1')) {
          const promotionMove = `${from}${to}q`
          if (promotionMove && promotionMove.length >= 5) {
            onMove(promotionMove).catch(error => {
              console.error('Error in onMove (promotion):', error, 'move:', promotionMove)
            })
            return { valid: true }
          }
        }
      }
      return { valid: false }
    }

    // Construct move string
    let moveString = `${from}${to}`
    if (foundMove.promotion) {
      moveString += foundMove.promotion
    }

    // Validate move string format
    if (!moveString || moveString.length < 4 || moveString.length > 5) {
      console.error('Invalid move string constructed:', moveString, 'from:', from, 'to:', to, 'promotion:', foundMove.promotion)
      return { valid: false }
    }

    // Double check move string before calling onMove
    if (moveString.trim() === '') {
      console.error('Move string is empty after construction!')
      return { valid: false }
    }

    // Call onMove but don't wait for it - it updates the board immediately
    onMove(moveString).catch(error => {
      console.error('Error in onMove:', error, 'moveString:', moveString)
    })
    return { valid: true }
  }

  // Handle piece drop (must be synchronous for react-chessboard)
  function onPieceDrop(sourceSquare, targetSquare) {
    if (gameOver) return false
    
    // If not player's turn, handle as premove
    if (!isPlayerTurn) {
      const piece = new Chess(position).get(sourceSquare)
      if (piece && piece.color === playerColor) {
        // Set premove
        if (setPremove) {
          setPremove({ from: sourceSquare, to: targetSquare })
          setMoveFrom(null)
          setOptionSquares({})
          return true
        }
      }
      return false
    }
    
    // Normal move (player's turn)
    // Validate inputs
    if (!sourceSquare || !targetSquare || typeof sourceSquare !== 'string' || typeof targetSquare !== 'string') {
      console.error('Invalid drop parameters:', { sourceSquare, targetSquare })
      return false
    }

    // Validate move locally first
    const game = new Chess(position)
    const moves = game.moves({ square: sourceSquare, verbose: true })
    const foundMove = moves.find(
      (m) => m.from === sourceSquare && m.to === targetSquare
    )

    if (!foundMove) {
      // Check if it's a pawn promotion
      const piece = game.get(sourceSquare)
      if (piece && piece.type === 'p') {
        if ((piece.color === 'w' && targetSquare[1] === '8') || 
            (piece.color === 'b' && targetSquare[1] === '1')) {
          const promotionMove = `${sourceSquare}${targetSquare}q`
          if (promotionMove && promotionMove.length >= 5) {
            // Trigger async move (fire and forget)
            onMove(promotionMove).catch(error => {
              console.error('Error in onMove (promotion drop):', error, 'move:', promotionMove)
            })
            setMoveFrom(null)
            setOptionSquares({})
            return true
          }
        }
      }
      return false
    }

    // Construct move string
    let moveString = `${sourceSquare}${targetSquare}`
    if (foundMove.promotion) {
      moveString += foundMove.promotion
    }

    // Validate move string format
    if (!moveString || moveString.length < 4 || moveString.length > 5 || moveString.trim() === '') {
      console.error('Invalid move string constructed (drop):', moveString, 'from:', sourceSquare, 'to:', targetSquare, 'promotion:', foundMove.promotion)
      return false
    }

    // Trigger async move (fire and forget)
    onMove(moveString).catch(error => {
      console.error('Error in onMove (drop):', error, 'moveString:', moveString)
    })
    setMoveFrom(null)
    setOptionSquares({})
    return true
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="relative">
        <Chessboard
          position={position}
          onSquareClick={onSquareClick}
          onPieceDrop={onPieceDrop}
          customSquareStyles={{
            ...optionSquares,
            ...premoveSquares,
          }}
          boardOrientation={playerColor === 'w' ? 'white' : 'black'}
          arePiecesDraggable={!gameOver && isPlayerTurn}
          customBoardStyle={{
            borderRadius: '4px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          }}
        />
      </div>
    </div>
  )
}

export default ChessBoard

