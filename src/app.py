import streamlit as st
import os
import sys
import json
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflow import TweetRewriter

st.set_page_config(page_title="Multi-Model Tweet Rewriter", page_icon="🐦", layout="wide", initial_sidebar_state="collapsed")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "config.json")

def load_config():
    # Priority 1: config.json (Local Dev)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
            
    # Priority 2: st.secrets (Streamlit Cloud Deployment)
    # Check if secrets are available and have the expected structure
    try:
        # Use simple dict conversion instead of json.dumps
        # Streamlit secrets might not be fully JSON serializable or have circular refs
        if hasattr(st, "secrets") and "step1_extraction" in st.secrets:
            # Recursive conversion helper
            def to_dict(obj):
                if isinstance(obj, (str, int, float, bool, type(None))):
                    return obj
                if hasattr(obj, "items"):
                    return {k: to_dict(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [to_dict(i) for i in obj]
                return obj
                
            return to_dict(st.secrets)
            
    except Exception as e:
        st.error(f"Secrets loading error: {e}")
        
    # Default fallback config if nothing found
    return {
        "step1_extraction": {},
        "step3_generation": {
            "primary": {},
            "secondary": {}
        },
        "step4_refinement": {
            "primary": {},
            "secondary": {}
        }
    }

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

# Initialize session state
if "config" not in st.session_state:
    st.session_state.config = load_config()

def get_rewriter():
    """Initialize rewriter with current session config"""
    return TweetRewriter(st.session_state.config)

# --- Sidebar Removed ---
# Configuration is now handled via config.json or st.secrets
# Persona management moved to main area expander

def render_persona_management():
    # Persona Management
    with st.expander("👥 Persona Management", expanded=False):
        
        # Initialize rewriter to load personas
        temp_rewriter = get_rewriter()
        personas = temp_rewriter.personas
        
        col_del, col_add = st.columns([1, 1])
        
        with col_del:
            st.subheader("Delete Persona")
            # Display existing personas
            persona_names = [f"{p['id']}. {p['name']}" for p in personas]
            selected_persona_to_del = st.selectbox("Select Persona to Delete", ["None"] + persona_names)
            
            if st.button("Delete Persona"):
                if selected_persona_to_del != "None":
                    p_id = int(selected_persona_to_del.split(".")[0])
                    temp_rewriter.delete_persona(p_id)
                    st.success(f"Deleted Persona ID: {p_id}")
                    st.rerun()

        with col_add:
            st.subheader("Add New Persona")
            new_name = st.text_input("Name", placeholder="e.g. The Fud Guy")
            new_desc = st.text_area("Description", placeholder="e.g. Always bearish...")
            new_type = st.selectbox("Type", [
                "Type A: Traders & Degens (High Risk)",
                "Type B: Airdrop Farmers & Interaction (Price Sensitive)",
                "Type C: Builders & Techies (Junior/Worker)",
                "Type D: Vibes & NFT (Culture Driven)",
                "Type E: Realists & Normies (Outsider/Edge)"
            ])
            new_gender = st.selectbox("Gender", ["Male", "Female", "Any"])
            new_age = st.text_input("Age", placeholder="20s")
            
            if st.button("Confirm Add"):
                if new_name and new_desc:
                    temp_rewriter.add_persona(new_name, new_desc, new_type, new_gender, new_age)
                    st.success("Persona Added Successfully!")
                    st.rerun()
                else:
                    st.error("Name and Description cannot be empty.")

# --- Main Area ---
st.title("Web3 Multi-Model Workflow 🚀")

# Render Persona Management at the top or bottom? 
# User wanted sidebar hidden. Let's put it at the bottom or in an expander at top.
# Let's put it at the very bottom or in a "Settings" section.

# Dynamic Pipeline Spec Display
s4_config = st.session_state.config.get("step4_refinement", {})
s4_desc = s4_config.get("primary", {}).get("model", "Unknown")
if "secondary" in s4_config:
    s4_desc += f" + {s4_config['secondary'].get('model', 'Unknown')} (Parallel/Backup)"

st.markdown(f"""
**Workflow:**
1. **Analysis & Extract**: Extract key facts from your tweets
2. **Rewriting**: Output = Original Text + Rewrite Intent + Persona Library
3. **Review**: Refine it through a quality gate to ensure it sounds human
""")

# Initialize rewriter early to get intents
rewriter = get_rewriter()

col1, col2 = st.columns([1, 1])

with col1:
    original_text = st.text_area("Original Tweet / Announcement", height=350, placeholder="Paste the official announcement here...")

with col2:
    # Load intents
    intents = rewriter.get_intents()
    intent_options = {i["label"]: i for i in intents}
    
    selected_intent_label = st.selectbox("Rewrite Intent", options=list(intent_options.keys()) + ["Custom"])
    
    selected_intent_obj = None
    intent_input_for_extraction = ""
    
    if selected_intent_label == "Custom":
        intent_custom = st.text_area("Enter Custom Intent", height=150, placeholder="e.g. 'Complain about high gas fees'...")
        intent_input_for_extraction = intent_custom
    else:
        selected_intent_obj = intent_options[selected_intent_label]
        intent_input_for_extraction = f"{selected_intent_obj['label']} - {selected_intent_obj['core_logic']}"
        
        # Display details
        st.info(f"**Style**: {selected_intent_obj['style']}\n\n**Tone**: {selected_intent_obj['tone']}")
        with st.expander("View Detailed Rules"):
             st.write(f"**Core Logic**: {selected_intent_obj['core_logic']}")
             st.write(f"**Content Requirements**: {selected_intent_obj['content_requirements']}")
             st.write(f"**Prompt Instruction**: {selected_intent_obj['prompt_instruction']}")

count = st.slider("Variations", min_value=1, max_value=10, value=1)

if st.button("🚀 Execute Pipeline", type="primary"):
    if not original_text or not intent_input_for_extraction:
        st.warning("Please enter both original text and rewrite intent.")
    else:
        # Container for results
        results_container = st.container()
        
        with st.status("Orchestrating Multi-Model Pipeline...", expanded=True) as status:
            # Step 1
            st.write("🔍 **Step 1: Understanding & Extraction** (DeepSeek-V3)")
            try:
                facts = rewriter.extract_facts(original_text, intent_input_for_extraction)
                st.markdown(f"> **Facts Extracted:**\n> {facts[:100]}...")
            except Exception as e:
                st.error(f"Step 1 Failed: {e}")
                st.stop()
                
            results = []
            
            for i in range(count):
                st.write(f"--- Processing Variation {i+1}/{count} ---")
                
                # Step 2
                st.write("🎭 **Step 2: Persona Selection**")
                # Determine intent ID for persona matching
                current_intent_id = selected_intent_obj['id'] if selected_intent_obj else None
                persona = rewriter.select_persona(intent_id=current_intent_id)
                st.info(f"Selected: **{persona['name']}** ({persona['type']})")
                
                # Step 3
                st.write("✍️ **Step 3: Role Generation** (Nous Hermes 3 -> Fallback: DeepSeek)")
                try:
                    draft = rewriter.generate_draft(persona, facts, intent_obj=selected_intent_obj)
                except Exception as e:
                    st.error(f"Generation Failed: {e}")
                    continue

                # Step 4
                st.write(f"🛡️ **Step 4: AI Detection & Refinement** ({s4_desc})")
                final_output = rewriter.quality_gate(persona, draft)
                
                if "[REWRITTEN]" in final_output:
                    final_content = final_output.replace("[REWRITTEN]", "").strip()
                    # Clean up score info if present (Matches both "(Score: XX)" and "(Scores: XX)")
                    if "(Score" in final_content:
                         # Extract content after scores
                         parts = final_content.split(")", 1)
                         if len(parts) > 1:
                             final_content = parts[1].strip()
                    
                    status_label = "Refined/Rewritten"
                    status_color = "orange"
                else:
                    final_content = final_output.replace("[PASSED]", "").strip()
                    if "(Score" in final_content:
                         parts = final_content.split(")", 1)
                         if len(parts) > 1:
                             final_content = parts[1].strip()
                             
                    status_label = "Passed Quality Gate"
                    status_color = "green"
                
                results.append({
                    "persona": persona,
                    "draft": draft,
                    "final": final_content,
                    "status_label": status_label,
                    "status_color": status_color,
                    "raw_output": final_output
                })
            
            status.update(label="Workflow Completed!", state="complete", expanded=False)

        # Display Results
        st.divider()
        st.header("✨ Final Output")
        
        for res in results:
            with st.container():
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image("https://api.dicebear.com/7.x/avataaars/svg?seed=" + res["persona"]["name"], width=80)
                    st.caption(f"**{res['persona']['name']}**")
                
                with cols[1]:
                    st.markdown(f"### Generated Tweet")
                    st.code(res["final"], language="text")
                    
                    with st.expander("Debug & Trace"):
                        st.markdown(f"**Initial Draft (Nous Hermes/DeepSeek):**")
                        st.text(res["draft"])
                        st.markdown(f"**Quality Gate Output (Claude + Grok):**")
                        st.text(res["raw_output"])
                        st.markdown(f"**Status:** :{res['status_color']}[{res['status_label']}]")
                
                st.divider()

        # Audit Logs
        with st.expander("📊 Audit Logs & Performance Metrics"):
            logs = rewriter.get_audit_logs()
            df = pd.DataFrame(logs)
            st.dataframe(df, use_container_width=True)

# Add Persona Management at the bottom
st.divider()
render_persona_management()


