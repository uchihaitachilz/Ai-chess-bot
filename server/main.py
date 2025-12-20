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
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from engine.stockfish import get_best_move
from ai.commentary import generate_commentary, generate_improvement_tips


async def keep_alive_ping():
    """
    Background task to ping the health endpoint to keep Render server awake.
    
    NOTE: This only works while the server is already running. When Render puts
    the server to sleep (after 50s inactivity), the entire process stops, so
    self-pinging won't wake it up. For a truly sleeping server, use an external
    service like UptimeRobot (https://uptimerobot.com) or cron-job.org to ping
    your server's root endpoint every 30-40 seconds.
    """
    # Only run on Render (when RENDER_EXTERNAL_URL is set)
    server_url = os.getenv("RENDER_EXTERNAL_URL")
    if not server_url:
        return  # Skip in local development
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            try:
                # Ping immediately, then every 30 seconds to stay under 50 second timeout
                await client.get(f"{server_url}/")
                await asyncio.sleep(30)  # Wait 30 seconds before next ping
            except Exception:
                # On error, wait before retrying (server might be starting up)
                await asyncio.sleep(30)
                pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start keep-alive task if on Render
    if os.getenv("RENDER_EXTERNAL_URL"):
        asyncio.create_task(keep_alive_ping())
    yield
    # Shutdown: cleanup if needed


app = FastAPI(title="Chess Bot API", lifespan=lifespan)

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_origin_regex=r"https://.*\.(onrender\.com|vercel\.app)",  # Regex for Render and Vercel subdomains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MoveRequest(BaseModel):
    """Request model for move endpoint."""
    fen: str
    move: str = ""  # Can be empty for engine to move first (default empty)
    
    class Config:
        # Allow empty strings to be preserved
        validate_assignment = True


class MoveResponse(BaseModel):
    """Response model for move endpoint."""
    engineMove: str
    evaluation: float
    commentary: str


class ImprovementTipsRequest(BaseModel):
    """Request model for improvement tips endpoint."""
    move: str
    evaluation: float
    previousEvaluation: float


class ImprovementTipsResponse(BaseModel):
    """Response model for improvement tips endpoint."""
    tips: str


@app.get("/")
@app.get("/health")
async def root():
    """
    Health check endpoint.
    Use this endpoint with external monitoring services (UptimeRobot, cron-job.org)
    to keep Render server alive by pinging every 30-40 seconds.
    """
    return {"status": "ok", "message": "Chess Bot API is running"}


@app.post("/api/improvement-tips", response_model=ImprovementTipsResponse)
async def get_improvement_tips(request: ImprovementTipsRequest):
    """
    Generate improvement tips when player makes a bad move.
    """
    try:
        tips = await generate_improvement_tips(
            move=request.move,
            evaluation=request.evaluation,
            previous_evaluation=request.previousEvaluation,  # Pydantic model uses camelCase
            is_white=True  # Default to white, can be enhanced later
        )
        
        return ImprovementTipsResponse(tips=tips)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error generating improvement tips: {str(e)}")
        print(f"Traceback: {error_trace}")
        # Return fallback tip on error
        return ImprovementTipsResponse(
            tips="That's why you are the dummy! Focus on piece development and safety, kid. Dis is da whey to improve!"
        )


