import { useState } from 'react'
import { Chessboard } from 'react-chessboard'
import { Chess } from 'chess.js'

function ChessBoard({ position, onMove, gameOver }) {
  const [moveFrom, setMoveFrom] = useState(null)
  const [optionSquares, setOptionSquares] = useState({})

  // Get valid move squares for a piece
  function getMoveOptions(square) {
    const moves = new Chess(position).moves({
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
          new Chess(position).get(move.to) &&
          new Chess(position).get(move.to).color !==
            new Chess(position).get(square).color
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

  // Handle piece drag start
  function onSquareClick(square) {
    if (gameOver) return

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

  // Make a move (non-blocking)
  function makeMove(from, to) {
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
          onMove(promotionMove).catch(console.error)
          return { valid: true }
        }
      }
      return { valid: false }
    }

    // Construct move string
    let moveString = `${from}${to}`
    if (foundMove.promotion) {
      moveString += foundMove.promotion
    }

    // Call onMove but don't wait for it - it updates the board immediately
    onMove(moveString).catch(console.error)
    return { valid: true }
  }

  // Handle piece drop (must be synchronous for react-chessboard)
  function onPieceDrop(sourceSquare, targetSquare) {
    if (gameOver) return false
    
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
          // Trigger async move (fire and forget)
          onMove(promotionMove).catch(console.error)
          setMoveFrom(null)
          setOptionSquares({})
          return true
        }
      }
      return false
    }

    // Construct move string
    let moveString = `${sourceSquare}${targetSquare}`
    if (foundMove.promotion) {
      moveString += foundMove.promotion
    }

    // Trigger async move (fire and forget)
    onMove(moveString).catch(console.error)
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
          }}
          boardOrientation="white"
          arePiecesDraggable={!gameOver}
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

