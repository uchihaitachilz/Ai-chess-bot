"""
Example usage of both AI tools.
Run this to see how to use the chatbot and chess analyzer.
"""

from local_chatbot import LocalChatbot
from chess_pattern_analyzer import ChessPatternAnalyzer
import json


def example_chatbot():
    """Example: Using the local chatbot."""
    print("=" * 60)
    print("EXAMPLE 1: Local AI Chatbot")
    print("=" * 60)
    
    # Create material folder with some content
    import os
    os.makedirs("material", exist_ok=True)
    
    # Add some sample material
    sample_content = """
    Chess Opening Principles:
    1. Control the center
    2. Develop your pieces
    3. Castle early
    4. Don't move the same piece twice in opening
    
    Common Openings:
    - e4 e5: King's Pawn Game
    - d4 d5: Queen's Gambit
    - e4 c5: Sicilian Defense
    """
    
    with open("material/chess_basics.txt", "w") as f:
        f.write(sample_content)
    
    # Initialize chatbot
    chatbot = LocalChatbot(material_folder="material")
    
    # Ask questions
    questions = [
        "What are the opening principles?",
        "Tell me about e4 e5",
        "What is the Sicilian Defense?"
    ]
    
    for question in questions:
        print(f"\nQ: {question}")
        answer = chatbot.chat(question)
        print(f"A: {answer}")


def example_chess_analyzer():
    """Example: Using the chess pattern analyzer."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Chess Pattern Analyzer")
    print("=" * 60)
    
    analyzer = ChessPatternAnalyzer()
    
    # Add some sample games with evaluations
    games = [
        {
            'moves': ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5', 'a7a6'],
            'evaluations': [0.2, 0.1, 0.3, 0.2, 0.4, 0.3]
        },
        {
            'moves': ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'f8c5'],
            'evaluations': [0.2, 0.1, 0.3, 0.2, 0.4, 0.3]
        },
        {
            'moves': ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'd2d4', 'e5d4'],
            'evaluations': [0.2, 0.1, 0.3, 0.2, 0.5, 0.4]
        }
    ]
    
    for game in games:
        analyzer.analyze_game_moves(
            moves=game['moves'],
            evaluations=game['evaluations']
        )
    
    # Generate report
    report = analyzer.generate_report()
    print(report)
    
    # Export to JSON
    analyzer.export_to_json("example_analysis.json")
    print("\n✓ Analysis exported to example_analysis.json")


def example_stockfish_integration():
    """Example: Integrating with Stockfish analysis."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Stockfish Integration")
    print("=" * 60)
    
    # This shows how you could integrate with actual Stockfish output
    # You would run Stockfish on games and save the analysis
    
    sample_stockfish_data = {
        "moves": ["e2e4", "e7e5", "g1f3", "b8c6"],
        "evaluations": [0.2, 0.1, 0.3, 0.2],
        "best_moves": ["e2e4", "e7e5", "g1f3", "b8c6"],
        "depths": [12, 12, 12, 12]
    }
    
    # Save sample data
    with open("sample_stockfish.json", "w") as f:
        json.dump(sample_stockfish_data, f, indent=2)
    
    # Load and analyze
    analyzer = ChessPatternAnalyzer()
    analyzer.load_stockfish_analysis("sample_stockfish.json")
    
    print("✓ Loaded Stockfish analysis")
    print("✓ Use analyzer.generate_report() to see patterns")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("NORMIE AI PROJECTS - EXAMPLES")
    print("=" * 60)
    print("\nThese examples show how to use the AI tools.")
    print("For personal/educational use only!\n")
    
    try:
        example_chess_analyzer()
        example_stockfish_integration()
        print("\n" + "=" * 60)
        print("For chatbot example, run: python local_chatbot.py")
        print("=" * 60)
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure to install requirements: pip install -r requirements.txt")

