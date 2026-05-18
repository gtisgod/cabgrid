import tkinter as tk
import os
import sys

# Ensure backend and frontend are accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.graph import CityGraph
from backend.cab_manager import CabManager
from backend.simulation import SimulationEngine
from frontend.app import CabGridApp
from rich.console import Console

console = Console()

def main():
    console.print("[bold green]Starting CabGrid AI...[/bold green]")
    
    # Initialize Graph
    console.print("Generating City Graph...")
    city_graph = CityGraph()
    city_graph.load_graph()
    console.print(f"Graph loaded with [cyan]{len(city_graph.get_nodes())}[/cyan] nodes and [cyan]{len(city_graph.graph.edges)}[/cyan] edges.")

    # Initialize Cab Manager
    console.print("Initializing Cabs...")
    cab_manager = CabManager(city_graph, num_cabs=15)
    
    # Initialize Simulation Engine
    simulation = SimulationEngine(cab_manager, city_graph)

    # Initialize Tkinter
    root = tk.Tk()
    
    # This prevents Matplotlib from causing threading errors on some OS
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, simulation))
    
    app = CabGridApp(root, city_graph, cab_manager, simulation)
    
    console.print("[bold green]System Ready. Waiting for user input via GUI.[/bold green]")
    root.mainloop()

def on_closing(root, simulation):
    simulation.stop()
    root.destroy()
    sys.exit()

if __name__ == "__main__":
    main()
