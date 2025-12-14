# Four Kingdoms Military Chess (四国军棋) AI Project

This project is a Python-based implementation of **Four Kingdoms Military Chess (四国军棋)** with a graphical interface and AI-related components. It is designed as a foundation for building **game logic, visualization, and belief-based AI reasoning** for hidden-information gameplay.

The system clearly separates **game rules**, **board connectivity**, **piece information visibility**, and **UI rendering**, making it suitable for future AI extensions.

---

## Key Concepts

- **Hidden Information (Fog of War)**  
  Each piece has a `reveal` state:
  - `reveal = False`: the piece’s rank/type is hidden from opponents
  - `reveal = True`: the piece’s rank/type is visible

  ⚠️ This is **independent of whether text or graphics are drawn on the board**. Visibility of information and UI rendering are handled by different systems.

- **Four-Player / Two-Player Support**  
  The project supports structured turn management and can be extended from two-player mode to full four-player gameplay.

- **Railway vs Road Movement**  
  The board distinguishes between:
  - **Road (公路线)**: normal movement, one step at a time
  - **Railway (铁路线)**: special movement rules (e.g., engineers can move freely)

---

## Project Structure

```text
.
├── main.py                 # Entry point / debugging utilities
├── game.py                 # Game setup, interaction, and rule enforcement
├── game_state.py           # Game state and turn management
├── two_player_mode.py      # Simplified two-player game logic
├── chessboard.py           # Board representation and piece placement
├── piece.py                # Piece definitions, ranks, and properties
├── routes.py               # Board connectivity and movement rules
├── constants.py            # Global constants and configuration values
├── belief_sampler.py       # Belief sampling for hidden-information AI
├── military_chess_gui.py   # Pygame-based GUI for visualization
├── test.py                 # Testing and manual interaction script
```

---

## Module Overview

### `piece.py`
Defines all chess pieces, including:
- Piece names and ranks
- Special pieces (Flag, Mine, Bomb, Engineer, etc.)
- Ownership and visibility (`reveal`) attributes

### `chessboard.py`
Handles:
- Board layout and valid/invalid cells
- Piece placement and retrieval
- Interaction with movement rules

### `routes.py`
Encodes board connectivity:
- Road vs Railway edges
- Legal movement checks
- Special railway constraints

### `game.py`
Core gameplay logic:
- Pre-battle setup rules
- Move validation
- Capture and elimination rules
- Integration with UI and state manager

### `game_state.py`
Manages:
- Turn order
- Game phases (editing vs playing)
- Player elimination and win conditions

### `two_player_mode.py`
A lightweight mode for:
- Testing mechanics
- Debugging logic without full four-player complexity

### `belief_sampler.py`
AI-oriented module for:
- Sampling possible hidden piece configurations
- Maintaining probabilistic beliefs under partial observability
- Serving as a foundation for decision-making AI

### `military_chess_gui.py`
Provides:
- Pygame-based graphical interface
- Mouse interaction
- Visual rendering of board, pieces, and movement

---

## Running the Project

### Requirements
- Python 3.9+
- `pygame`

Install dependencies:
```bash
pip install pygame
```

### Launch the GUI
```bash
python military_chess_gui.py
```

or run test/debug mode:
```bash
python test.py
```

---

## Design Goals

- **Clear separation of logic and UI**
- **Support for hidden-information AI research**
- **Extensible architecture for four-player gameplay**
- **Faithful modeling of Four Kingdoms Military Chess rules**

---

## Future Work

- Full four-player online gameplay
- AI agents using belief sampling and search
- Self-play training and evaluation
- Replay system and game logging
- Improved GUI and animations

---

## Author Notes

This project is intended as a **research- and AI-oriented implementation** rather than a casual game clone. Code clarity, rule correctness, and extensibility are prioritized over short-term performance.

If you plan to build AI agents on top of this system, start with `belief_sampler.py` and `game_state.py`.

