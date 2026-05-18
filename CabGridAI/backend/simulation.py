import time
import threading
from .cab_manager import CabState, ProcessState
from .benchmark import BenchmarkPanel

class SimulationEngine:
    def __init__(self, cab_manager, city_graph):
        self.cab_manager = cab_manager
        self.graph = city_graph
        self.running = False
        self.thread = None
        self.update_callback = None

    def start(self, update_callback=None):
        self.update_callback = update_callback
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def dispatch_cab(self, cab, route_path):
        # The route path should be a list of nodes.
        cab.path = list(route_path)
        
        old_state, old_process = cab.state, cab.process_state
        cab.transition_state(CabState.DISPATCHED, ProcessState.NEW)
        BenchmarkPanel.log_process_state_transition(cab.cab_id, old_state, CabState.DISPATCHED, old_process, ProcessState.NEW)
        
        def delay_dispatch():
            time.sleep(0.5) # Simulate dispatch delay
            old_state2, old_process2 = cab.state, cab.process_state
            cab.transition_state(CabState.EN_ROUTE, ProcessState.RUNNING)
            BenchmarkPanel.log_process_state_transition(cab.cab_id, old_state2, CabState.EN_ROUTE, old_process2, ProcessState.RUNNING)
            
        threading.Thread(target=delay_dispatch, daemon=True).start()

    def _loop(self):
        pos = self.graph.get_pos()
        while self.running:
            needs_update = False
            for cab in self.cab_manager.get_all_cabs():
                if cab.state == CabState.EN_ROUTE and cab.path:
                    needs_update = True
                    
                    if cab.progress >= 1.0:
                        cab.progress = 0.0
                        cab.current_node = cab.path.pop(0)
                        
                        if not cab.path:
                            old_state, old_process = cab.state, cab.process_state
                            cab.transition_state(CabState.COMPLETED, ProcessState.TERMINATED)
                            BenchmarkPanel.log_process_state_transition(cab.cab_id, old_state, CabState.COMPLETED, old_process, ProcessState.TERMINATED)
                            
                            # Give it a moment to show completion, then back to idle
                            def reset_cab(c):
                                time.sleep(2)
                                os, op = c.state, c.process_state
                                c.transition_state(CabState.IDLE, ProcessState.READY)
                                BenchmarkPanel.log_process_state_transition(c.cab_id, os, CabState.IDLE, op, ProcessState.READY)
                            
                            threading.Thread(target=reset_cab, args=(cab,), daemon=True).start()
                            continue
                            
                    if cab.path:
                        next_node = cab.path[0]
                        # interpolate between current_node and next_node
                        x1, y1 = pos[cab.current_node]
                        x2, y2 = pos[next_node]
                        
                        # Speed based on edge
                        edge_data = self.graph.graph.get_edge_data(cab.current_node, next_node)
                        speed = 0.05
                        if edge_data:
                            # Higher speed limit + lower traffic = faster progress
                            speed = (edge_data['speed_limit'] / 60.0) / edge_data['traffic'] * 0.08
                        
                        cab.progress = min(1.0, cab.progress + speed)
                        cab.current_x = x1 + (x2 - x1) * cab.progress
                        cab.current_y = y1 + (y2 - y1) * cab.progress
                        
            if needs_update and self.update_callback:
                self.update_callback()
                
            time.sleep(0.05) # ~20 FPS
