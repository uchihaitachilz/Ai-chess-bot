import { useEffect, useState } from 'react'

// Unicode chess piece symbols
const PIECE_SYMBOLS = {
  'p': '♟', // black pawn
  'r': '♜', // black rook
  'n': '♞', // black knight
  'b': '♝', // black bishop
  'q': '♛', // black queen
  'k': '♚', // black king
  'P': '♙', // white pawn
  'R': '♖', // white rook
  'N': '♘', // white knight
  'B': '♗', // white bishop
  'Q': '♕', // white queen
  'K': '♔', // white king
}

function PlayerInfo({ 
  username, 
  avatar, 
  country, 
  rating, 
  capturedPieces, 
  isWhite,
  isOpponent = false 
}) {
  const [imageSrc, setImageSrc] = useState(null)
  const [imageError, setImageError] = useState(false)

  useEffect(() => {
    if (avatar && typeof avatar === 'string') {
      // If avatar is a path, try to load it
      if (avatar.startsWith('/') || avatar.startsWith('./')) {
        const img = new Image()
        img.onload = () => {
          setImageSrc(avatar)
          setImageError(false)
        }
        img.onerror = () => {
          setImageError(true)
        }
        img.src = avatar
      } else if (avatar.startsWith('http')) {
        // URL
        setImageSrc(avatar)
      } else {
        // Emoji or text
        setImageError(false)
      }
    }
  }, [avatar])

  // Group captured pieces by type
  const groupedPieces = {}
  capturedPieces.forEach(piece => {
    const key = piece.toLowerCase()
    groupedPieces[key] = (groupedPieces[key] || 0) + 1
  })

  // Order: pawn, rook, knight, bishop, queen (king is never captured)
  const pieceOrder = ['p', 'r', 'n', 'b', 'q']
  const sortedPieces = pieceOrder.filter(p => groupedPieces[p] > 0)

  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg px-3 py-2.5 shadow-md border border-gray-700/50 hover:border-purple-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/10 cursor-default">
      <div className="flex items-center gap-2.5">
        {/* Avatar */}
        <div className="w-10 h-10 rounded-full overflow-hidden bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center shadow-md flex-shrink-0 border border-purple-500/50 hover:border-purple-400 transition-all duration-300 hover:scale-110">
          {imageSrc && !imageError ? (
            <img 
              src={imageSrc} 
              alt={username} 
              className="w-full h-full object-cover"
              onError={() => setImageError(true)}
            />
          ) : avatar && typeof avatar === 'string' && !avatar.startsWith('/') && !avatar.startsWith('http') ? (
            <span className="text-white font-bold text-sm">{avatar}</span>
          ) : (
            <span className="text-white font-bold text-sm">{username.charAt(0).toUpperCase()}</span>
          )}
        </div>

        {/* Username */}
        <div className="flex-1 min-w-0">
          <span className="text-white font-semibold text-sm truncate block hover:text-purple-300 transition-colors">
            {username}
          </span>
        </div>

        {/* Captured Pieces */}
        {sortedPieces.length > 0 && (
          <div className="flex items-center gap-1.5 ml-auto">
            {sortedPieces.map(pieceType => {
              const count = groupedPieces[pieceType]
              // Pieces are stored as lowercase
              // White player (isWhite=true) captured black pieces -> show black symbols (lowercase)
              // Black player (isWhite=false) captured white pieces -> show white symbols (uppercase)
              const pieceKey = isWhite ? pieceType : pieceType.toUpperCase()
              const symbol = PIECE_SYMBOLS[pieceKey]
              if (!symbol) return null
              return (
                <div 
                  key={pieceType} 
                  className="flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-gray-700/50 hover:bg-gray-700 transition-colors"
                  title={`Captured ${count} ${pieceType === 'p' ? 'pawn' : pieceType === 'r' ? 'rook' : pieceType === 'n' ? 'knight' : pieceType === 'b' ? 'bishop' : 'queen'}(s)`}
                >
                  <span className="text-lg text-gray-200">{symbol}</span>
                  {count > 1 && (
                    <span className="text-gray-300 text-xs font-semibold">{count}</span>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default PlayerInfo
