import streamlit as st
import time
import json
import random
import os
import urllib.request
import re
from budget_optimizer import calculate_mrc, get_budget_tradeoffs

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
    "IAD_Analog_Gateway": {"sku": "LUM-CPE-IAD", "price_mrc": 60, "desc": "Integrated access device / analog gateway (FXS/FXO)", "category": "Hardware", "products": ["VoIP", "SIP"]},
    "SBC_Managed": {"sku": "LUM-CPE-SBC", "price_mrc": 350, "desc": "Managed session border controller (SIP trunk demarc)", "category": "Hardware", "products": ["SIP"]},
    "IP_Phone": {"sku": "LUM-CPE-PHONE", "price_mrc": 12, "desc": "IP desk phone (per seat)", "category": "Hardware", "products": ["VoIP"]},
    "PRI_Gateway": {"sku": "LUM-CPE-PRI", "price_mrc": 120, "desc": "T1/PRI to SIP media gateway", "category": "Hardware", "products": ["VoIP", "SIP"]},
    "Demarc_NID": {"sku": "LUM-NID", "price_mrc": 45, "desc": "Network interface device / Ethernet demarc", "category": "Hardware", "products": ["DIA", "Ethernet", "VoIP", "SIP"]},
    "Fiber_Patch_Cable": {"sku": "LUM-CBL-FBR", "price_mrc": 0, "desc": "Fiber jumper / patch cable (one-time)", "category": "Hardware", "products": ["DIA", "Ethernet", "FrameATM"]},
    "Copper_Cable_CAT6": {"sku": "LUM-CBL-CU", "price_mrc": 0, "desc": "CAT6 cable (one-time)", "category": "Hardware", "products": ["DIA", "VoIP", "SIP"]},
    "NNI_Port": {"sku": "LUM-NNI", "price_mrc": 400, "desc": "Carrier NNI port (ASR / Ethernet access)", "category": "Access", "products": ["ASR", "Ethernet"]},
    "Last_Mile_Local_Loop": {"sku": "LUM-LOOP", "price_mrc": 250, "desc": "Local access / last-mile loop", "category": "Access", "products": ["DIA", "Ethernet", "VoIP", "SIP", "FrameATM"]},
    "Cross_Connect": {"sku": "LUM-XCON", "price_mrc": 75, "desc": "Physical cross-connect in Lumen facility", "category": "Hardware", "products": ["DIA", "Ethernet", "8xx"]},
    "CSU_DSU": {"sku": "LUM-CPE-CSU", "price_mrc": 30, "desc": "CSU/DSU for T1/DS3 and Frame/ATM", "category": "Hardware", "products": ["FrameATM", "PRI"]},
    "Frame_ATM_Router": {"sku": "LUM-CPE-FRATM", "price_mrc": 180, "desc": "Frame Relay / ATM access router", "category": "Hardware", "products": ["FrameATM"]},
    "Edge_Router_CPE": {"sku": "LUM-CPE-RTR", "price_mrc": 200, "desc": "Customer edge router (managed CPE)", "category": "Hardware", "products": ["DIA", "Ethernet", "Networx"]},
    "TN_Block": {"sku": "LUM-RES-TN", "price_mrc": 1, "desc": "Telephone number (per TN) / DID block", "category": "Resource", "products": ["VoIP", "SIP"]},
    "Toll_Free_Number": {"sku": "LUM-RES-8XX", "price_mrc": 2, "desc": "8xx toll-free number reservation", "category": "Resource", "products": ["8xx"]},
    "Trunk_Group": {"sku": "LUM-RES-TG", "price_mrc": 100, "desc": "Trunk group / channel capacity", "category": "Resource", "products": ["8xx", "SIP"]},
    "E911_Location": {"sku": "LUM-RES-E911", "price_mrc": 3, "desc": "E911 address registration (per location)", "category": "Resource", "products": ["VoIP", "SIP"]},
    "Static_IP_Block": {"sku": "LUM-RES-IP", "price_mrc": 20, "desc": "Static IPv4 block (/29)", "category": "Resource", "products": ["DIA"]},
    "Install_Labor": {"sku": "LUM-SVC-INST", "price_mrc": 0, "desc": "Technician install / turn-up (NRC)", "category": "Service", "products": ["All"]},
    "CPE_Config_Staging": {"sku": "LUM-SVC-STAGE", "price_mrc": 0, "desc": "CPE staging and configuration in CPE lab (NRC)", "category": "Service", "products": ["VoIP", "SIP"]},
    "Number_Port_Fee": {"sku": "LUM-SVC-PORT", "price_mrc": 0, "desc": "Number porting / PON processing (NRC)", "category": "Service", "products": ["VoIP", "SIP"]},
    "BTL_Billing_Telephone_Line": {"sku": "LUM-RES-BTL", "price_mrc": 0, "desc": "BTL / billing association for Networx circuits", "category": "Resource", "products": ["Networx"]},
    "VLAN_SEID": {"sku": "LUM-RES-VLAN", "price_mrc": 0, "desc": "VLAN / SEID assignment", "category": "Resource", "products": ["Ethernet", "Networx"]},
    "CFA_Assignment": {"sku": "LUM-RES-CFA", "price_mrc": 0, "desc": "Connecting facility assignment", "category": "Resource", "products": ["ASR", "Ethernet"]},
    "Disconnect_Labor": {"sku": "LUM-SVC-DISC", "price_mrc": 0, "desc": "Disconnect / equipment recovery (NRC)", "category": "Service", "products": ["Auto-Disconnect"]},
}

