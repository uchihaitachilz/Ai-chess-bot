# AI Chess Bot - TUSHI Edition

A complete AI-assisted chess web application where you play against Stockfish with savage-but-safe AI commentary inspired by SadisticTushi. Built with React, FastAPI, and Stockfish.

## Features

- 🎮 Interactive chess board with click-to-move
- 🤖 Stockfish engine integration (depth 10-12)
- 💬 AI-generated commentary (OpenAI or rule-based fallback)
- ✅ Move validation and game state management
- 🎨 Modern UI with Tailwind CSS
- 🔥 Savage, sarcastic, and witty commentary

## Tech Stack

### Frontend
- React 18
- Vite
- JavaScript
- react-chessboard
- chess.js
- Tailwind CSS

### Backend
- Python 3.8+
- FastAPI
- python-chess
- Stockfish (UCI engine)
- OpenAI-compatible LLM (optional)

## Deployment on Vercel

### Frontend Deployment

1. Go to [Vercel Dashboard](https://vercel.com)
2. Click "New Project"
3. Import the repository
4. Set Root Directory to `client`
5. Build Command: `npm run build`
6. Output Directory: `dist`
7. Install Command: `npm install`
8. Add Environment Variables:
   - `VITE_API_URL`: Your backend Vercel URL

### Backend Deployment

**Note:** Vercel's serverless functions have limitations with Stockfish. Consider alternatives:

1. **Option 1: Vercel Serverless (Limited)**
   - Stockfish needs to be installed in the environment
   - May require custom Docker setup

2. **Option 2: Railway/Render (Recommended)**
   - Better for long-running processes
   - Easier Stockfish installation
   - Deploy the `server` folder

3. **Option 3: Separate Backend Hosting**
   - Deploy backend on Railway, Render, or Heroku
   - Update frontend API URL to point to backend

## Local Development

### Prerequisites

1. **Python 3.8+** installed
2. **Node.js 18+** and npm installed
3. **Stockfish** installed on your system

### Setup

1. **Backend:**
```bash
cd server
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

2. **Frontend:**
```bash
cd client
npm install
npm run dev
```

3. **Environment Variables:**
Create a `.env` file in the root:
```
ENGINE_PATH=/usr/bin/stockfish
ENGINE_DEPTH=12
OPENAI_API_KEY=your_key_here (optional)
```

## Project Structure

```
Chess-Bot/
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChessBoard.jsx
│   │   │   └── Commentary.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── vercel.json
├── server/                 # FastAPI backend
│   ├── engine/
│   │   └── stockfish.py
│   ├── ai/
│   │   └── commentary.py
│   ├── main.py
│   └── vercel.json
└── README.md
```

## API Endpoints

### POST `/api/move`

Process a chess move and get the engine's response.

**Request:**
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "move": "e2e4"
}
```

**Response:**
```json
{
  "engineMove": "e7e5",
  "evaluation": 0.3,
  "commentary": "Looks so cheeky! That's actually a solid move, dummy."
}
```

## License

This project is open source and available for personal and educational use.

## Credits

- Built with [react-chessboard](https://github.com/Clariity/react-chessboard)
- Chess logic powered by [chess.js](https://github.com/jhlywa/chess.js) and [python-chess](https://github.com/niklasf/python-chess)
- Engine: [Stockfish](https://stockfishchess.org/)
- Commentary style inspired by SadisticTushi
