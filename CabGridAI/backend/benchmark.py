from rich.console import Console
from rich.table import Table
import logging

console = Console()

class BenchmarkPanel:
    @staticmethod
    def print_dispatch_comparison(bfs_time, bfs_nodes, bf_time, bf_nodes):
        table = Table(title="Dispatch Algorithm Benchmark", style="cyan")
        table.add_column("Algorithm", style="magenta")
        table.add_column("Time Taken (ms)", justify="right", style="green")
        table.add_column("Nodes Traversed", justify="right", style="yellow")
        
        table.add_row("BFS (Shortest Hop)", f"{bfs_time * 1000:.2f}", str(bfs_nodes))
        table.add_row("Brute Force (Dijkstra to All)", f"{bf_time * 1000:.2f}", str(bf_nodes))
        
        console.print(table)
        
    @staticmethod
    def log_process_state_transition(cab_id, old_state, new_state, old_process, new_process):
        console.print(f"[bold yellow]CAB EVENT:[/bold yellow] [cyan]{cab_id}[/cyan] State: [blue]{old_state}[/blue] -> [green]{new_state}[/green] | Process: [red]{old_process}[/red] -> [magenta]{new_process}[/magenta]")
        
    @staticmethod
    def log_surge(multiplier):
        console.print(f"[bold red]⚠️ SURGE PRICING ACTIVE: {multiplier}x ⚠️[/bold red]")
