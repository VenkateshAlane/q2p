import streamlit as st
import time
import json
import random
import os
import urllib.request
import re

# --- MOCK DATA: Lumen Product Catalog ---
CATALOG = {
    # Ethernet ports
    "1G_Port": {"sku": "LUM-PRT-1G", "price_mrc": 150, "desc": "1 Gbps Ethernet Port", "category": "Port"},
    "10G_Port": {"sku": "LUM-PRT-10G", "price_mrc": 500, "desc": "10 Gbps Ethernet Port", "category": "Port"},
    "100G_Port": {"sku": "LUM-PRT-100G", "price_mrc": 1200, "desc": "100 Gbps Ethernet Port", "category": "Port"},
    "400G_Port": {"sku": "LUM-PRT-400G", "price_mrc": 3500, "desc": "400 Gbps Ethernet Port", "category": "Port"},
    # Cloud connectivity
    "Cloud_Azure": {"sku": "LUM-CX-AZURE", "price_mrc": 300, "desc": "Lumen Cloud Connect to Azure", "category": "Cloud"},
    "Cloud_AWS": {"sku": "LUM-CX-AWS", "price_mrc": 300, "desc": "Lumen Cloud Connect to AWS", "category": "Cloud"},
    "Cloud_GCP": {"sku": "LUM-CX-GCP", "price_mrc": 300, "desc": "Lumen Cloud Connect to Google Cloud", "category": "Cloud"},
    # Security
    "DDoS_Basic": {"sku": "LUM-SEC-DDOS-B", "price_mrc": 800, "desc": "Basic DDoS Mitigation", "category": "Security"},
    "DDoS_Advanced": {"sku": "LUM-SEC-DDOS-A", "price_mrc": 1800, "desc": "Advanced DDoS Mitigation (scrubbing up to 100 Gbps)", "category": "Security"},
    "Managed_Firewall": {"sku": "LUM-SEC-FW", "price_mrc": 900, "desc": "Lumen Managed Next-Gen Firewall", "category": "Security"},
    "SASE_Secure_Access": {"sku": "LUM-SEC-SASE", "price_mrc": 650, "desc": "Secure Access Service Edge (SASE) gateway", "category": "Security"},
    "MACsec_Encryption": {"sku": "LUM-SEC-MACSEC", "price_mrc": 250, "desc": "Layer 2 MACsec line encryption", "category": "Security"},
    # Materials required for the connection
    "Optic_1G": {"sku": "LUM-OPT-1G", "price_mrc": 10, "desc": "1G SFP transceiver", "category": "Hardware"},
    "Optic_10G": {"sku": "LUM-OPT-10G", "price_mrc": 25, "desc": "10G SFP+ LR transceiver", "category": "Hardware"},
    "Optic_100G": {"sku": "LUM-OPT-100G", "price_mrc": 90, "desc": "100G QSFP28 LR4 transceiver", "category": "Hardware"},
    "Optic_400G": {"sku": "LUM-OPT-400G", "price_mrc": 250, "desc": "400G QSFP-DD transceiver", "category": "Hardware"},
    "Edge_Router_CPE": {"sku": "LUM-CPE-RTR", "price_mrc": 200, "desc": "Customer edge router (managed CPE)", "category": "Hardware"},
    "Cross_Connect": {"sku": "LUM-XCON", "price_mrc": 75, "desc": "Physical cross-connect in Lumen facility", "category": "Hardware"},
}

PORT_OPTICS = {"1G_Port": "Optic_1G", "10G_Port": "Optic_10G", "100G_Port": "Optic_100G", "400G_Port": "Optic_400G"}

