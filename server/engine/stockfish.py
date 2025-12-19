"""
Stockfish engine integration using python-chess.
Handles engine initialization and move calculation.
"""

import chess
import chess.engine
import os
import asyncio
from typing import Tuple

# Try to use Python stockfish package first, fallback to system installation
try:
    from stockfish import Stockfish as PyStockfish
    USE_PYTHON_STOCKFISH = True
except ImportError:
    USE_PYTHON_STOCKFISH = False

# Stockfish engine path (configurable via environment variable)
ENGINE_PATH = os.getenv("ENGINE_PATH", "/usr/bin/stockfish")
ENGINE_DEPTH = int(os.getenv("ENGINE_DEPTH", "12"))


def _get_best_move_sync(board_fen: str) -> Tuple[str, float]:
    """Synchronously get the best move."""
    board = chess.Board(board_fen)
    
    # Try Python stockfish package first (works on Render without system installation)
    if USE_PYTHON_STOCKFISH:
        try:
            sf = PyStockfish()
            sf.depth = ENGINE_DEPTH
            sf.set_fen_position(board_fen)
            best_move = sf.get_best_move()
            
            if not best_move:
                raise ValueError("No best move returned")
            
            # Apply the move and get evaluation of new position
            board.push(chess.Move.from_uci(best_move))
            sf.set_fen_position(board.fen())
            eval_after = sf.get_evaluation()
            
            # Convert evaluation to pawns
            if eval_after['type'] == 'mate':
                evaluation = 100.0 if eval_after['value'] > 0 else -100.0
            else:
                # Convert centipawns to pawns
                evaluation = float(eval_after['value']) / 100.0
            
            return best_move, evaluation
        except Exception as e:
            print(f"Python Stockfish failed: {e}, falling back to system Stockfish")
            # Continue to fallback
    
    # Fallback to system Stockfish (python-chess)
    try:
        engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
        
        try:
            limit = chess.engine.Limit(depth=ENGINE_DEPTH)
            
            # Get the best move (synchronous)
            result = engine.play(board, limit)
            
            # Apply the engine's move to get the new position
            board_copy = board.copy()
            board_copy.push(result.move)
            
            # Analyze the position after the engine's move
            info = engine.analyse(board_copy, limit)
            
            # Extract evaluation
            score = info["score"]
            white_score = score.white()
            
            # Convert to pawns
            if white_score.is_mate():
                mate_score = white_score.mate()
                evaluation = 100.0 if mate_score > 0 else -100.0
            else:
                cp_score = white_score.score()
                evaluation = float(cp_score) / 100.0 if cp_score is not None else 0.0
            
            return result.move.uci(), evaluation
        finally:
            engine.quit()
    except Exception as e:
        raise RuntimeError(f"Both Python Stockfish and system Stockfish failed. Error: {str(e)}")


async def get_best_move(board: chess.Board) -> Tuple[str, float]:
    """
    Get the best move from Stockfish for the given board position.
    
    Args:
        board: The chess board position
        
    Returns:
        Tuple of (move in UCI format, evaluation in centipawns)
    """
    try:
        # Run the synchronous function in an executor
        # Use asyncio.to_thread if available (Python 3.9+), otherwise use run_in_executor
        if hasattr(asyncio, 'to_thread'):
            return await asyncio.to_thread(_get_best_move_sync, board.fen())
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _get_best_move_sync, board.fen())
    except Exception as e:
        error_msg = str(e)
        # Provide more helpful error message
        if "can't be used in 'await' expression" in error_msg:
            raise RuntimeError(
                f"Error initializing Stockfish engine. "
                f"Make sure Stockfish is installed at {ENGINE_PATH} and the path is correct. "
                f"Original error: {error_msg}"
            )
        raise RuntimeError(f"Error getting best move from Stockfish: {error_msg}")
