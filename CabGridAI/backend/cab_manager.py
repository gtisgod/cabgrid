import random
import logging

class CabState:
    IDLE = "IDLE"
    DISPATCHED = "DISPATCHED"
    EN_ROUTE = "EN_ROUTE"
    COMPLETED = "COMPLETED"

class ProcessState:
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    TERMINATED = "TERMINATED"

class Cab:
    def __init__(self, cab_id, node):
        self.cab_id = cab_id
        self.current_node = node
        
        # Path and routing
        self.target_node = None
        self.path = []
        
        # States
        self.state = CabState.IDLE
        self.process_state = ProcessState.READY
        
        # Attributes
        self.rating = round(random.uniform(3.5, 5.0), 1)
        self.cab_type = random.choice(["Sedan", "SUV", "Hatchback", "Premium"])
        
        # Position interpolation for smooth UI
        self.current_x = None
        self.current_y = None
        self.progress = 0.0 # 0 to 1 along the current edge
        
    def transition_state(self, new_state, new_process_state):
        self.state = new_state
        self.process_state = new_process_state

class CabManager:
    def __init__(self, city_graph, num_cabs=15):
        self.graph = city_graph
        self.cabs = []
        self._initialize_cabs(num_cabs)

    def _initialize_cabs(self, num_cabs):
        nodes = self.graph.get_nodes()
        if not nodes:
            return
            
        pos = self.graph.get_pos()
        for i in range(num_cabs):
            node = random.choice(nodes)
            cab = Cab(f"CAB-{i+1:03d}", node)
            if node in pos:
                cab.current_x, cab.current_y = pos[node]
            self.cabs.append(cab)

    def get_available_cabs(self):
        return [cab for cab in self.cabs if cab.state == CabState.IDLE]
        
    def get_cab_by_id(self, cab_id):
        for cab in self.cabs:
            if cab.cab_id == cab_id:
                return cab
        return None
        
    def get_all_cabs(self):
        return self.cabs