PORT_OPTICS = {"1G_Port": "Optic_1G", "10G_Port": "Optic_10G", "100G_Port": "Optic_100G", "400G_Port": "Optic_400G"}

PRODUCT_MATERIALS = {
    "VoIP": {"required": ["Last_Mile_Local_Loop", "Demarc_NID", "IAD_Analog_Gateway", "TN_Block", "E911_Location", "Install_Labor", "CPE_Config_Staging"], "optional": ["IP_Phone", "PRI_Gateway", "Number_Port_Fee", "Copper_Cable_CAT6"]},
    "SIP_Trunk": {"required": ["Last_Mile_Local_Loop", "Demarc_NID", "SBC_Managed", "Trunk_Group", "TN_Block", "E911_Location", "Install_Labor", "CPE_Config_Staging"], "optional": ["PRI_Gateway", "Number_Port_Fee", "Edge_Router_CPE"]},
    "8xx_Toll_Free": {"required": ["Toll_Free_Number", "Trunk_Group"], "optional": ["Cross_Connect", "Install_Labor"]},
    "DIA": {"required": ["Last_Mile_Local_Loop", "Demarc_NID", "Edge_Router_CPE", "Static_IP_Block", "Fiber_Patch_Cable", "Install_Labor"], "optional": ["Cross_Connect", "Optic_1G", "Optic_10G", "Optic_100G"]},
    "Ethernet_ASR": {"required": ["NNI_Port", "CFA_Assignment", "VLAN_SEID", "Last_Mile_Local_Loop", "Demarc_NID", "Fiber_Patch_Cable", "Install_Labor"], "optional": ["Cross_Connect", "Optic_1G", "Optic_10G", "Optic_100G", "Optic_400G", "Edge_Router_CPE"]},
    "Frame_ATM": {"required": ["Last_Mile_Local_Loop", "CSU_DSU", "Frame_ATM_Router", "Install_Labor"], "optional": ["Cross_Connect"]},
    "Networx_NVPN": {"required": ["BTL_Billing_Telephone_Line", "VLAN_SEID", "Last_Mile_Local_Loop", "Demarc_NID", "Edge_Router_CPE", "Install_Labor"], "optional": ["Static_IP_Block", "IAD_Analog_Gateway", "Fiber_Patch_Cable"]},
    "Auto_Disconnect": {"required": ["Disconnect_Labor"], "optional": []},
}

