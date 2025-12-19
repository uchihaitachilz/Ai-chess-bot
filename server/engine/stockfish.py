"""
Stockfish engine integration using python-chess.
Handles engine initialization and move calculation.
"""

import chess
import chess.engine
import os
import asyncio
import shutil
from typing import Tuple

# Stockfish engine path (configurable via environment variable)
# Try multiple common locations
ENGINE_DEPTH = int(os.getenv("ENGINE_DEPTH", "12"))


def _find_stockfish_path() -> str:
    """Find Stockfish executable in common locations."""
    # Check environment variable first
    env_path = os.getenv("ENGINE_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    
    # Check for engine_path.txt file (created by install script)
    home_dir = os.path.expanduser("~")
    engine_path_file = f"{home_dir}/stockfish/engine_path.txt"
    if os.path.exists(engine_path_file):
        try:
            with open(engine_path_file, 'r') as f:
                saved_path = f.read().strip()
                if saved_path and os.path.exists(saved_path) and os.access(saved_path, os.X_OK):
                    return saved_path
        except Exception:
            pass  # Fall through to other checks
    
    # Common locations (check user-installed first, then system)
    common_paths = [
        f"{home_dir}/stockfish/stockfish",  # User-installed via script (Render)
        "/usr/games/stockfish",  # Debian/Ubuntu standard location
        "/usr/bin/stockfish",
        "/opt/homebrew/bin/stockfish",
        "/usr/local/bin/stockfish",
    ]
    
    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    # Try to find in PATH
    stockfish_path = shutil.which("stockfish")
    if stockfish_path:
        return stockfish_path
    
    # Default fallback (user-installed location)
    default_path = f"{home_dir}/stockfish/stockfish"
    return default_path


def _get_best_move_sync(board_fen: str) -> Tuple[str, float]:
    """Synchronously get the best move using python-chess SimpleEngine."""
    board = chess.Board(board_fen)
    engine_path = _find_stockfish_path()
    
    # Verify the path exists and is executable before trying to use it
    if not os.path.exists(engine_path):
        # Try to find it in PATH as a last resort
        stockfish_in_path = shutil.which("stockfish")
        if stockfish_in_path:
            engine_path = stockfish_in_path
        else:
            # List all possible locations for debugging (including home directory)
            home_dir = os.path.expanduser("~")
            engine_path_file = f"{home_dir}/stockfish/engine_path.txt"
            all_paths = [
                f"{home_dir}/stockfish/stockfish",  # User-installed location
                engine_path_file,  # Path file from install script
                "/usr/games/stockfish",
                "/usr/bin/stockfish",
                "/opt/homebrew/bin/stockfish",
                "/usr/local/bin/stockfish",
            ]
            existing_paths = [p for p in all_paths if os.path.exists(p)]
            executable_paths = [p for p in all_paths if os.path.exists(p) and os.access(p, os.X_OK)]
            
            # Check if engine_path.txt exists and what it contains
            path_file_info = ""
            if os.path.exists(engine_path_file):
                try:
                    with open(engine_path_file, 'r') as f:
                        saved_path = f.read().strip()
                        path_file_info = f" (contains: {saved_path}, exists: {os.path.exists(saved_path) if saved_path else False})"
                except Exception as e:
                    path_file_info = f" (read error: {e})"
            
            raise RuntimeError(
                f"Stockfish not found. Checked: {all_paths}. "
                f"Existing paths: {existing_paths}. "
                f"Executable paths: {executable_paths}. "
                f"Path file{path_file_info}. "
                f"HOME: {home_dir}. "
                f"PATH contains: {os.environ.get('PATH', 'N/A')}. "
                f"Please ensure Stockfish is installed."
            )
    
    # Verify it's executable
    if not os.access(engine_path, os.X_OK):
        raise RuntimeError(
            f"Stockfish found at {engine_path} but is not executable. "
            f"Please run: chmod +x {engine_path}"
        )
    
    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        
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
        raise RuntimeError(
            f"Failed to get best move from Stockfish at {engine_path}. "
            f"Make sure Stockfish is installed. Error: {str(e)}"
        )


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
