import streamlit as st
import time
import json
import random

# --- MOCK DATA: Lumen Product Catalog ---
CATALOG = {
    "10G_Port": {"sku": "LUM-PRT-10G", "price_mrc": 500, "desc": "10 Gbps Ethernet Port"},
    "100G_Port": {"sku": "LUM-PRT-100G", "price_mrc": 1200, "desc": "100 Gbps Ethernet Port"},
    "Cloud_Azure": {"sku": "LUM-CX-AZURE", "price_mrc": 300, "desc": "Lumen Cloud Connect to Azure"},
    "Cloud_AWS": {"sku": "LUM-CX-AWS", "price_mrc": 300, "desc": "Lumen Cloud Connect to AWS"},
    "DDoS_Basic": {"sku": "LUM-SEC-DDOS-B", "price_mrc": 800, "desc": "Basic DDoS Mitigation"}
}

# --- AI SIMULATION FUNCTIONS ---
# In a real hackathon, replace these with actual API calls to Gemini/OpenAI
def parse_requirements_with_llm(user_input):
    """Simulates an LLM extracting entities from natural language."""
    time.sleep(1.5) # Simulate latency
    reqs = []
    user_input = user_input.lower()
    
    if "10g" in user_input: reqs.append("10G_Port")
    elif "100g" in user_input: reqs.append("100G_Port")
    else: reqs.append("10G_Port") # Default
        
    if "azure" in user_input: reqs.append("Cloud_Azure")
    if "aws" in user_input: reqs.append("Cloud_AWS")
    if "ddos" in user_input or "security" in user_input: reqs.append("DDoS_Basic")
        
    return reqs

def generate_bom_and_quote(extracted_reqs):
    bom = []
    total_mrc = 0
    for req in extracted_reqs:
        item = CATALOG[req]
        bom.append(item)
        total_mrc += item["price_mrc"]
    return bom, total_mrc

def mock_lumen_provisioning_api(bom):
    """Simulates translating the BOM into Lumen NaaS API calls."""
    payload = {
        "order_id": f"LUM-{random.randint(10000,99999)}",
        "action": "PROVISION",
        "services": [item["sku"] for item in bom],
        "status": "INITIATED"
    }
    return payload

# --- STREAMLIT UI ---
st.set_page_config(page_title="Lumen Quote-to-Provision AI", layout="wide")

st.title("🌐 Customer Quote-to-Provision Assistant")
st.markdown("*Lumen Hackathon Prototype - AI-driven NaaS Orchestration*")

# Initialize session state for multi-step flow
if "step" not in st.session_state:
    st.session_state.step = "intake"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display Chat History
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# STEP 1: Natural Language Intake
if st.session_state.step == "intake":
    user_query = st.chat_input("Describe your network requirements (e.g., 'I need a 10G connection to Azure with DDoS protection').")
    
    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
            
        with st.chat_message("assistant"):
            with st.spinner("Analyzing requirements & querying Lumen inventory..."):
                extracted_reqs = parse_requirements_with_llm(user_query)
                bom, total_price = generate_bom_and_quote(extracted_reqs)
                
                st.session_state.bom = bom
                st.session_state.total_price = total_price
                st.session_state.step = "quote_approval"
                st.rerun()

# STEP 2: Quote Approval & BOM Review
if st.session_state.step == "quote_approval":
    with st.chat_message("assistant"):
        st.markdown("### 📋 Generated Bill of Materials & Quote")
        st.markdown("I have translated your requirements into the following Lumen architecture:")
        
        st.table(st.session_state.bom)
        st.success(f"**Estimated Monthly Recurring Cost (MRC): ${st.session_state.total_price}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve & Provision Network", use_container_width=True):
                st.session_state.step = "provisioning"
                st.rerun()
        with col2:
            if st.button("❌ Reject / Modify", use_container_width=True):
                st.session_state.step = "intake"
                st.rerun()

# STEP 3: Automated Provisioning
if st.session_state.step == "provisioning":
    with st.chat_message("assistant"):
        st.markdown("### ⚙️ Executing Zero-Touch Provisioning")
        
        with st.status("Translating BOM into Lumen NaaS API Payloads...", expanded=True) as status:
            time.sleep(1)
            st.write("Generating JSON configuration...")
            api_payload = mock_lumen_provisioning_api(st.session_state.bom)
            st.json(api_payload)
            
            time.sleep(1.5)
            st.write("POST /api/v1/network/provision ... HTTP 202 Accepted")
            
            time.sleep(1)
            st.write("Running automated validation scripts (latency & routing check)...")
            
            status.update(label="Provisioning Complete & Validated!", state="complete", expanded=False)
        
        st.balloons()
        st.success("Your infrastructure is online and ready for traffic.")
        if st.button("Start New Request"):
            st.session_state.step = "intake"
            st.session_state.chat_history = []
            st.rerun()