import streamlit as st
import os
import sys
import json
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflow import TweetRewriter

st.set_page_config(page_title="Multi-Model Tweet Rewriter", page_icon="🐦", layout="wide")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "config.json")

def load_config():
    # Priority 1: config.json (Local Dev)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
            
    # Priority 2: st.secrets (Streamlit Cloud Deployment)
    # Check if secrets are available and have the expected structure
    try:
        if hasattr(st, "secrets") and "step1_extraction" in st.secrets:
            # Deep copy secrets to a regular dict since st.secrets is read-only
            # We use json round-trip for a clean dict
            return json.loads(json.dumps(st.secrets))
    except Exception as e:
        print(f"Error loading secrets: {e}")
        
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

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ 管道配置 (Pipeline Config)")
    
    def render_model_config(conf, label_prefix):
        with st.container():
            provider = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "deepseek", "grok"], 
                                  key=f"{label_prefix}_provider",
                                  index=["openrouter", "openai", "anthropic", "deepseek", "grok"].index(conf.get("provider", "openrouter")) if conf.get("provider") in ["openrouter", "openai", "anthropic", "deepseek", "grok"] else 0)
            conf["provider"] = provider
            
            model = st.text_input("Model", value=conf.get("model", ""), key=f"{label_prefix}_model")
            conf["model"] = model
            
            api_key = st.text_input("API Key", value=conf.get("api_key", ""), type="password", key=f"{label_prefix}_key")
            conf["api_key"] = api_key
            
            # Auto-set base_url for convenience
            if provider == "openrouter":
                conf["base_url"] = "https://openrouter.ai/api/v1"
            elif provider == "deepseek":
                conf["base_url"] = "https://api.deepseek.com"
            elif provider == "grok":
                conf["base_url"] = "https://api.x.ai/v1"

    with st.expander("1. 理解与提取 (Step 1)", expanded=False):
        render_model_config(st.session_state.config.get("step1_extraction", {}), "s1")

    with st.expander("2. 角色生成 (Step 3)", expanded=False):
        st.caption("Primary Model")
        render_model_config(st.session_state.config["step3_generation"].get("primary", {}), "s3_p")
        st.divider()
        st.caption("Secondary Model")
        render_model_config(st.session_state.config["step3_generation"].get("secondary", {}), "s3_s")

    with st.expander("3. 质检与润色 (Step 4)", expanded=False):
        st.caption("Primary Model")
        render_model_config(st.session_state.config["step4_refinement"].get("primary", {}), "s4_p")
        
        if "secondary" in st.session_state.config["step4_refinement"]:
            st.divider()
            st.caption("Secondary Model")
            render_model_config(st.session_state.config["step4_refinement"]["secondary"], "s4_s")
        
    if st.button("💾 保存配置 (Save Config)"):
        save_config(st.session_state.config)
        st.success("配置已保存 (Config Saved)")

    st.divider()

    # Persona Management
    st.subheader("👥 人设管理 (Persona Management)")
    
    # Initialize rewriter to load personas
    temp_rewriter = get_rewriter()
    personas = temp_rewriter.personas
    
    # Display existing personas
    persona_names = [f"{p['id']}. {p['name']}" for p in personas]
    selected_persona_to_del = st.selectbox("选择要删除的人设", ["None"] + persona_names)
    
    if st.button("删除人设 (Delete)"):
        if selected_persona_to_del != "None":
            p_id = int(selected_persona_to_del.split(".")[0])
            temp_rewriter.delete_persona(p_id)
            st.success(f"已删除人设 ID: {p_id}")
            st.rerun()

    with st.expander("➕ 添加新人设 (Add New)"):
        new_name = st.text_input("名称 (Name)", placeholder="e.g. The Fud Guy")
        new_desc = st.text_area("描述 (Description)", placeholder="e.g. Always bearish...")
        new_type = st.selectbox("类型 (Type)", [
            "Type A: Traders & Degens (High Risk)",
            "Type B: Airdrop Farmers & Interaction (Price Sensitive)",
            "Type C: Builders & Techies (Junior/Worker)",
            "Type D: Vibes & NFT (Culture Driven)",
            "Type E: Realists & Normies (Outsider/Edge)"
        ])
        new_gender = st.selectbox("性别 (Gender)", ["Male", "Female", "Any"])
        new_age = st.text_input("年龄 (Age)", placeholder="20s")
        
        if st.button("确认添加"):
            if new_name and new_desc:
                temp_rewriter.add_persona(new_name, new_desc, new_type, new_gender, new_age)
                st.success("人设添加成功！")
                st.rerun()
            else:
                st.error("名称和描述不能为空。")

