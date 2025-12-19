"""
Stockfish engine integration using python-chess.
Handles engine initialization and move calculation.
"""

import chess
import chess.engine
import os
import asyncio
from typing import Tuple

# Stockfish engine path (configurable via environment variable)
ENGINE_PATH = os.getenv("ENGINE_PATH", "/usr/bin/stockfish")
ENGINE_DEPTH = int(os.getenv("ENGINE_DEPTH", "12"))


def _get_best_move_sync(board_fen: str) -> Tuple[str, float]:
    """Synchronously get the best move."""
    board = chess.Board(board_fen)
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