# --- MOCK DATA: Lumen Sites (not live inventory) ---
LUMEN_SITES = [
    {"site_id": "LUM-SEA-01", "city": "Seattle, WA", "type": "Metro PoP", "offerings": ["1G_Port", "10G_Port", "100G_Port", "Cloud_Azure", "Cloud_AWS", "Cloud_GCP", "DDoS_Basic", "DDoS_Advanced", "Managed_Firewall", "MACsec_Encryption"]},
    {"site_id": "LUM-DEN-01", "city": "Denver, CO", "type": "Data Center", "offerings": ["10G_Port", "100G_Port", "400G_Port", "Cloud_Azure", "Cloud_AWS", "DDoS_Basic", "DDoS_Advanced", "Managed_Firewall", "SASE_Secure_Access", "MACsec_Encryption"]},
    {"site_id": "LUM-DFW-01", "city": "Dallas, TX", "type": "Data Center", "offerings": ["1G_Port", "10G_Port", "100G_Port", "400G_Port", "Cloud_Azure", "Cloud_AWS", "Cloud_GCP", "DDoS_Basic", "DDoS_Advanced", "Managed_Firewall", "SASE_Secure_Access", "MACsec_Encryption"]},
    {"site_id": "LUM-NYC-01", "city": "New York, NY", "type": "Metro PoP", "offerings": ["1G_Port", "10G_Port", "100G_Port", "Cloud_Azure", "Cloud_AWS", "DDoS_Basic", "Managed_Firewall", "SASE_Secure_Access"]},
    {"site_id": "LUM-LON-01", "city": "London, UK", "type": "Data Center", "offerings": ["10G_Port", "100G_Port", "Cloud_Azure", "Cloud_AWS", "Cloud_GCP", "DDoS_Basic", "DDoS_Advanced", "Managed_Firewall"]},
]

# --- AI FUNCTIONS ---
GEMINI_MODEL = "gemini-2.0-flash"

def parse_requirements_with_gemini(user_input, api_key):
    """Asks Google Gemini to map the request to catalog SKUs."""
    prompt = (
        "Map this customer network request to SKUs from this list: " + ", ".join(CATALOG.keys()) + ". "
        "Ignore services the customer says they do not want. "
        "Return only a JSON array of matching SKU names. Request: " + user_input
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "x-goog-api-key": api_key})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    items = json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
    if not isinstance(items, list):
        raise ValueError("Gemini did not return a JSON array")
    return [sku for sku in items if sku in CATALOG]

def parse_requirements_with_llm(user_input, api_key=""):
    """Uses Gemini when a key is provided, otherwise or on error the keyword parser."""
    if api_key:
        try:
            return parse_requirements_with_gemini(user_input, api_key), "Gemini"
        except Exception as e:
            st.warning(f"Gemini call failed ({e}). Using offline keyword parser.")
    return parse_requirements_keywords(user_input), "Keyword parser"

NEGATION_BEFORE = r"\b(without|no|not|exclude|excluding|except|don't)\b"
NEGATION_AFTER = r"\b(not needed|not required|not necessary|no need)\b"

def is_requested(text, *terms):
    """Returns True if a term appears in a clause without a negation before or after it."""
    for clause in re.split(r",|;| and | but | with | plus ", text):
        for term in terms:
            idx = clause.find(term)
            if idx == -1:
                continue
            before, after = clause[:idx], clause[idx + len(term):]
            if not re.search(NEGATION_BEFORE, before) and not re.search(NEGATION_AFTER, after):
                return True
    return False

def parse_requirements_keywords(user_input):
    """Offline keyword parser used when no LLM key is provided or the call fails."""
    time.sleep(1.5) # Simulate latency
    reqs = []
    user_input = user_input.lower()
    
    if is_requested(user_input, "400g"): reqs.append("400G_Port")
    elif is_requested(user_input, "100g"): reqs.append("100G_Port")
    elif is_requested(user_input, "10g"): reqs.append("10G_Port")
    elif is_requested(user_input, "1g"): reqs.append("1G_Port")
    else: reqs.append("10G_Port") # Default
        
    if is_requested(user_input, "gcp", "google"): reqs.append("Cloud_GCP")
    if is_requested(user_input, "azure"): reqs.append("Cloud_Azure")
    if is_requested(user_input, "aws"): reqs.append("Cloud_AWS")
    if is_requested(user_input, "advanced ddos", "ddos advanced"): reqs.append("DDoS_Advanced")
    elif is_requested(user_input, "ddos", "security"): reqs.append("DDoS_Basic")
    if is_requested(user_input, "firewall"): reqs.append("Managed_Firewall")
    if is_requested(user_input, "sase", "remote user"): reqs.append("SASE_Secure_Access")
    if is_requested(user_input, "encrypt", "macsec"): reqs.append("MACsec_Encryption")
        
    return reqs

def generate_bom_and_quote(extracted_reqs):
    """Builds BOM lines (services plus required hardware) with quantities and total MRC."""
    keys = list(extracted_reqs)
    ports = [k for k in keys if CATALOG[k]["category"] == "Port"]
    for port in ports:
        keys.append(PORT_OPTICS[port])
    if ports:
        keys += ["Edge_Router_CPE", "Cross_Connect"]
    keys = list(dict.fromkeys(keys))

    bom = []
    total_mrc = 0
    for key in keys:
        item = {"item": key, "qty": 1, **CATALOG[key]}
        bom.append(item)
        total_mrc += item["price_mrc"] * item["qty"]
    return bom, total_mrc

