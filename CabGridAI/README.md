# CabGrid AI

CabGrid AI is a comprehensive, production-quality intelligent cab dispatch and route optimization system built in Python.

## Features

- **Realistic City Generation**: Generates an irregular 2D grid resembling city blocks with traffic, speed limits, and distance weightings.
- **Dijkstra's Routing Engine**: Calculates 4 distinct routes:
  - Shortest (Distance)
  - Fastest (Time/Traffic)
  - Eco (Fuel)
  - Optimal (Blended metrics)
- **Cab Dispatching Benchmark**: Compares finding nearest cabs using:
  - BFS (Shortest hop count)
  - Brute Force Dijkstra (Exact distance calculation)
- **Surge Pricing Engine**: Dynamically calculates fare multiplier based on fleet utilization (idle vs. active cabs).
- **Process State Simulation**: Cabs act as OS processes transitioning through states (NEW, READY, RUNNING, WAITING, TERMINATED) alongside ride states (IDLE, DISPATCHED, EN_ROUTE, COMPLETED).
- **Beautiful GUI**: Modern dark/neon-themed Tkinter + Matplotlib frontend.
- **Live Ride Simulation**: Cabs physically move across the map in real-time on a separate thread, providing smooth animation without blocking the UI.

## Architecture

- `backend/graph.py`: City Map generation using `networkx`.
- `backend/routing_engine.py`: Pathfinding algorithms.
- `backend/dispatch_engine.py`: BFS and DFS dispatch algorithms.
- `backend/pricing_engine.py`: Dynamic surge calculations.
- `backend/simulation.py`: Multithreaded cab movement orchestrator.
- `frontend/app.py`: Tkinter UI layout.
- `frontend/visualization.py`: Matplotlib canvas rendering.

## Setup and Installation

1. Ensure you have Python 3.9+ installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Usage

1. Select a **Pickup Node** and a **Destination Node** from the dropdowns on the left panel.
2. Click **Find Routes**.
3. You will see up to four distinct routes based on different optimization metrics. Select one.
4. A benchmark will automatically run comparing BFS cab search with Brute-Force cab search, with results displayed in your terminal.
5. Nearby available cabs will appear in the UI. Click **Book** on a cab.
6. Watch the live animation on the map as the cab is dispatched and travels along the route. Check the terminal for colored logs indicating OS process state transitions.
