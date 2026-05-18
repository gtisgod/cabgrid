class PricingEngine:
    def __init__(self, base_fare=5.0, per_km=2.0, per_min=0.5):
        self.base_fare = base_fare
        self.per_km = per_km
        self.per_min = per_min

    def calculate_surge(self, cab_manager):
        all_cabs = cab_manager.get_all_cabs()
        if not all_cabs:
            return 1.0
        
        busy_cabs = sum(1 for cab in all_cabs if cab.state != "IDLE")
        utilization = busy_cabs / len(all_cabs)
        
        # Surge trigger > 0.6 utilization
        if utilization > 0.6:
            return round(1.0 + (utilization - 0.6) * 2.5, 1) # Max surge ~2.0x
        return 1.0

    def estimate_fare(self, distance, time, surge_multiplier):
        fare = self.base_fare + (distance * self.per_km) + (time * self.per_min)
        return round(fare * surge_multiplier, 2)
