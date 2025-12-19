# Quick Start Guide

## Setup

1. Install dependencies:
```bash
cd normie
pip install -r requirements.txt
```

## Local AI Chatbot

### How it works:
- Uses **RAG (Retrieval Augmented Generation)** - no training needed!
- Loads your material into a vector database
- When you ask a question, it finds relevant content and generates an answer
- Everything runs locally - no API calls

### Usage:

1. Create a `material/` folder
2. Add your text files (.txt or .md) with your content
3. Run:
```bash
python local_chatbot.py
```

### Example:
```python
from local_chatbot import LocalChatbot

chatbot = LocalChatbot(material_folder="material")
response = chatbot.chat("What are chess opening principles?")
print(response)
```

### Is it easy?
- **Yes!** No complex training needed
- Just add your material files and chat
- Uses pre-trained models (no GPU required for small models)

### Legal Note:
- ✅ Personal use: Fine
- ✅ Educational use: Fine  
- ❌ Commercial use: Only if you own copyright to all material

## Chess Pattern Analyzer

### How it works:
- Analyzes Stockfish evaluation data
- Finds repeated move sequences
- Identifies common patterns
- Detects blunders (big evaluation drops)

### Usage:

```python
from chess_pattern_analyzer import ChessPatternAnalyzer

analyzer = ChessPatternAnalyzer()

# Add games with Stockfish evaluations
analyzer.analyze_game_moves(
    moves=['e2e4', 'e7e5', 'g1f3'],
    evaluations=[0.2, 0.1, 0.3]
)

# Generate report
report = analyzer.generate_report()
print(report)

# Export to JSON
analyzer.export_to_json("analysis.json")
```

### Features:
- Find repeated move sequences
- Analyze opening patterns
- Detect common moves
- Find blunders (evaluation drops)
- Export analysis to JSON

## Example

Run the example file:
```bash
python example_usage.py
```

## Model Options

For the chatbot, you can use different models:

**Small (faster, less powerful):**
- `microsoft/DialoGPT-small`
- `gpt2`

**Medium (balanced):**
- `microsoft/DialoGPT-medium` (default)

**Large (slower, more powerful - needs more RAM):**
- `microsoft/DialoGPT-large`
- `gpt2-medium`

Change in `local_chatbot.py`:
```python
chatbot = LocalChatbot(model_name="gpt2")  # Use smaller model
```

