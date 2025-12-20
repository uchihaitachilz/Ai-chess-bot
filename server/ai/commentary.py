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
        "Wow, that's... actually good? Who are you and what did you do with the dummy?",
        "Okay, okay. That's a solid move. I see you, kid. Don't let it go to your head though!",
        "Hmm, interesting. That actually works well here. Are you sure you're not cheating, dummy?",
        "That's a proper move right there. The engine is nodding in approval... barely.",
    ],
    "good": [
        "Solid move. Nothing flashy, but it works. Can't fault you for that, dummy. Barely.",
        "Standard play. The engine approves... barely. You're not completely hopeless, kid.",
        "Reasonable. I mean, it's not terrible. That's the best I can say, dummy.",
        "Okay, that's a move. It exists. Moving on before you mess it up.",
        "That'll work. Nothing special, but it's playable. Keep going, dummy.",
        "Decent. Not impressive, but acceptable. That's the bar, kid.",
        "Standard stuff. Nothing to write home about, but it works.",
        "Okay move. The position stays playable. Don't mess it up now!",
    ],
    "questionable": [
        "Hmm, that's... a choice. Let's see where this leads, dummy. Probably nowhere good.",
        "Interesting. Not what I would have done, but okay. That's why you the dummy and I'm not, kid.",
        "That move exists, I suppose. Moving forward... into what, I'm not sure.",
        "Well, it's legal. That's something, kid. The bar is on the floor and you're still limbo dancing under it.",
        "That's... an interesting decision. Let's see how this plays out, dummy.",
        "Hmm, okay. Not ideal, but we'll see. That's why you are the dummy!",
        "Interesting choice. The engine is confused, and so am I, kid.",
        "That's a move. Not a great one, but a move nonetheless.",
    ],
    "bad": [
        "Oof. That's not ideal, dummy. The engine is laughing at you. We'll work with it... somehow.",
        "Yikes. The engine is not a fan of that one, kid. That's why you are the dummy!",
        "That's... certainly a move. Not a great one, but a move. Like, technically it's chess, I guess?",
        "Hmm, the evaluation just dropped. Interesting strategy, dummy. If your strategy is losing, you're nailing it!",
        "Ouch. That's not good, kid. The position is getting worse. That's why you are the dummy!",
        "That hurts. The engine is shaking its head, dummy. What were you thinking?",
        "Yikes. That move didn't help at all. The position is suffering, kid!",
        "That's rough, dummy. The evaluation is looking grim. Keep trying though!",
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


def get_board_context(board: chess.Board, player_move: str, engine_move: str) -> dict:
    """
    Extract rich contextual information about the current position.
    Helps generate more varied and contextual commentary.
    """
    context = {
        "move_number": len(board.move_stack) + 1,
        "is_opening": len(board.move_stack) < 10,
        "is_middlegame": 10 <= len(board.move_stack) < 30,
        "is_endgame": len(board.move_stack) >= 30,
        "pieces_on_board": len([p for p in board.piece_map().values()]),
        "is_check": board.is_check(),
        "is_checkmate": board.is_checkmate(),
        "captures_available": len(list(board.legal_moves)) if board.legal_moves else 0,
    }
    
    # Analyze player move
    if player_move and player_move.strip():
        try:
            move_obj = chess.Move.from_uci(player_move)
            from_piece = board.piece_at(move_obj.to_square)
            context["player_piece"] = PIECE_NAMES.get(from_piece.symbol().upper() if from_piece else "", "piece")
            context["player_captured"] = board.piece_at(move_obj.to_square) is None and move_obj.to_square != move_obj.from_square
        except:
            pass
    
    # Analyze engine move
    try:
        engine_move_obj = chess.Move.from_uci(engine_move)
        engine_board_copy = board.copy()
        engine_board_copy.push(engine_move_obj)
        context["engine_causes_check"] = engine_board_copy.is_check()
        from_piece = board.piece_at(engine_move_obj.from_square)
        context["engine_piece"] = PIECE_NAMES.get(from_piece.symbol().upper() if from_piece else "", "piece")
    except:
        pass
    
    return context


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
        
        # Get rich context for varied commentary
        context = get_board_context(board, player_move, engine_move)
        
        # Determine move quality
        # If player_move is empty, this is the engine's first move (no previous position to evaluate)
        if not player_move or player_move.strip() == "":
            # Engine's first move - use a neutral quality
            quality = "good"
            prev_eval = 0.0  # Starting position is balanced
        else:
            board_before = board.copy()
            if len(board.move_stack) > 0:
                board_before.pop()  # Remove player's move to get previous position
            # Simple evaluation approximation for previous position
            # (In a real scenario, you'd want to store previous eval)
            prev_eval = evaluation + 0.3  # Rough approximation
            quality = get_move_quality(prev_eval, evaluation, board.turn == chess.BLACK)
        
        # Build rich, contextual prompt that varies each time
        game_phase = "opening" if context["is_opening"] else ("middlegame" if context["is_middlegame"] else "endgame")
        
        if player_move and player_move.strip():
            move_details = f"""
Move #{context['move_number']} - {game_phase.upper()}:
- Player played: {player_move} ({context.get('player_piece', 'piece')})
- Engine responds: {engine_move} ({context.get('engine_piece', 'piece')})
- Move quality: {quality}
- Position evaluation: {evaluation:.2f} pawns
- Pieces remaining: {context['pieces_on_board']}
- Current check: {context['is_check']}
- Engine move causes check: {context.get('engine_causes_check', False)}"""
            roast_instruction = "Roast the player's move with UNIQUE, CREATIVE sarcasm - avoid repeating the same jokes or phrases from previous moves."
            roast_target = "of this specific move - be creative and reference what makes THIS move unique (piece type, position, timing, etc.)"
        else:
            move_details = f"""
Move #1 - OPENING:
- Engine opening move: {engine_move} ({context.get('engine_piece', 'piece')})
- Position evaluation: {evaluation:.2f} pawns
- Starting the game!"""
            roast_instruction = "Comment on the opening move with unique, creative commentary - make it different from typical opening comments."
            roast_target = "about this specific opening - reference the piece moved or strategy implied, be creative!"
        
        # Add random variation instruction to ensure uniqueness
        import random
        variation_instructions = [
            "Use a DIFFERENT angle/approach than you've used before",
            "Reference something specific about THIS position that's unique",
            "Vary your delivery style - try a different sarcastic tone",
            "Focus on a different aspect (timing, piece choice, position, etc.)",
            "Make an observation that's unique to this exact moment in the game"
        ]
        
        prompt = f"""You are SadisticTushi - a chess commentator who is EXTREMELY TOXIC, SARCASATIC, WITTY, and SAVAGE but FUNNY.

CRITICAL: Generate UNIQUE commentary that doesn't repeat phrases or jokes from previous moves. Be CREATIVE and VARIED.

Your vocabulary (use NATURALLY, don't force every phrase):
- Pieces: Pony (knight), Juicer (bishop), Monster Cookie (rook), Fatty (queen), Chicken (king), Candy (pawn), Lollipop (king)
- Phrases: "dummy", "kid", "That's why you are the dummy", "Dis is da whey!", "Looks so cheeky", 
  "Fried the chicken" (checkmate), "Get diabetes" (capturing pieces), "HOP IN THE PONY", 
  "Bring out the Juicer", "Bring oudda juucerrr", "Focus on the Lollipop" (target king), 
  "Spilling the tomato ketchup" (blunder), "That's why you the dummy", "Giga dummy", "Copycat"

{move_details}

{roast_instruction}
{random.choice(variation_instructions)}
- Use EXTREME sarcasm and wit - but make it FRESH and UNIQUE to this specific move
- Be TOXIC but in a playful, funny way
- Reference specific details from the move details above to make it contextual
- Keep it to 1-2 sentences maximum
- Make it EXTREMELY sarcastic, witty, and ORIGINAL - avoid clichés and repetition"""

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
                        {"role": "system", "content": "You are SadisticTushi - EXTREMELY TOXIC, SARCASATIC, WITTY, and SAVAGE but FUNNY. CRITICAL: Generate UNIQUE, VARIED commentary. Never repeat the same jokes, phrases, or commentary style. Each move deserves fresh, creative roasts. Use catchphrases naturally: Pony, Juicer, Monster Cookie, Fatty, Chicken, Candy, Lollipop, 'dummy', 'kid', 'That's why you are the dummy', 'Dis is da whey!', 'Fried the chicken', 'HOP IN THE PONY', 'Bring out the Juicer', 'Spilling the tomato ketchup'. Be BRUTALLY SARCASATIC, WITTY, and TOXIC but in a playful, entertaining way. ALWAYS reference specific details from the move/position to make commentary contextual and unique."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 150,
                    "temperature": 1.2,  # Higher temperature for more creativity and variety
                    "top_p": 0.95,  # Nucleus sampling for more diverse outputs
                    "frequency_penalty": 0.5,  # Penalize repetition
                    "presence_penalty": 0.3,  # Encourage new topics/phrases
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
    
    # Get board context for variety
    context = get_board_context(board, player_move, engine_move)
    
    # Determine move quality (simplified)
    if abs(evaluation) > 5.0:
        quality = "blunder" if evaluation < 0 else "excellent"
    elif abs(evaluation) > 2.0:
        quality = "bad" if evaluation < 0 else "good"
    else:
        quality = "questionable" if abs(evaluation) > 1.0 else "good"
    
    # Handle engine's first move (no player move)
    if not player_move or player_move.strip() == "":
        # Engine's opening move - varied commentary based on piece moved
        engine_piece = get_piece_name(engine_move, board)
        opening_commentary = [
            f"Opening with {engine_move}! Bringing out the {engine_piece} early. Let's see what you got, dummy!",
            f"First move: {engine_move}. The {engine_piece} enters the game! Time to play chess, kid!",
            f"Engine starts with {engine_move}. Your move, dummy! The {engine_piece} is ready to cause chaos!",
            f"{engine_move}! The {engine_piece} makes its debut. Try not to blunder on move 2, kid!",
            f"Game on! {engine_move} to start. The {engine_piece} is in play. That's why you are the dummy if you mess this up!",
            f"Here we go! {engine_move} opens the game. {engine_piece} movement detected. Don't disappoint, dummy!",
        ]
        return random.choice(opening_commentary)
    
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
    if len(board.move_stack) > 0:
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
    
    # Add move-specific context to vary commentary
    move_number = len(board.move_stack)
    is_opening = move_number < 10
    is_endgame = move_number >= 30
    pieces_count = context.get("pieces_on_board", len([p for p in board.piece_map().values()]))
    
    context_additions = []
    
    if is_opening and random.random() < 0.3:
        context_additions.append("Still in the opening phase, dummy!")
    elif is_endgame and random.random() < 0.3:
        context_additions.append("Endgame time, kid! Every move counts now!")
    
    if pieces_count < 10 and random.random() < 0.4:
        context_additions.append("Pieces are dropping like flies!")
    
    # Combine commentary with variations
    if commentary_parts:
        final_commentary = f"{' '.join(commentary_parts)} {base_commentary}"
    else:
        final_commentary = base_commentary
    
    # Add context if available
    if context_additions and random.random() < 0.5:
        final_commentary += " " + random.choice(context_additions)
    
    # Add evaluation context for extreme positions (less frequently)
    if abs(evaluation) > 3.0 and random.random() < 0.6:
        if evaluation > 0:
            final_commentary += " The engine is feeling confident, dummy."
        else:
            final_commentary += " That's why you are the dummy!"
    
    return final_commentary


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


async def generate_improvement_tips(
    move: str,
    evaluation: float,
    previous_evaluation: float,
    is_white: bool = True
) -> str:
    """
    Generate improvement tips when player makes a bad move.
    Uses the same toxic but funny tone as commentary.
    
    Args:
        move: The move the player made
        evaluation: Current position evaluation
        previous_evaluation: Previous position evaluation
        is_white: Whether the player is white
        
    Returns:
        Improvement tips string
    """
    # Adjust evaluation based on side
    if not is_white:
        prev_eval = -previous_evaluation
        curr_eval = -evaluation
    else:
        prev_eval = previous_evaluation
        curr_eval = evaluation
    
    eval_change = curr_eval - prev_eval
    is_bad = eval_change < -0.5
    
    if not is_bad:
        return ""  # Don't show tips for good moves
    
    try:
        import httpx
        
        # Determine severity
        if eval_change < -2.0:
            severity = "blunder"
            tip_style = "URGENT - major mistake"
        elif eval_change < -1.0:
            severity = "bad move"
            tip_style = "significant error"
        else:
            severity = "questionable move"
            tip_style = "minor mistake"
        
        if USE_OPENAI:
            prompt = f"""You are SadisticTushi, a chess coach helping a player improve. The player just made a {severity} (move: {move}). 
The evaluation dropped by {abs(eval_change):.2f} pawns.

Generate a HELPFUL, SIMPLE improvement tip in TUSHI's style - toxic but funny, but also genuinely educational.
- Use simple, actionable advice
- Reference the move or position
- Use catchphrases naturally: "dummy", "kid", "That's why you are the dummy", "Dis is da whey!"
- Keep it to 1-2 sentences
- Focus on what they should do better next time
- Be encouraging despite the roasts

Example style: "That's why you are the dummy! Next time, focus on piece development before moving your pieces randomly, kid. Dis is da whey to improve!"

Generate the tip now:"""
            
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
                            {"role": "system", "content": "You are SadisticTushi - a chess coach who roasts but also helps players improve. Use catchphrases: 'dummy', 'kid', 'That's why you are the dummy', 'Dis is da whey!'. Give SIMPLE, ACTIONABLE improvement tips in a toxic but funny and encouraging way."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 100,
                        "temperature": 1.1,
                        "frequency_penalty": 0.4,
                        "presence_penalty": 0.2,
                    },
                    timeout=10.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
        
        # Fallback to rule-based tips
        return generate_improvement_tips_fallback(move, eval_change)
        
    except Exception as e:
        print(f"Error generating improvement tips: {e}")
        return generate_improvement_tips_fallback(move, eval_change)


def generate_improvement_tips_fallback(move: str, eval_change: float) -> str:
    """Generate fallback improvement tips."""
    tips = []
    
    if eval_change < -2.0:
        tips = [
            "That's why you are the dummy! That was a huge blunder, kid! Next time, double-check your piece safety before moving. Dis is da whey to avoid mistakes!",
            "Ouch! That's a major mistake, dummy. Always think about what your opponent can do after your move. Think before you move, kid!",
            "Spilling the tomato ketchup everywhere! That's a big blunder. Focus on protecting your pieces and controlling the center, dummy!",
        ]
    elif eval_change < -1.0:
        tips = [
            "That's not ideal, dummy! Try to develop your pieces and control important squares. Dis is da whey to improve, kid!",
            "That move hurt your position, kid. Next time, think about piece coordination and avoid weakening your king's safety. That's why you are the dummy!",
            "Not great, dummy! Focus on piece activity and avoid moving the same piece multiple times in the opening. Learn from this, kid!",
        ]
    else:
        tips = [
            "Hmm, that's questionable, dummy. Try to think about your opponent's threats and keep your pieces active. Dis is da whey, kid!",
            "That move could be better, kid. Focus on developing pieces and controlling the center. That's why you are the dummy if you keep making these moves!",
        ]
    
    import random
    return random.choice(tips)

