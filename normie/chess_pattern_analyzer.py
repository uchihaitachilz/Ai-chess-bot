"""
Chess Pattern Analyzer - Analyze Stockfish data for patterns
Finds repeated moves, common patterns, and strategic insights.

Requirements:
    pip install python-chess pandas numpy
"""

import chess
import chess.engine
import pandas as pd
import json
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
from pathlib import Path
import re


class ChessPatternAnalyzer:
    """
    Analyzes Stockfish analysis data to find patterns:
    - Repeated moves/sequences
    - Common opening patterns
    - Position evaluation patterns
    - Move frequency analysis
    """
    
    def __init__(self):
        self.games_data = []
        self.move_patterns = defaultdict(int)
        self.position_evaluations = []
        self.opening_sequences = []
    
    def load_pgn_file(self, pgn_path: str):
        """Load games from a PGN file."""
        with open(pgn_path, 'r') as f:
            pgn_content = f.read()
        
        # Simple PGN parser (for basic use)
        games = pgn_content.split('\n\n\n')
        for game_text in games:
            if '[Event' in game_text:
                self._parse_game(game_text)
    
    def load_stockfish_analysis(self, analysis_file: str):
        """
        Load Stockfish analysis data.
        Expected format: JSON with moves and evaluations
        {
            "moves": ["e2e4", "e7e5", ...],
            "evaluations": [0.2, 0.1, ...],
            "best_moves": ["e2e4", "e7e5", ...]
        }
        """
        with open(analysis_file, 'r') as f:
            data = json.load(f)
        
        game_data = {
            'moves': data.get('moves', []),
            'evaluations': data.get('evaluations', []),
            'best_moves': data.get('best_moves', []),
            'depths': data.get('depths', [])
        }
        
        self.games_data.append(game_data)
        self._extract_patterns(game_data)
    
    def analyze_game_moves(self, moves: List[str], evaluations: List[float] = None):
        """Analyze a single game's moves."""
        game_data = {
            'moves': moves,
            'evaluations': evaluations or [],
            'best_moves': moves.copy(),
            'depths': []
        }
        self.games_data.append(game_data)
        self._extract_patterns(game_data)
    
    def _parse_game(self, game_text: str):
        """Parse a PGN game (simplified)."""
        # Extract moves (basic implementation)
        moves_match = re.search(r'1\.\s+([^\n]+)', game_text)
        if moves_match:
            moves_str = moves_match.group(1)
            # Simple move extraction (can be improved)
            moves = re.findall(r'\b[a-h][1-8][a-h][1-8][qrnb]?\b', moves_str)
            if moves:
                self.analyze_game_moves(moves)
    
    def _extract_patterns(self, game_data: Dict):
        """Extract patterns from game data."""
        moves = game_data['moves']
        
        # Extract 2-move sequences
        for i in range(len(moves) - 1):
            sequence = f"{moves[i]} -> {moves[i+1]}"
            self.move_patterns[sequence] += 1
        
        # Extract 3-move sequences
        for i in range(len(moves) - 2):
            sequence = f"{moves[i]} -> {moves[i+1]} -> {moves[i+2]}"
            self.move_patterns[sequence] += 1
        
        # Store opening (first 10 moves)
        if len(moves) >= 10:
            opening = " -> ".join(moves[:10])
            self.opening_sequences.append(opening)
        
        # Store evaluations if available
        if game_data.get('evaluations'):
            for eval_score in game_data['evaluations']:
                self.position_evaluations.append(eval_score)
    
    def find_repeated_sequences(self, min_occurrences: int = 3) -> Dict[str, int]:
        """Find move sequences that repeat across games."""
        repeated = {
            seq: count 
            for seq, count in self.move_patterns.items() 
            if count >= min_occurrences
        }
        return dict(sorted(repeated.items(), key=lambda x: x[1], reverse=True))
    
    def analyze_opening_patterns(self) -> Dict[str, int]:
        """Analyze common opening patterns."""
        opening_counter = Counter()
        
        for opening in self.opening_sequences:
            # Extract first 3 moves as opening signature
            first_moves = " -> ".join(opening.split(" -> ")[:3])
            opening_counter[first_moves] += 1
        
        return dict(opening_counter.most_common(10))
    
    def find_common_moves(self, position: str = None) -> Dict[str, int]:
        """
        Find most common moves.
        If position is provided, find moves from that position.
        """
        move_counter = Counter()
        
        for game in self.games_data:
            for move in game['moves']:
                if position:
                    # Filter moves that could come from this position
                    # (simplified - would need board state matching)
                    move_counter[move] += 1
                else:
                    move_counter[move] += 1
        
        return dict(move_counter.most_common(20))
    
    def analyze_evaluation_trends(self) -> Dict:
        """Analyze evaluation patterns."""
        if not self.position_evaluations:
            return {"error": "No evaluation data available"}
        
        evals = self.position_evaluations
        
        return {
            "average_evaluation": sum(evals) / len(evals),
            "max_evaluation": max(evals),
            "min_evaluation": min(evals),
            "evaluation_range": max(evals) - min(evals),
            "positive_evaluations": sum(1 for e in evals if e > 0),
            "negative_evaluations": sum(1 for e in evals if e < 0),
            "neutral_evaluations": sum(1 for e in evals if e == 0)
        }
    
    def find_blunder_patterns(self, threshold: float = -2.0) -> List[Dict]:
        """
        Find positions where evaluation drops significantly (potential blunders).
        threshold: Minimum evaluation drop to consider it a blunder
        """
        blunders = []
        
        for game_idx, game in enumerate(self.games_data):
            evals = game.get('evaluations', [])
            moves = game.get('moves', [])
            
            for i in range(1, len(evals)):
                eval_drop = evals[i] - evals[i-1]
                if eval_drop <= threshold:
                    blunders.append({
                        'game': game_idx,
                        'move_number': i,
                        'move': moves[i] if i < len(moves) else 'unknown',
                        'evaluation_drop': eval_drop,
                        'before_eval': evals[i-1],
                        'after_eval': evals[i]
                    })
        
        return sorted(blunders, key=lambda x: x['evaluation_drop'])
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report."""
        report = []
        report.append("=" * 60)
        report.append("CHESS PATTERN ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Repeated sequences
        report.append("TOP REPEATED MOVE SEQUENCES:")
        report.append("-" * 60)
        repeated = self.find_repeated_sequences(min_occurrences=2)
        for seq, count in list(repeated.items())[:10]:
            report.append(f"  {seq}: {count} times")
        report.append("")
        
        # Opening patterns
        report.append("COMMON OPENING PATTERNS:")
        report.append("-" * 60)
        openings = self.analyze_opening_patterns()
        for opening, count in list(openings.items())[:5]:
            report.append(f"  {opening}: {count} games")
        report.append("")
        
        # Common moves
        report.append("MOST COMMON MOVES:")
        report.append("-" * 60)
        common_moves = self.find_common_moves()
        for move, count in list(common_moves.items())[:10]:
            report.append(f"  {move}: {count} times")
        report.append("")
        
        # Evaluation trends
        if self.position_evaluations:
            report.append("EVALUATION TRENDS:")
            report.append("-" * 60)
            trends = self.analyze_evaluation_trends()
            for key, value in trends.items():
                report.append(f"  {key}: {value}")
            report.append("")
        
        # Blunders
        report.append("POTENTIAL BLUNDERS (Big Evaluation Drops):")
        report.append("-" * 60)
        blunders = self.find_blunder_patterns(threshold=-1.5)
        for blunder in blunders[:5]:
            report.append(f"  Move {blunder['move_number']}: {blunder['move']} "
                         f"(Drop: {blunder['evaluation_drop']:.2f})")
        
        return "\n".join(report)
    
    def export_to_json(self, output_file: str):
        """Export analysis results to JSON."""
        data = {
            'repeated_sequences': self.find_repeated_sequences(),
            'opening_patterns': self.analyze_opening_patterns(),
            'common_moves': self.find_common_moves(),
            'evaluation_trends': self.analyze_evaluation_trends(),
            'blunders': self.find_blunder_patterns()
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Analysis exported to {output_file}")


def analyze_stockfish_output(stockfish_file: str):
    """
    Analyze Stockfish output file.
    Expected format: One analysis per line
    """
    analyzer = ChessPatternAnalyzer()
    
    with open(stockfish_file, 'r') as f:
        for line in f:
            # Parse Stockfish output (adjust based on your format)
            if 'bestmove' in line.lower():
                # Extract move from Stockfish output
                parts = line.split()
                if 'bestmove' in parts:
                    idx = parts.index('bestmove')
                    if idx + 1 < len(parts):
                        move = parts[idx + 1]
                        analyzer.analyze_game_moves([move])
    
    return analyzer


def main():
    """Example usage."""
    print("=" * 60)
    print("Chess Pattern Analyzer")
    print("=" * 60)
    
    analyzer = ChessPatternAnalyzer()
    
    # Example: Analyze some sample games
    print("\nAnalyzing sample games...")
    
    # Sample game 1
    analyzer.analyze_game_moves(
        moves=['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1b5', 'a7a6'],
        evaluations=[0.2, 0.1, 0.3, 0.2, 0.4, 0.3]
    )
    
    # Sample game 2 (similar opening)
    analyzer.analyze_game_moves(
        moves=['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'f8c5'],
        evaluations=[0.2, 0.1, 0.3, 0.2, 0.4, 0.3]
    )
    
    # Sample game 3 (different opening)
    analyzer.analyze_game_moves(
        moves=['d2d4', 'd7d5', 'c2c4', 'e7e6', 'b1c3', 'g8f6'],
        evaluations=[0.1, 0.0, 0.2, 0.1, 0.3, 0.2]
    )
    
    # Generate report
    report = analyzer.generate_report()
    print("\n" + report)
    
    # Export to JSON
    analyzer.export_to_json("chess_analysis.json")
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()

