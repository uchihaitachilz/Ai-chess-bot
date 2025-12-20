import { useState, useEffect } from 'react'

function ImproveWithTushi({ playerMove, evaluation, prevEvaluation, isBadMove, playerColor }) {
  const [imageSrc, setImageSrc] = useState(null)
  const [imageError, setImageError] = useState(false)
  const [tips, setTips] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showAnimation, setShowAnimation] = useState(false)
  
  // Try to load image
  useEffect(() => {
    const imagePaths = [
      '/tushi-coach.png',
      '/tushi-coach.jpg',
      './tushi-coach.png',
    ]
    
    let currentIndex = 0
    
    const tryLoadImage = (index) => {
      if (index >= imagePaths.length) {
        setImageError(true)
        return
      }
      
      const img = new Image()
      img.onload = () => {
        setImageSrc(imagePaths[index])
        setImageError(false)
      }
      img.onerror = () => {
        tryLoadImage(index + 1)
      }
      img.src = imagePaths[index]
    }
    
    tryLoadImage(0)
  }, [])

  // Fetch improvement tips when bad move is detected
  useEffect(() => {
    console.log('ImproveWithTushi useEffect:', { isBadMove, playerMove, evaluation, prevEvaluation })
    if (isBadMove && playerMove && evaluation !== null && prevEvaluation !== null) {
      console.log('Fetching improvement tips for move:', playerMove)
      fetchImprovementTips(playerMove, evaluation, prevEvaluation)
    } else {
      // Clear tips when move is good or no bad move detected
      if (!isBadMove) {
        setTips(null)
        setShowAnimation(false)
      }
    }
  }, [isBadMove, playerMove, evaluation, prevEvaluation])

  const fetchImprovementTips = async (move, currentEval, previousEval) => {
    console.log('fetchImprovementTips called:', { move, currentEval, previousEval, playerColor })
    setLoading(true)
    setShowAnimation(true)
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
      // Flip evaluation if player is black (backend evaluation is from white's perspective)
      const playerCurrentEval = playerColor === 'b' ? -currentEval : currentEval
      const playerPrevEval = playerColor === 'b' ? -previousEval : previousEval
      
      console.log('Calling improvement tips API:', `${apiUrl}/api/improvement-tips`)
      console.log('Evaluation from player perspective:', { playerCurrentEval, playerPrevEval })
      
      const response = await fetch(`${apiUrl}/api/improvement-tips`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          move: move,
          evaluation: playerCurrentEval,
          previousEvaluation: playerPrevEval,
          playerColor: playerColor,
        }),
      })

      console.log('Improvement tips response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('Improvement tips received:', data)
        setTips(data.tips || "Focus on piece development and controlling the center, dummy! Don't just move randomly, kid!")
      } else {
        const errorText = await response.text()
        console.error('Improvement tips API error:', response.status, errorText)
        // Fallback to generic tips
        setTips("Focus on piece development and controlling the center, dummy! Don't just move randomly, kid!")
      }
    } catch (error) {
      console.error('Error fetching improvement tips:', error)
      // Fallback tips
      setTips("That's why you are the dummy! Try thinking about piece safety and control. Dis is da whey to improve, kid!")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-2xl p-4 sm:p-6 h-full flex flex-col min-w-0">
      {/* Tushi Coach Image and Header */}
      <div className="mb-4">
        <div className="mb-3">
          <div className="flex items-start gap-2 sm:gap-3 mb-2">
            <div className="w-14 h-14 sm:w-16 sm:h-16 md:w-20 md:h-20 rounded-full overflow-hidden bg-gradient-to-br from-green-400 to-blue-400 flex items-center justify-center shadow-lg flex-shrink-0 border-2 border-green-500 relative">
              {imageSrc && !imageError ? (
                <img 
                  src={imageSrc} 
                  alt="TUSHI Coach" 
                  className="w-full h-full object-cover"
                  onError={() => setImageError(true)}
                />
              ) : (
                <span className="text-white font-bold text-lg sm:text-xl md:text-2xl">T</span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-base sm:text-lg md:text-xl font-bold text-gray-800 border-b-2 border-green-600 pb-2 leading-tight">
                IMPROVE WITH TUSHI
              </h2>
              <p className="text-[9px] sm:text-[10px] md:text-xs text-gray-500 italic mt-1 leading-tight">
                "#1 Coach - Helping you get better!"
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="flex-1 min-h-[200px] flex flex-col justify-center overflow-hidden">
        {loading ? (
          <div className="flex flex-col items-center justify-center space-y-4 animate-pulse">
            <div className="w-16 h-16 border-4 border-green-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-gray-500 text-sm">TUSHI is analyzing your move...</p>
          </div>
        ) : tips ? (
          <div 
            className={`space-y-4 transition-all duration-500 ${
              showAnimation ? 'animate-fade-in-up' : ''
            }`}
          >
            <div className="bg-gradient-to-r from-green-50 via-blue-50 to-purple-50 rounded-lg p-4 border-l-4 border-green-600 shadow-md transform hover:scale-[1.02] transition-transform duration-300">
              <div className="flex items-start gap-3">
                <div className="text-3xl flex-shrink-0 animate-bounce" style={{ animationDelay: '0s' }}>
                  💡
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-gray-800 text-sm sm:text-base leading-relaxed font-medium break-words word-wrap overflow-wrap-anywhere">
                    {tips}
                  </p>
                </div>
              </div>
            </div>
            
            {/* Animated decoration */}
            <div className="flex justify-center gap-2 mt-4">
              <span className="text-2xl animate-bounce" style={{ animationDelay: '0s' }}>🎓</span>
              <span className="text-2xl animate-bounce" style={{ animationDelay: '0.2s' }}>♟️</span>
              <span className="text-2xl animate-bounce" style={{ animationDelay: '0.4s' }}>💪</span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full space-y-4 px-2">
            <div className="text-6xl mb-2 animate-pulse">🎯</div>
            <p className="text-gray-400 text-center text-xs whitespace-nowrap">
              Make a bad move to get TUSHI's coaching tips!
            </p>
            <p className="text-gray-300 text-center text-[10px] italic whitespace-nowrap">
              Learn and improve with simple, actionable advice
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ImproveWithTushi