# --- Main Area ---
st.title("Web3 Multi-Model Workflow 🚀")

# Dynamic Pipeline Spec Display
s4_config = st.session_state.config.get("step4_refinement", {})
s4_desc = s4_config.get("primary", {}).get("model", "Unknown")
if "secondary" in s4_config:
    s4_desc += f" + {s4_config['secondary'].get('model', 'Unknown')} (Parallel/Backup)"

st.markdown(f"""
**工作流LLM大模型:**
1. **原文分析**: DeepSeek-V3
2. **内容改写**: Nous Hermes 3 (Fallback: DeepSeek V3)
3. **AI检测**: {s4_desc}
""")

# Initialize rewriter early to get intents
rewriter = get_rewriter()

col1, col2 = st.columns([1, 1])

with col1:
    original_text = st.text_area("原始推文 / 公告 (Original Text)", height=350, placeholder="Paste the official announcement here...")

with col2:
    # Load intents
    intents = rewriter.get_intents()
    intent_options = {i["label"]: i for i in intents}
    
    selected_intent_label = st.selectbox("改写方向与意图 (Rewrite Intent)", options=list(intent_options.keys()) + ["自定义 (Custom)"])
    
    selected_intent_obj = None
    intent_input_for_extraction = ""
    
    if selected_intent_label == "自定义 (Custom)":
        intent_custom = st.text_area("请输入具体意图 (Enter Custom Intent)", height=150, placeholder="例如：'抱怨Gas费太贵'...")
        intent_input_for_extraction = intent_custom
    else:
        selected_intent_obj = intent_options[selected_intent_label]
        intent_input_for_extraction = f"{selected_intent_obj['label']} - {selected_intent_obj['core_logic']}"
        
        # Display details
        st.info(f"**风格 (Style)**: {selected_intent_obj['style']}\n\n**语气 (Tone)**: {selected_intent_obj['tone']}")
        with st.expander("查看详细规则 (View Rules)"):
             st.write(f"**核心逻辑 (Core Logic)**: {selected_intent_obj['core_logic']}")
             st.write(f"**内容要求 (Content)**: {selected_intent_obj['content_requirements']}")
             st.write(f"**Prompt指令**: {selected_intent_obj['prompt_instruction']}")

count = st.slider("生成数量 (Variations)", min_value=1, max_value=10, value=1)

if st.button("🚀 执行多模型工作流 (Execute Pipeline)", type="primary"):
    if not original_text or not intent_input_for_extraction:
        st.warning("请同时输入原文和改写意图。")
    else:
        # Container for results
        results_container = st.container()
        
        with st.status("正在编排多模型管线 (Orchestrating Multi-Model Pipeline)...", expanded=True) as status:
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
                    # Clean up score info if present
                    if "(Scores:" in final_content:
                         # Extract content after scores
                         parts = final_content.split(")", 1)
                         if len(parts) > 1:
                             final_content = parts[1].strip()
                    
                    status_label = "Refined/Rewritten"
                    status_color = "orange"
                else:
                    final_content = final_output.replace("[PASSED]", "").strip()
                    if "(Scores:" in final_content:
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
