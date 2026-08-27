import streamlit as st
import time
import random
import pandas as pd

# --- CORE CLASSES (From your script) ---
class Client:
    def __init__(self, client_id, base_limit):
        self.client_id = client_id
        self.base_limit = base_limit
        self.allocated_limit_mbps = base_limit
        self.current_traffic_mbps = 0
        self.buffer = 0 

class Router:
    def __init__(self, total_capacity):
        self.total_capacity = total_capacity
        self.available_pool = total_capacity
        self.clients = []
        
    def add_client(self, client):
        self.clients.append(client)
        self.available_pool -= client.base_limit

# --- UI SETUP ---
st.set_page_config(page_title="Elastic Router Sim", layout="wide")
st.title("🌐 Virtual Elastic Router Dashboard")
st.write("Dynamic Bandwidth Allocation to prevent Bufferbloat.")

# Layout columns for metrics
col1, col2 = st.columns(2)
pool_metric = col1.empty()
buffer_metric = col2.empty()

# Placeholder for our live data table
data_placeholder = st.empty()

if st.button("Start Live Simulation"):
    # Initialize Network
    my_router = Router(1000)
    for i in range(1, 6):
        my_router.add_client(Client(f"Client_{i}", 100))
        
    # Run a 15-second simulation
    for tick in range(15):
        # 1. Reset & Generate Traffic
        my_router.available_pool = my_router.total_capacity - sum(c.base_limit for c in my_router.clients)
        
        for client in my_router.clients:
            client.allocated_limit_mbps = client.base_limit
            # 15% chance of spike, otherwise normal
            if random.random() < 0.15:
                client.current_traffic_mbps = random.randint(150, 250)
            else:
                client.current_traffic_mbps = random.randint(10, 90)
                
            # Add waiting buffer to demand
            client.current_traffic_mbps += client.buffer
            client.buffer = 0
            
        # 2. Elastic Allocation
        total_buffer = 0
        client_data = []
        
        for client in my_router.clients:
            if client.current_traffic_mbps > client.allocated_limit_mbps:
                extra_needed = client.current_traffic_mbps - client.allocated_limit_mbps
                if my_router.available_pool >= extra_needed:
                    client.allocated_limit_mbps += extra_needed
                    my_router.available_pool -= extra_needed
                elif my_router.available_pool > 0:
                    client.allocated_limit_mbps += my_router.available_pool
                    client.buffer += (client.current_traffic_mbps - client.allocated_limit_mbps)
                    my_router.available_pool = 0
                else:
                    client.buffer += (client.current_traffic_mbps - client.allocated_limit_mbps)
            
            total_buffer += client.buffer
            
            # Save data for UI
            client_data.append({
                "Port": client.client_id,
                "Incoming Traffic (Mbps)": client.current_traffic_mbps,
                "Allocated Limit (Mbps)": client.allocated_limit_mbps,
                "Buffer Status": f"{client.buffer} Mbps" if client.buffer > 0 else "Clear ✅"
            })
            
        # 3. Update the Streamlit UI
        pool_metric.metric("Shared Bandwidth Pool", f"{my_router.available_pool} Mbps")
        if total_buffer == 0:
            buffer_metric.metric("Total Network Congestion", "0 Mbps", delta="Optimal Flow", delta_color="normal")
        else:
            buffer_metric.metric("Total Network Congestion", f"{total_buffer} Mbps", delta="Traffic Jam!", delta_color="inverse")
            
        df = pd.DataFrame(client_data)
        data_placeholder.dataframe(df, use_container_width=True)
        
        time.sleep(1) # Wait 1 second before next cycle
        
    st.success("Simulation Complete!")