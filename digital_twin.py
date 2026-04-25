"""
DIGITAL TWIN - Smart City Waste Management Simulation
Simulates virtual bins across a city with route optimization
"""

import numpy as np
import networkx as nx
import folium
import streamlit as st
from streamlit_folium import folium_static
import heapq

class VirtualBinNetwork:
    def __init__(self):
        # Create virtual bins across a city grid
        self.bins = {
            'BIN001': {'location': 'Downtown', 'lat': 40.7128, 'lon': -74.0060, 'fill': 0, 'capacity': 100},
            'BIN002': {'location': 'Residential A', 'lat': 40.7135, 'lon': -74.0075, 'fill': 0, 'capacity': 100},
            'BIN003': {'location': 'Park', 'lat': 40.7110, 'lon': -74.0045, 'fill': 0, 'capacity': 100},
            'BIN004': {'location': 'School', 'lat': 40.7140, 'lon': -74.0080, 'fill': 0, 'capacity': 100},
            'BIN005': {'location': 'Hospital', 'lat': 40.7100, 'lon': -74.0050, 'fill': 0, 'capacity': 100},
            'BIN006': {'location': 'Mall', 'lat': 40.7150, 'lon': -74.0090, 'fill': 0, 'capacity': 100},
            'BIN007': {'location': 'Office Complex', 'lat': 40.7090, 'lon': -74.0030, 'fill': 0, 'capacity': 100},
            'BIN008': {'location': 'Train Station', 'lat': 40.7160, 'lon': -74.0100, 'fill': 0, 'capacity': 100},
        }
        
        # Create graph for route optimization
        self.graph = nx.Graph()
        
        # Add edges between bins (roads)
        bin_ids = list(self.bins.keys())
        for i in range(len(bin_ids)):
            for j in range(i+1, len(bin_ids)):
                lat1, lon1 = self.bins[bin_ids[i]]['lat'], self.bins[bin_ids[i]]['lon']
                lat2, lon2 = self.bins[bin_ids[j]]['lat'], self.bins[bin_ids[j]]['lon']
                distance = np.sqrt((lat1-lat2)**2 + (lon1-lon2)**2) * 111  # Convert to km
                self.graph.add_edge(bin_ids[i], bin_ids[j], weight=distance)
    
    def update_bin_fill(self, bin_id, increment=1):
        """Update virtual bin fill level"""
        if bin_id in self.bins:
            self.bins[bin_id]['fill'] = min(self.bins[bin_id]['fill'] + increment, self.bins[bin_id]['capacity'])
            return self.bins[bin_id]['fill']
        return None
    
    def get_full_bins(self, threshold=80):
        """Get bins that are above threshold"""
        return [bid for bid, data in self.bins.items() if data['fill'] >= threshold]
    
    def optimize_route(self, depot='BIN001'):
        """Find optimal collection route using Dijkstra's algorithm"""
        full_bins = self.get_full_bins()
        
        if not full_bins:
            return None
        
        # Simple nearest neighbor route
        route = [depot]
        unvisited = set(full_bins)
        current = depot
        
        while unvisited:
            nearest = min(unvisited, key=lambda x: nx.shortest_path_length(self.graph, current, x, weight='weight'))
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        route.append(depot)  # Return to depot
        
        # Calculate total distance
        total_distance = 0
        for i in range(len(route)-1):
            total_distance += nx.shortest_path_length(self.graph, route[i], route[i+1], weight='weight')
        
        return {'route': route, 'total_distance': total_distance, 'bins_to_collect': len(full_bins)}
    
    def create_map(self):
        """Create interactive map of virtual bins"""
        center_lat = np.mean([data['lat'] for data in self.bins.values()])
        center_lon = np.mean([data['lon'] for data in self.bins.values()])
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
        
        for bin_id, data in self.bins.items():
            fill_percent = (data['fill'] / data['capacity']) * 100
            
            # Color based on fill level
            if fill_percent >= 80:
                color = 'red'
            elif fill_percent >= 50:
                color = 'orange'
            else:
                color = 'green'
            
            folium.CircleMarker(
                location=[data['lat'], data['lon']],
                radius=10,
                popup=f"{bin_id}<br>{data['location']}<br>Fill: {fill_percent:.0f}%",
                color=color,
                fill=True,
                fill_color=color
            ).add_to(m)
        
        # Add route optimization
        route_data = self.optimize_route()
        if route_data:
            route_coords = []
            for bin_id in route_data['route']:
                route_coords.append([self.bins[bin_id]['lat'], self.bins[bin_id]['lon']])
            
            folium.PolyLine(
                route_coords,
                color='blue',
                weight=3,
                popup=f"Route Distance: {route_data['total_distance']:.2f} km"
            ).add_to(m)
        
        return m
    
    def detect_contamination(self, waste_type, bin_id, expected_type=None):
        """Detect if wrong waste type is placed in bin"""
        if expected_type and waste_type != expected_type:
            return {
                'alert': True,
                'message': f"⚠️ CONTAMINATION ALERT: {waste_type.upper()} detected in {bin_id} (Expected: {expected_type.upper()})",
                'severity': 'high'
            }
        return {'alert': False}

# Streamlit integration
def create_logistics_dashboard():
    st.markdown("## 🗺️ Digital Twin - Smart City Waste Network")
    
    # Initialize digital twin
    if 'digital_twin' not in st.session_state:
        st.session_state.digital_twin = VirtualBinNetwork()
    
    twin = st.session_state.digital_twin
    
    # Main display
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📍 Virtual Bin Map")
        m = twin.create_map()
        folium_static(m, width=600, height=400)
    
    with col2:
        st.markdown("### 🗑️ Bin Status")
        
        for bin_id, data in twin.bins.items():
            fill_percent = (data['fill'] / data['capacity']) * 100
            color = "🔴" if fill_percent >= 80 else "🟡" if fill_percent >= 50 else "🟢"
            st.write(f"{color} **{bin_id}** ({data['location']}): {fill_percent:.0f}%")
    
    # Route optimization
    st.markdown("### 🚛 Collection Route Optimization")
    
    if st.button("🔄 Calculate Optimal Route"):
        route_data = twin.optimize_route()
        
        if route_data:
            st.success(f"✅ Optimal route found!")
            st.write(f"**Bins to collect:** {route_data['bins_to_collect']}")
            st.write(f"**Total distance:** {route_data['total_distance']:.2f} km")
            st.write(f"**Route:** {' → '.join(route_data['route'])}")
            
            # Estimated fuel savings
            fuel_saved = route_data['total_distance'] * 0.1  # Assume 0.1 L/km saved
            st.metric("Fuel Savings", f"{fuel_saved:.1f} L", delta="Optimized route")
        else:
            st.info("No bins need collection at this time")
    
    # Contamination alerts
    st.markdown("### ⚠️ Contamination Detection")
    st.caption("System alerts when wrong waste type is placed in designated bins")
    
    bin_to_test = st.selectbox("Select bin", list(twin.bins.keys()))
    waste_to_test = st.selectbox("Test waste type", ['plastic', 'glass', 'metal', 'paper', 'cardboard', 'trash'])
    
    if st.button("Simulate Contamination"):
        # Simulate contamination detection
        expected = 'paper' if 'Paper' in twin.bins[bin_to_test]['location'] else None
        alert = twin.detect_contamination(waste_to_test, bin_to_test, expected)
        
        if alert['alert']:
            st.error(alert['message'])
        else:
            st.success(f"✅ Clean detection: {waste_to_test} accepted in {bin_to_test}")
    
    return twin