PRODUCT_ALIASES = {
    "VoIP": ("voip", "voice over ip"),
    "SIP_Trunk": ("sip trunk", "sip trunks"),
    "8xx_Toll_Free": ("8xx", "toll free", "toll-free"),
    "DIA": ("dia", "dedicated internet", "internet access"),
    "Ethernet_ASR": ("ethernet asr", "asr", "ethernet access"),
    "Frame_ATM": ("frame relay", "frame atm", "atm service"),
    "Networx_NVPN": ("networx", "nvpn"),
    "Auto_Disconnect": ("auto-disconnect", "auto disconnect", "disconnect service", "disconnect"),
}

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
    """Asks Google Gemini to map the request to catalog items and product bundles."""
    valid_items = list(CATALOG) + list(PRODUCT_MATERIALS)
    prompt = (
        "Map this customer request to product bundle names and requested catalog items from this list: " + ", ".join(valid_items) + ". "
        "Product bundles: " + ", ".join(PRODUCT_MATERIALS) + ". Include the bundle when requested, and include optional materials only when explicitly requested. "
        "For DIA or Ethernet_ASR speed requests, choose the matching Optic item, not an Ethernet port. "
        "Ignore services the customer says they do not want. Return only a JSON array of exact names from the list. Request: " + user_input
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
    return [item for item in items if item in valid_items]

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

    for product, aliases in PRODUCT_ALIASES.items():
        if is_requested(user_input, *aliases):
            reqs.append(product)

    has_bundle = bool(reqs)
    has_optical_bundle = any(product in reqs for product in ("DIA", "Ethernet_ASR"))
    if is_requested(user_input, "400g"):
        if has_optical_bundle:
            reqs.append("Optic_400G")
        elif not has_bundle:
            reqs.append("400G_Port")
    elif is_requested(user_input, "100g"):
        if has_optical_bundle:
            reqs.append("Optic_100G")
        elif not has_bundle:
            reqs.append("100G_Port")
    elif is_requested(user_input, "10g"):
        if has_optical_bundle:
            reqs.append("Optic_10G")
        elif not has_bundle:
            reqs.append("10G_Port")
    elif is_requested(user_input, "1g"):
        if has_optical_bundle:
            reqs.append("Optic_1G")
        elif not has_bundle:
            reqs.append("1G_Port")
    elif not has_bundle:
        reqs.append("10G_Port") # Default

    optional_aliases = {
        "IP_Phone": ("ip phone", "desk phone"),
        "PRI_Gateway": ("pri gateway", "pri"),
        "Number_Port_Fee": ("number port", "port my number", "number porting"),
        "Copper_Cable_CAT6": ("cat6", "copper cable"),
        "Cross_Connect": ("cross-connect", "cross connect"),
        "Edge_Router_CPE": ("edge router", "managed router"),
        "Static_IP_Block": ("static ip", "/29"),
        "Fiber_Patch_Cable": ("fiber patch", "fiber jumper"),
        "Optic_1G": ("1g optic", "1g transceiver"),
        "Optic_10G": ("10g optic", "10g transceiver"),
        "Optic_100G": ("100g optic", "100g transceiver"),
        "Optic_400G": ("400g optic", "400g transceiver"),
    }
    for item, aliases in optional_aliases.items():
        if item not in reqs and is_requested(user_input, *aliases):
            reqs.append(item)
        
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
    """Expands requested products into Lumen BOM lines and calculates monthly cost."""
    requested = set(extracted_reqs)
    product_keys = [key for key in extracted_reqs if key in PRODUCT_MATERIALS]
    keys = [key for key in extracted_reqs if key in CATALOG]
    bundle_optionals = {
        key for product in product_keys for key in PRODUCT_MATERIALS[product]["optional"]
    }
    all_bundle_optionals = {
        key for spec in PRODUCT_MATERIALS.values() for key in spec["optional"]
    }
    if product_keys:
        keys = [key for key in keys if key not in all_bundle_optionals or key in bundle_optionals]

    for product in product_keys:
        spec = PRODUCT_MATERIALS[product]
        keys.extend(spec["required"])
        keys.extend(key for key in spec["optional"] if key in requested)

    if any(product in product_keys for product in ("DIA", "Ethernet_ASR")):
        port_keys = [key for key in keys if key in PORT_OPTICS]
        keys = [key for key in keys if key not in PORT_OPTICS]
        keys.extend(PORT_OPTICS[key] for key in port_keys)

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

def catalog_rows():
    """Lists catalog materials and product bundles with their required-material MRC."""
    rows = [{
        "Item": key,
        "SKU": item["sku"],
        "Category": item["category"],
        "Description": item["desc"],
        "MRC ($)": item["price_mrc"],
    } for key, item in CATALOG.items()]
    for product, spec in PRODUCT_MATERIALS.items():
        base_mrc = sum(CATALOG[key]["price_mrc"] for key in spec["required"])
        rows.append({
            "Item": product,
            "SKU": "Derived from BOM",
            "Category": "Product",
            "Description": "Required: " + ", ".join(spec["required"]),
            "MRC ($)": base_mrc,
        })
    return rows

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
budget_limit = None
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
    budget_enabled = st.toggle("Enable budget optimization", key="budget_optimization_enabled")
    if budget_enabled:
        budget_limit = st.number_input("Maximum MRC ($)", min_value=1, value=300, step=25, key="budget_limit")

# Initialize session state for multi-step flow
if "step" not in st.session_state:
    st.session_state.step = "intake"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if st.session_state.step == "budget_review" and not budget_enabled:
    st.session_state.step = "quote_approval"
if (
    budget_enabled
    and st.session_state.step in {"quote_approval", "provisioning"}
    and st.session_state.get("total_price", 0) > budget_limit
):
    st.session_state.step = "budget_review"

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
                location_scoped = [
                    r for r in extracted_reqs
                    if r in CATALOG and CATALOG[r]["category"] in {"Port", "Cloud", "Security"}
                ]
                unavailable = [r for r in location_scoped if r not in site_offerings]
                extracted_reqs = [r for r in extracted_reqs if r not in unavailable]
                if unavailable:
                    st.warning(f"Not offered at {st.session_state.site_id}, removed: {', '.join(unavailable)}")
                if not extracted_reqs:
                    st.error("None of the requested services are offered at this site. Choose another site in the sidebar.")
                    st.stop()
                bom, total_price = generate_bom_and_quote(extracted_reqs)
                st.session_state.parser_used = parser_used
                st.session_state.requested_items = extracted_reqs
                st.session_state.product_keys = [item for item in extracted_reqs if item in PRODUCT_MATERIALS]
                st.session_state.budget_changes = []
                st.session_state.bom = bom
                st.session_state.total_price = total_price
                st.session_state.step = (
                    "budget_review"
                    if budget_enabled and total_price > budget_limit
                    else "quote_approval"
                )
                st.rerun()

# STEP 2: Interactive Budget Review
if page == "Quote Assistant" and st.session_state.step == "budget_review":
    if st.session_state.total_price <= budget_limit:
        st.session_state.step = "quote_approval"
        st.rerun()

    with st.chat_message("assistant"):
        st.markdown("### Budget Review")
        st.warning(
            f"This quote is ${st.session_state.total_price - budget_limit} over your "
            f"${budget_limit} monthly limit. Current estimated MRC: ${st.session_state.total_price}."
        )
        if st.session_state.get("budget_changes"):
            st.caption("Applied adjustments: " + "; ".join(st.session_state.budget_changes))

        tradeoffs = get_budget_tradeoffs(
            st.session_state.bom,
            st.session_state.get("product_keys", []),
            CATALOG,
            PRODUCT_MATERIALS,
        )
        if tradeoffs:
            st.markdown("What can we adjust to bring the quote within budget?")
            for option in tradeoffs:
                meets_budget = option["mrc"] <= budget_limit
                with st.container(border=True):
                    st.markdown(f"**{option['question']}**")
                    st.write(
                        f"{option['label']} · saves ${option['savings']}/month · "
                        f"new MRC ${option['mrc']}"
                        + (" · within budget" if meets_budget else "")
                    )
                    if st.button("Apply adjustment", key=f"budget_{option['id']}"):
                        st.session_state.bom = option["bom"]
                        st.session_state.total_price = calculate_mrc(option["bom"])
                        st.session_state.budget_changes.append(option["label"])
                        st.rerun()
        else:
            st.info(
                "The current catalog has no supported component changes that can lower this quote. "
                "Increase the maximum MRC in the sidebar or revise the request."
            )

        if st.button("Revise requirements"):
            st.session_state.step = "intake"
            st.rerun()

# STEP 3: Quote Approval & BOM Review
if page == "Quote Assistant" and st.session_state.step == "quote_approval":
    with st.chat_message("assistant"):
        st.markdown("### 📋 Generated Bill of Materials & Quote")
        st.markdown("I have translated your requirements into the following Lumen architecture:")
        
        st.caption(f"Requirements parsed by: {st.session_state.get('parser_used', 'n/a')}")
        if budget_enabled:
            st.caption(f"Within the enabled ${budget_limit} MRC budget.")
        if st.session_state.get("budget_changes"):
            st.caption("Budget adjustments: " + "; ".join(st.session_state.budget_changes))
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

# STEP 4: Automated Provisioning
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
    st.subheader("Lumen Product & Materials Catalog")
    st.table(catalog_rows())
    st.subheader("BOM for Current Quote")
    if "bom" in st.session_state:
        st.table(bom_rows(st.session_state.bom))
        st.success(f"**Total Estimated MRC: ${st.session_state.total_price}**")
    else:
        st.info("No quote generated yet. Use the Quote Assistant to create a BOM.")