"""
FastAPI backend for AI-assisted chess application.
Handles move validation, Stockfish engine integration, and AI commentary.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chess
import chess.engine
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from engine.stockfish import get_best_move
from ai.commentary import generate_commentary

app = FastAPI(title="Chess Bot API")

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.onrender.com",  # Allow all Render subdomains
        "https://*.vercel.app",    # Allow all Vercel subdomains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MoveRequest(BaseModel):
    """Request model for move endpoint."""
    fen: str
    move: str


class MoveResponse(BaseModel):
    """Response model for move endpoint."""
    engineMove: str
    evaluation: float
    commentary: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Chess Bot API is running"}


@app.post("/api/move", response_model=MoveResponse)
async def process_move(request: MoveRequest):
    """
    Process a chess move:
    1. Validate the move
    2. Update the board
    3. Get Stockfish's best reply
    4. Generate AI commentary
    """
    try:
        # Create board from FEN
        board = chess.Board(request.fen)
        
        # Validate and apply the move
        try:
            move = chess.Move.from_uci(request.move)
            if move not in board.legal_moves:
                raise HTTPException(
                    status_code=400,
                    detail=f"Illegal move: {request.move}"
                )
            board.push(move)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid move format: {request.move}"
            )
        
        # Check game status
        if board.is_checkmate():
            return MoveResponse(
                engineMove="",
                evaluation=float("inf") if board.turn == chess.BLACK else float("-inf"),
                commentary="Checkmate! Game over. Well played... or not."
            )
        
        if board.is_stalemate():
            return MoveResponse(
                engineMove="",
                evaluation=0.0,
                commentary="Stalemate. A draw by boredom. How exciting."
            )
        
        if board.is_insufficient_material():
            return MoveResponse(
                engineMove="",
                evaluation=0.0,
                commentary="Insufficient material. Even the engine can't win this one."
            )
        
        # Get Stockfish's best move
        engine_move, evaluation = await get_best_move(board)
        
        # Generate AI commentary
        commentary = await generate_commentary(
            board,
            request.move,
            engine_move,
            evaluation
        )
        
        return MoveResponse(
            engineMove=engine_move,
            evaluation=evaluation,
            commentary=commentary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

