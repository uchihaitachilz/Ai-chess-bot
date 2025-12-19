"""
AI commentary generation system.
Uses OpenAI-compatible API if available, otherwise falls back to rule-based commentary.
"""

import os
import random
from typing import Optional
import chess

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
USE_OPENAI = bool(OPENAI_API_KEY)

# SadisticTushi piece names
PIECE_NAMES = {
    'N': 'Pony',  # Knight
    'B': 'Juicer',  # Bishop
    'R': 'Monster Cookie',  # Rook
    'Q': 'Fatty',  # Queen
    'K': 'Chicken',  # King
    'P': 'Candy',  # Pawn
}

# SadisticTushi catchphrases and commentary templates - EXTREMELY TOXIC BUT FUNNY
COMMENTARY_TEMPLATES = {
    "excellent": [
        "Looks so cheeky! That's actually... wait, did you just make a good move? That's why you are NOT the dummy for once, kid!",
        "Not bad, dummy! You're making me work for it. Dis is da whey! But don't get too excited.",
        "Alright, I see what you're going for here. That's... surprisingly decent. Are you sure you meant to do that?",
        "Interesting choice. The position is getting complex. You're actually thinking? That's new!",
    ],
    "good": [
        "Solid move. Nothing flashy, but it works. Can't fault you for that, dummy. Barely.",
        "Standard play. The engine approves... barely. You're not completely hopeless, kid.",
        "Reasonable. I mean, it's not terrible. That's the best I can say, dummy.",
        "Okay, that's a move. It exists. Moving on before you mess it up.",
    ],
    "questionable": [
        "Hmm, that's... a choice. Let's see where this leads, dummy. Probably nowhere good.",
        "Interesting. Not what I would have done, but okay. That's why you the dummy and I'm not, kid.",
        "That move exists, I suppose. Moving forward... into what, I'm not sure.",
        "Well, it's legal. That's something, kid. The bar is on the floor and you're still limbo dancing under it.",
    ],
    "bad": [
        "Oof. That's not ideal, dummy. The engine is laughing at you. We'll work with it... somehow.",
        "Yikes. The engine is not a fan of that one, kid. That's why you are the dummy!",
        "That's... certainly a move. Not a great one, but a move. Like, technically it's chess, I guess?",
        "Hmm, the evaluation just dropped. Interesting strategy, dummy. If your strategy is losing, you're nailing it!",
    ],
    "blunder": [
        "Oh no! That's why you are the dummy! Spilling the tomato ketchup everywhere! The position is bleeding, kid!",
        "Yikes! That's a blunder of epic proportions, dummy! The engine is having a field day with this one!",
        "Ouch. The position just collapsed like a house of cards. That's why you the dummy! Thanks for the free win!",
        "That's a blunder that would make beginners cry, kid. You're really out here doing the most... to lose!",
    ],
    "check": [
        "Check! Focus on the Lollipop, dummy! The Chicken is in danger! Things are getting SPICY!",
        "Check! The pressure is on the Chicken, kid! Time to panic... I mean, defend!",
        "Check! Time to defend, dummy! Or don't, I'm not your mom. That's why you the dummy!",
    ],
    "checkmate": [
        "Fried the chicken! 🔥🐓 That's why you are the dummy! Checkmate, kid! Game over!",
        "Checkmate! Fried the chicken! That's a wrap, dummy. Well played... said no one ever!",
        "Checkmate! Game over, kid. The Chicken is cooked! That's why you are the dummy!",
    ],
    "pony": [
        "HOP IN THE PONY! Let's go, dummy!",
        "Hoping the Pony! That's the way, kid!",
        "Bring out the Pony! Dis is da whey!",
    ],
    "juicer": [
        "Bring oudda juucerrr! Let's get spicy, dummy!",
        "Bring out the Juicer! Time to cause chaos, kid!",
        "Bishop to juicer! Things are about to get wild, dummy!",
    ],
    "candy": [
        "Taking the candy! Get diabetes, dummy!",
        "Free candies! That's why you are the dummy for falling for it, kid!",
        "Candy captured! Sweet moves lead to sweet defeats, dummy!",
    ],
}