def bom_rows(bom):
    """Formats BOM items as display rows."""
    return [{
        "Item": item["item"],
        "SKU": item["sku"],
        "Category": item["category"],
        "Description": item["desc"],
        "Qty": item["qty"],
        "Unit MRC ($)": item["price_mrc"],
        "Line MRC ($)": item["price_mrc"] * item["qty"],
    } for item in bom]

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

# --- SIDEBAR: navigation, LLM key, delivery site ---
with st.sidebar:
    page = st.radio("Navigate", ["Quote Assistant", "Lumen Sites & Offerings", "BOM Listing"])
    st.subheader("LLM Settings")
    st.text_input(
        "Gemini API key",
        type="password",
        key="api_key",
        value=os.environ.get("GEMINI_API_KEY", ""),
        help="Free key from https://aistudio.google.com/app/apikey. Leave blank for offline keyword parsing.",
    )
    st.selectbox(
        "Delivery site",
        [s["site_id"] for s in LUMEN_SITES],
        key="site_id",
        format_func=lambda sid: next(s["city"] for s in LUMEN_SITES if s["site_id"] == sid),
    )

# Initialize session state for multi-step flow
if "step" not in st.session_state:
    st.session_state.step = "intake"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display Chat History
if page == "Quote Assistant":
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# STEP 1: Natural Language Intake
if page == "Quote Assistant" and st.session_state.step == "intake":
    user_query = st.chat_input("Describe your network requirements (e.g., 'I need a 10G connection to Azure with DDoS protection').")
    
    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
            
        with st.chat_message("assistant"):
            with st.spinner("Analyzing requirements & querying Lumen inventory..."):
                extracted_reqs, parser_used = parse_requirements_with_llm(user_query, st.session_state.get("api_key", ""))
                site_offerings = next(s["offerings"] for s in LUMEN_SITES if s["site_id"] == st.session_state.site_id)
                unavailable = [r for r in extracted_reqs if r not in site_offerings]
                extracted_reqs = [r for r in extracted_reqs if r in site_offerings]
                if unavailable:
                    st.warning(f"Not offered at {st.session_state.site_id}, removed: {', '.join(unavailable)}")
                if not extracted_reqs:
                    st.error("None of the requested services are offered at this site. Choose another site in the sidebar.")
                    st.stop()
                bom, total_price = generate_bom_and_quote(extracted_reqs)
                st.session_state.parser_used = parser_used
                
                st.session_state.bom = bom
                st.session_state.total_price = total_price
                st.session_state.step = "quote_approval"
                st.rerun()

# STEP 2: Quote Approval & BOM Review
if page == "Quote Assistant" and st.session_state.step == "quote_approval":
    with st.chat_message("assistant"):
        st.markdown("### 📋 Generated Bill of Materials & Quote")
        st.markdown("I have translated your requirements into the following Lumen architecture:")
        
        st.caption(f"Requirements parsed by: {st.session_state.get('parser_used', 'n/a')}")
        st.table(bom_rows(st.session_state.bom))
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
if page == "Quote Assistant" and st.session_state.step == "provisioning":
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

# --- PAGE: Lumen Sites & Offerings ---
if page == "Lumen Sites & Offerings":
    st.subheader("Lumen Sites & Offerings")
    st.caption("Mock site data for prototype use. Not live Lumen inventory.")
    for site in LUMEN_SITES:
        st.markdown(f"#### {site['city']} ({site['site_id']}) - {site['type']}")
        st.table([
            {"SKU": CATALOG[o]["sku"], "Offering": CATALOG[o]["desc"], "Category": CATALOG[o]["category"], "MRC ($)": CATALOG[o]["price_mrc"]}
            for o in site["offerings"]
        ])

# --- PAGE: BOM Listing ---
if page == "BOM Listing":
    st.subheader("Full Materials Catalog")
    st.table([
        {"Item": k, "SKU": v["sku"], "Category": v["category"], "Description": v["desc"], "MRC ($)": v["price_mrc"]}
        for k, v in CATALOG.items()
    ])
    st.subheader("BOM for Current Quote")
    if "bom" in st.session_state:
        st.table(bom_rows(st.session_state.bom))
        st.success(f"**Total Estimated MRC: ${st.session_state.total_price}**")
    else:
        st.info("No quote generated yet. Use the Quote Assistant to create a BOM.")