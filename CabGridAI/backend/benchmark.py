from rich.console import Console
from rich.table import Table
import logging

console = Console()

class BenchmarkPanel:
    _ui_callback = None

    @classmethod
    def set_ui_callback(cls, callback):
        cls._ui_callback = callback

    @staticmethod
    def print_dispatch_comparison(bfs_time, bfs_nodes, bf_time, bf_nodes):
        table = Table(title="Dispatch Algorithm Benchmark", style="cyan")
        table.add_column("Algorithm", style="magenta")
        table.add_column("Time Taken (ms)", justify="right", style="green")
        table.add_column("Nodes Traversed", justify="right", style="yellow")
        
        table.add_row("BFS (Shortest Hop)", f"{bfs_time * 1000:.2f}", str(bfs_nodes))
        table.add_row("Brute Force (Dijkstra to All)", f"{bf_time * 1000:.2f}", str(bf_nodes))
        
        console.print(table)
        
    @classmethod
    def log_process_state_transition(cls, cab_id, old_state, new_state, old_process, new_process):
        def get_name(e): return e.name if hasattr(e, 'name') else str(e)
        msg = f"CAB EVENT: {cab_id} State: {get_name(old_state)} -> {get_name(new_state)} | Process: {get_name(old_process)} -> {get_name(new_process)}"
        
        console.print(f"[bold yellow]CAB EVENT:[/bold yellow] [cyan]{cab_id}[/cyan] State: [blue]{get_name(old_state)}[/blue] -> [green]{get_name(new_state)}[/green] | Process: [red]{get_name(old_process)}[/red] -> [magenta]{get_name(new_process)}[/magenta]")
        
        if cls._ui_callback:
            cls._ui_callback(msg)
        
    @classmethod
    def log_surge(cls, multiplier):
        msg = f"⚠️ SURGE PRICING ACTIVE: {multiplier}x ⚠️"
        console.print(f"[bold red]{msg}[/bold red]")
        if cls._ui_callback:
            cls._ui_callback(msg)
