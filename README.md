# Wizard101 Pet Dance Game Bot

The go to Bronze Medal getter and Pet Promenade game winner. A Python script that automatically plays the Wizard101 pet dance game using computer vision and automated inputs.

## Features

- Uses computer vision to detect arrow sequences and navigate the game interface
- Plays multiple games with configurable parameters for number of games and pet snacks
- Feeds pets with selected snack after each game

## Requirements

- Python 3.9+
- Windows OS

## Installation

### Standard Installation (with Git)

1. Clone the repository:

```bash
git clone https://github.com/dostalek/dance-gamer.git
```

2. Navigate into the project directory:

```bash
cd dance-gamer
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Alternate Installation (without Git)

1. Download the repository as a ZIP file by clicking [here](https://github.com/dostalek/dance-gamer/archive/refs/heads/main.zip).
2. Extract the contents of the ZIP file to a location of your choice.
3. Open a command prompt or terminal and navigate to the extracted folder. It should be named dance-gamer-main:

```bash
cd path/to/your/dance-gamer-main
```

4. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Setup Instructions

### Game Settings

1. Fullscreen -> OFF
2. Resolution -> 800x600
3. UI Size -> REGULAR

### Pet Dance Game

1. Run the script before:
   - entering the dance game sigil
   - selecting the dance game level
2. Enter the dance game sigil
3. Avoid keyboard and mouse inputs during runtime
4. Press the "[" key to exit the program at any time

## Usage

```bash
python main.py -n <number_games> [-t <truncate_sequences>] [-s <snack_position>]
```

### Arguments

- `-n, --number`: **(Required)** Number of games to play (1-99).
- `-t, --truncate`: (Optional) Number of sequences before ending the game (2-5). Defaults to 5.
- `-s, --snack`: (Optional) Snack position to select (1-5), with 1 being the first snack on the left, and 5 being the last snack on the right of the first snacks page. Defaults to no snack.

### Basic Example

```bash
python main.py -n 25
```

This will play 25 full games (5 sequences matched), without feeding a snack.

### Advanced Example

```bash
python main.py -n 5 -t 2 -s 1
```

This will play 5 games, stop matching after 2 sequences, and feed the snack at position 1.

## How It Works

1. **Screen Capture**: Takes screenshots of the Wizard101 client area
2. **Template Matching**: Uses OpenCV to detect arrow sequences and GUI elements
3. **Input Simulation**: Replicates the sequence using keyboard input
4. **Game Navigation**: Automatically navigates menus and feeds pets after each game

## Resources

The `resources/` directory contains template images used for computer vision:

- Arrow templates (up, down, left, right)
- GUI element templates (buttons)

## Disclaimer

Obligatory "this is against Wizard101 ToS, and you could be banned for it, but probably not."
