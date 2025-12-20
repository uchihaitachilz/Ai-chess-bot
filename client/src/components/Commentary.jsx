import { useState, useEffect } from 'react'

function Commentary({ commentary, evaluation }) {
  const [imageSrc, setImageSrc] = useState(null)
  const [imageError, setImageError] = useState(false)
  
  // Try to load image from multiple possible locations
  useEffect(() => {
    const imagePaths = [
      '/tushi.jpg',
      '/tushi.png',
      '/tushi.jpeg',
      '/tushi.JPG',
      '/tushi.PNG',
      '/tushi.JPEG',
      './tushi.jpg',
      './tushi.png',
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
  
  return (
    <div className="bg-white rounded-lg shadow-2xl p-4 sm:p-6 h-full flex flex-col min-w-0">
      {/* Tushi Image and Header */}
      <div className="mb-4">
        <div className="mb-3">
          <div className="flex items-start gap-2 sm:gap-3 mb-2">
            <div className="w-14 h-14 sm:w-16 sm:h-16 md:w-20 md:h-20 rounded-full overflow-hidden bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center shadow-lg flex-shrink-0 border-2 border-purple-500 relative">
              {imageSrc && !imageError ? (
                <img 
                  src={imageSrc} 
                  alt="SadisticTushi" 
                  className="w-full h-full object-cover"
                  onError={() => setImageError(true)}
                />
              ) : (
                <span className="text-white font-bold text-lg sm:text-xl md:text-2xl">T</span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-base sm:text-lg md:text-xl font-bold text-gray-800 border-b-2 border-purple-600 pb-2 leading-tight">
                TUSHI COMMENTARY
              </h2>
              <p className="text-[9px] sm:text-[10px] md:text-xs text-gray-500 italic mt-1 leading-tight">
                "I am sweetest guy who keep kids at basement"
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="flex-1 min-h-[200px] overflow-hidden">
        {commentary ? (
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-4 border-l-4 border-purple-600">
              <p className="text-gray-800 text-lg leading-relaxed">
                {commentary}
              </p>
            </div>
            
            {evaluation !== null && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-600 mb-1">Position Evaluation:</p>
                <p className={`text-xl font-bold ${
                  evaluation > 0 ? 'text-green-600' : 
                  evaluation < 0 ? 'text-red-600' : 
                  'text-gray-600'
                }`}>
                  {evaluation > 0 ? '+' : ''}{evaluation.toFixed(2)} pawns
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full p-4">
            <p className="text-gray-400 text-center text-[10px] sm:text-xs md:text-sm leading-tight">
              Make a move to see TUSHI's savage commentary
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Commentary