@app.post("/api/move", response_model=MoveResponse)
async def process_move(request: MoveRequest):
    """
    Process a chess move:
    1. Validate the move (if provided)
    2. Update the board
    3. Get Stockfish's best reply
    4. Generate AI commentary
    
    If move is empty, engine makes the first move (for when player chooses black).
    """
    try:
        # Create board from FEN
        board = chess.Board(request.fen)
        
        # PRIORITY: Check if move is empty FIRST - handle engine's first move (when player chose black)
        # Direct access to move field
        move_value = request.move
        
        # Normalize: convert to string and strip
        if move_value is None:
            move_clean = ""
        else:
            move_clean = str(move_value).strip()
        
        # Empty check: move is empty if it's empty string or None
        move_is_empty = (not move_clean or move_clean == "")
        
        print(f"=== DEBUG START ===")
        print(f"request.move = {request.move!r} (type: {type(request.move)})")
        print(f"move_clean = {move_clean!r}")
        print(f"move_is_empty = {move_is_empty}")
        print(f"board.turn = {board.turn} ({'white' if board.turn == chess.WHITE else 'black'})")
        print(f"chess.WHITE = {chess.WHITE}")
        print(f"===================")
        
        # Handle empty move FIRST (engine goes first when player chose black)
        if move_is_empty:
            print(f"DEBUG: Empty move detected, entering engine first move handler")
            try:
                print(f"DEBUG: Inside empty move handler, board.turn={board.turn}, chess.WHITE={chess.WHITE}")
                # Check that it's white's turn (engine's turn) - this is for engine's first move when player chose black
                current_turn = 'white' if board.turn == chess.WHITE else 'black'
                print(f"DEBUG: Current turn check: board.turn={board.turn}, chess.WHITE={chess.WHITE}, match={board.turn == chess.WHITE}")
                if board.turn != chess.WHITE:
                    error_msg = f"Cannot process empty move: It's {current_turn}'s turn, not white's turn. Empty move is only valid when it's white's turn (engine's first move when player chose black)."
                    print(f"DEBUG ERROR: {error_msg}")
                    raise HTTPException(
                        status_code=400,
                        detail=error_msg
                    )
                
                print(f"DEBUG: Calling get_best_move for engine's first move")
                # Engine makes the first move
                engine_move, evaluation = await get_best_move(board)
                print(f"DEBUG: Engine returned move: {engine_move}, evaluation: {evaluation}")
                
                if not engine_move:
                    raise HTTPException(
                        status_code=500,
                        detail="Engine failed to generate a move"
                    )
                
                # Apply engine move to get new position
                engine_board = board.copy()
                engine_board.push(chess.Move.from_uci(engine_move))
                
                # Check game status after engine move
                if engine_board.is_checkmate():
                    commentary = "Checkmate! Game over. Well played... or not."
                elif engine_board.is_stalemate():
                    commentary = "Stalemate. A draw by boredom. How exciting."
                elif engine_board.is_insufficient_material():
                    commentary = "Insufficient material. Even the engine can't win this one."
                else:
                    # Generate commentary for engine's first move
                    # Pass the board before the move for consistency
                    commentary = await generate_commentary(
                        board,
                        "",
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
                # Log the actual error for debugging
                import traceback
                error_trace = traceback.format_exc()
                print(f"Error in engine first move: {str(e)}")
                print(f"Traceback: {error_trace}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error getting engine's first move: {str(e)}. Check server logs for details."
                )
        
        # Validate and apply the player's move (move is NOT empty at this point - if we reach here, move has a value)
        print(f"=== DEBUG: Processing non-empty player move ===")
        print(f"move_clean = {move_clean!r}")
        try:
            # Use the already-cleaned move value from above
            move_str = move_clean
            
            # Double-check it's not empty (should not happen if empty move check worked)
            if not move_str or move_str == "":
                # This should never happen if empty move handling above worked correctly
                current_turn = 'white' if board.turn == chess.WHITE else 'black'
                error_msg = f"BUG: Move is empty when it's {current_turn}'s turn. This should have been caught earlier. Empty moves are only allowed when it's white's turn (for engine's first move)."
                print(f"ERROR: {error_msg}")
                raise HTTPException(
                    status_code=400,
                    detail=error_msg
                )
            
            # Basic format check
            if len(move_str) < 4 or len(move_str) > 5:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid move format: '{move_str}'. Move must be 4-5 characters (e.g., 'e2e4' or 'e7e8q')."
                )
            
            try:
                move = chess.Move.from_uci(move_str)
            except ValueError as ve:
                # This should not happen for empty moves - they should be caught above
                error_detail = f"Invalid move format: '{move_str}'. Expected UCI format (e.g., 'e2e4'). Python error: {str(ve)}"
                print(f"ERROR: ValueError in move parsing: {error_detail}")
                print(f"DEBUG: move_str={move_str!r}, type={type(move_str)}, len={len(move_str) if move_str else 0}")
                raise HTTPException(
                    status_code=400,
                    detail=error_detail
                )
            
            if move not in board.legal_moves:
                raise HTTPException(
                    status_code=400,
                    detail=f"Illegal move: '{move_str}'. This move is not legal in the current position."
                )
            board.push(move)
        except HTTPException:
            raise
        except Exception as e:
            # Catch any other unexpected errors
            raise HTTPException(
                status_code=400,
                detail=f"Error processing move '{move_str if 'move_str' in locals() else request.move}': {str(e)}"
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