def get_move_quality(prev_eval: float, new_eval: float, is_white: bool) -> str:
    """
    Determine the quality of a move based on evaluation change.
    
    Args:
        prev_eval: Evaluation before the move
        new_eval: Evaluation after the move
        is_white: Whether the player is white
        
    Returns:
        Quality category string
    """
    # Adjust evaluation based on side to move
    if not is_white:
        prev_eval = -prev_eval
        new_eval = -new_eval
    
    eval_change = new_eval - prev_eval
    
    # Categorize move quality
    if eval_change < -2.0:
        return "blunder"
    elif eval_change < -0.5:
        return "bad"
    elif eval_change < 0.0:
        return "questionable"
    elif eval_change < 0.5:
        return "good"
    else:
        return "excellent"


async def generate_commentary_openai(
    board: chess.Board,
    player_move: str,
    engine_move: str,
    evaluation: float
) -> str:
    """
    Generate commentary using OpenAI-compatible API.
    
    Args:
        board: Current chess board
        player_move: The move the player made
        engine_move: The move the engine will make
        evaluation: Position evaluation
        
    Returns:
        Generated commentary string
    """
    try:
        import httpx
        
        # Determine move quality
        board_before = board.copy()
        board_before.pop()  # Remove player's move to get previous position
        
        # Simple evaluation approximation for previous position
        # (In a real scenario, you'd want to store previous eval)
        prev_eval = evaluation + 0.3  # Rough approximation
        quality = get_move_quality(prev_eval, evaluation, board.turn == chess.BLACK)
        
        # Build prompt with SadisticTushi style - EXTREMELY TOXIC BUT FUNNY
        prompt = f"""You are SadisticTushi - a chess commentator who is EXTREMELY TOXIC, SARCASATIC, WITTY, and SAVAGE but in a funny way.
You MUST use his catchphrases and vocabulary:
- Pieces: Pony (knight), Juicer (bishop), Monster Cookie (rook), Fatty (queen), Chicken (king), Candy (pawn), Lollipop (king)
- Phrases: "dummy", "kid", "That's why you are the dummy", "Dis is da whey!", "Looks so cheeky", 
  "Fried the chicken" (checkmate), "Get diabetes" (capturing pieces), "HOP IN THE PONY", 
  "Bring out the Juicer", "Bring oudda juucerrr", "Focus on the Lollipop" (target king), 
  "Spilling the tomato ketchup" (blunder), "That's why you the dummy", "Giga dummy", "Copycat"

The player just played: {player_move}
The engine will respond with: {engine_move}
Move quality: {quality}
Position evaluation: {evaluation:.2f} pawns

Generate EXTREMELY TOXIC, SARCASATIC, WITTY commentary. Be SAVAGE but FUNNY. 
- Roast the MOVE mercilessly with sarcasm
- Use EXTREME sarcasm and wit
- Be TOXIC but in a playful, funny way
- Use SadisticTushi's catchphrases naturally throughout
- Make it BRUTAL but ENTERTAINING
- No actual abuse - just savage roasts of the move
- Keep it to 1-2 sentences maximum
- Make it EXTREMELY sarcastic and witty"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                    "messages": [
                        {"role": "system", "content": "You are SadisticTushi - EXTREMELY TOXIC, SARCASATIC, WITTY, and SAVAGE but FUNNY. Use catchphrases: Pony, Juicer, Monster Cookie, Fatty, Chicken, Candy, Lollipop, 'dummy', 'kid', 'That's why you are the dummy', 'Dis is da whey!', 'Fried the chicken', 'HOP IN THE PONY', 'Bring out the Juicer', 'Spilling the tomato ketchup'. Be BRUTALLY SARCASATIC, WITTY, and TOXIC but in a playful, entertaining way. Roast MOVES mercilessly with extreme sarcasm."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 120,
                    "temperature": 1.0,
                },
                timeout=10.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                commentary = data["choices"][0]["message"]["content"].strip()
                return commentary
            else:
                # Fall back to rule-based if API fails
                return generate_commentary_fallback(board, player_move, engine_move, evaluation)
                
    except Exception as e:
        # Fall back to rule-based on any error
        print(f"OpenAI API error: {e}")
        return generate_commentary_fallback(board, player_move, engine_move, evaluation)


def get_piece_name(move_uci: str, board: chess.Board) -> str:
    """Get SadisticTushi piece name from move."""
    try:
        move = chess.Move.from_uci(move_uci)
        piece = board.piece_at(move.from_square)
        if piece:
            return PIECE_NAMES.get(piece.symbol().upper(), 'piece')
    except:
        pass
    return 'piece'


def generate_commentary_fallback(
    board: chess.Board,
    player_move: str,
    engine_move: str,
    evaluation: float
) -> str:
    """
    Generate rule-based commentary in SadisticTushi style as fallback.
    
    Args:
        board: Current chess board
        player_move: The move the player made
        engine_move: The move the engine will make
        evaluation: Position evaluation
        
    Returns:
        Generated commentary string
    """
    # Check for checkmate first
    if board.is_checkmate():
        return random.choice(COMMENTARY_TEMPLATES["checkmate"])
    
    # Check for check
    if board.is_check():
        return random.choice(COMMENTARY_TEMPLATES["check"])
    
    # Determine move quality (simplified)
    if abs(evaluation) > 5.0:
        quality = "blunder" if evaluation < 0 else "excellent"
    elif abs(evaluation) > 2.0:
        quality = "bad" if evaluation < 0 else "good"
    else:
        quality = "questionable" if abs(evaluation) > 1.0 else "good"
    
    # Get piece names for moves
    player_piece = get_piece_name(player_move, board)
    engine_piece = get_piece_name(engine_move, board)
    
    # Special handling for specific piece moves
    commentary_parts = []
    
    # Check if it's a knight move
    if player_piece == 'Pony':
        if random.random() < 0.3:
            commentary_parts.append(random.choice(COMMENTARY_TEMPLATES["pony"]))
    
    # Check if it's a bishop move
    if player_piece == 'Juicer':
        if random.random() < 0.3:
            commentary_parts.append(random.choice(COMMENTARY_TEMPLATES["juicer"]))
    
    # Check if it's a pawn capture
    board_before = board.copy()
    board_before.pop()
    try:
        move_obj = chess.Move.from_uci(player_move)
        if board_before.piece_at(move_obj.from_square) and board_before.piece_at(move_obj.from_square).piece_type == chess.PAWN:
            if board_before.piece_at(move_obj.to_square):  # Capturing
                if random.random() < 0.4:
                    commentary_parts.append(random.choice(COMMENTARY_TEMPLATES["candy"]))
    except:
        pass
    
    # Select base commentary based on quality
    if quality in COMMENTARY_TEMPLATES:
        base_commentary = random.choice(COMMENTARY_TEMPLATES[quality])
    else:
        base_commentary = random.choice(COMMENTARY_TEMPLATES["good"])
    
    # Combine commentary
    if commentary_parts:
        return f"{' '.join(commentary_parts)} {base_commentary}"
    
    # Add evaluation context for extreme positions
    if abs(evaluation) > 3.0:
        if evaluation > 0:
            base_commentary += " The engine is feeling confident, dummy."
        else:
            base_commentary += " That's why you are the dummy!"
    
    return base_commentary


async def generate_commentary(
    board: chess.Board,
    player_move: str,
    engine_move: str,
    evaluation: float
) -> str:
    """
    Main commentary generation function.
    Uses OpenAI if available, otherwise falls back to rule-based.
    
    Args:
        board: Current chess board
        player_move: The move the player made
        engine_move: The move the engine will make
        evaluation: Position evaluation
        
    Returns:
        Generated commentary string
    """
    if USE_OPENAI:
        return await generate_commentary_openai(board, player_move, engine_move, evaluation)
    else:
        return generate_commentary_fallback(board, player_move, engine_move, evaluation)

