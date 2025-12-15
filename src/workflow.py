import json
import random
import os
import time
from typing import List, Dict, Optional, Literal, Any
import traceback

# Import prompts
from src.prompts import FACT_EXTRACTION_PROMPT, DRAFTING_PROMPT, QUALITY_GATE_JSON_PROMPT

# Provider Types
Provider = Literal["openai", "anthropic", "deepseek", "openrouter", "grok", "mock"]

class AuditLogger:
    def __init__(self):
        self.logs = []

    def log(self, step: str, model: str, status: str, latency: float, details: str = ""):
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "step": step,
            "model": model,
            "status": status,
            "latency": f"{latency:.2f}s",
            "details": details
        }
        self.logs.append(entry)
        # In a real app, this would write to a database or file
        
    def get_logs(self):
        return self.logs

class LLMClient:
    """Wrapper for different LLM providers with retry logic"""
    def __init__(self, provider: Provider, api_key: Optional[str] = None, model_name: str = "gpt-3.5-turbo", base_url: Optional[str] = None):
        self.provider = provider
        self.model_name = model_name
        self.client = None
        self.base_url = base_url
        self.api_key = api_key.strip() if api_key else None
        
        self._init_client()

    def _init_client(self):
        if self.provider == "mock":
            return

        if self.provider == "anthropic":
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                print("Anthropic not installed")
        
        elif self.provider in ["openai", "deepseek", "openrouter", "grok"]:
            try:
                from openai import OpenAI
                # Set specific base URLs if not provided
                if not self.base_url:
                    if self.provider == "deepseek":
                        self.base_url = "https://api.deepseek.com"
                    elif self.provider == "openrouter":
                        self.base_url = "https://openrouter.ai/api/v1"
                    elif self.provider == "grok":
                        self.base_url = "https://api.x.ai/v1"
                
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                print("OpenAI not installed")

    def generate(self, prompt: str, system_instruction: str = "You are a helpful assistant.", json_mode: bool = False) -> str:
        if self.provider == "mock" or not self.client:
            time.sleep(1) # Simulate latency
            if json_mode:
                 return json.dumps({
                    "score": 88,
                    "reason": "Mock pass",
                    "is_passed": True,
                    "rewritten_tweet": "Mock tweet content"
                })
            return f"[MOCK {self.provider.upper()}] Response"

        retries = 2
        for attempt in range(retries + 1):
            try:
                if self.provider == "anthropic":
                    response = self.client.messages.create(
                        model=self.model_name,
                        max_tokens=4096,
                        system=system_instruction,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    return response.content[0].text.strip()

                elif self.provider in ["openai", "deepseek", "openrouter", "grok"]:
                    messages = [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ]
                    
                    params = {
                        "model": self.model_name,
                        "messages": messages,
                        "temperature": 0.7
                    }
                    
                    if json_mode:
                        params["response_format"] = {"type": "json_object"}
                        
                    # Extra headers for OpenRouter
                    extra_headers = {}
                    if self.provider == "openrouter":
                         extra_headers = {
                            "HTTP-Referer": "https://localhost:8501", 
                            "X-Title": "TweetRewriter"
                        }

                    response = self.client.chat.completions.create(
                        **params,
                        extra_headers=extra_headers if extra_headers else None
                    )
                    
                    if not response:
                        raise ValueError("Received empty response from provider")
                        
                    if not hasattr(response, 'choices') or response.choices is None:
                         # Fallback for potential non-standard responses or errors masked as success
                         raise ValueError(f"Response missing choices: {response}")

                    if not response.choices:
                         raise ValueError(f"Response choices empty: {response}")

                    content = response.choices[0].message.content
                    return content.strip() if content else ""

            except Exception as e:
                if attempt == retries:
                    raise e
                time.sleep(1)

class TweetRewriter:
    def __init__(self, config: Dict):
        """
        Initialize with full config dictionary
        """
        self.config = config
        self.personas_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "personas.json")
        self.personas = self._load_personas()
        self.intents_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intents.json")
        self.intents = self._load_intents()
        self.audit_logger = AuditLogger()

    def _load_personas(self) -> List[Dict]:
        if os.path.exists(self.personas_path):
            with open(self.personas_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _load_intents(self) -> List[Dict]:
        if os.path.exists(self.intents_path):
            with open(self.intents_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
        
    def get_intents(self) -> List[Dict]:
        return self.intents

    def save_personas(self):
        with open(self.personas_path, "w", encoding="utf-8") as f:
            json.dump(self.personas, f, indent=2, ensure_ascii=False)

    def add_persona(self, name: str, description: str, type_cat: str, gender: str, age: str):
        new_id = max([p["id"] for p in self.personas]) + 1 if self.personas else 1
        new_persona = {
            "id": new_id,
            "name": name,
            "description": description,
            "type": type_cat,
            "gender": gender,
            "age": age
        }
        self.personas.append(new_persona)
        self.save_personas()
        return new_persona

    def delete_persona(self, persona_id: int):
        self.personas = [p for p in self.personas if p["id"] != persona_id]
        self.save_personas()

    INTENT_PERSONA_MAP = {
        "koc": ["Type B", "Type E"],
        "trader": ["Type A", "Type C"],
        "media": ["Type E", "Type C"],
        "social": ["Type D", "Type E"],
        "degen": ["Type A", "Type D"],
        "skeptic": ["Type C", "Type A"],
        "farmer": ["Type B"]
    }

    def select_persona(self, persona_id: Optional[int] = None, intent_id: Optional[str] = None) -> Dict:
        if persona_id:
            for p in self.personas:
                if p["id"] == persona_id:
                    return p
            return random.choice(self.personas)
            
        if intent_id and intent_id in self.INTENT_PERSONA_MAP:
            target_types = self.INTENT_PERSONA_MAP[intent_id]
            # Flexible matching: if persona["type"] starts with the target type string
            candidates = [p for p in self.personas if any(p["type"].startswith(t) for t in target_types)]
            if candidates:
                return random.choice(candidates)
                
        return random.choice(self.personas)

    def _create_client(self, config_section: Dict) -> LLMClient:
        return LLMClient(
            provider=config_section.get("provider", "mock"),
            api_key=config_section.get("api_key"),
            model_name=config_section.get("model", "gpt-3.5-turbo"),
            base_url=config_section.get("base_url")
        )

    # --- Step 1: Extraction ---
    def extract_facts(self, original_text: str, intent: str) -> str:
        step_config = self.config.get("step1_extraction", {})
        client = self._create_client(step_config)
        
        prompt = FACT_EXTRACTION_PROMPT.format(original_text=original_text, intent=intent)
        
        start_time = time.time()
        try:
            result = client.generate(prompt, system_instruction="You are an expert crypto analyst.")
            latency = time.time() - start_time
            self.audit_logger.log("Step 1", step_config.get("model"), "Success", latency)
            return result
        except Exception as e:
            latency = time.time() - start_time
            self.audit_logger.log("Step 1", step_config.get("model"), f"Error: {str(e)}", latency)
            raise e

    # --- Step 3: Generation (with Fallback) ---
    def generate_draft(self, persona: Dict, facts_and_intent: str, intent_obj: Optional[Dict] = None) -> str:
        step_config = self.config.get("step3_generation", {})
        
        # Try Primary
        primary_config = step_config.get("primary", {})
        primary_client = self._create_client(primary_config)
        
        # Construct intent rules string
        intent_rules = ""
        if intent_obj:
            intent_rules = f"""
**Core Logic**: {intent_obj.get('core_logic', '')}
**Style**: {intent_obj.get('style', '')}
**Content Requirements**: {intent_obj.get('content_requirements', '')}
**Tone**: {intent_obj.get('tone', '')}
**Key Instruction**: {intent_obj.get('prompt_instruction', '')}
"""
        
        prompt = DRAFTING_PROMPT.format(
            persona_name=persona["name"],
            persona_description=persona["description"],
            persona_type=persona["type"],
            intent_rules=intent_rules,
            facts_and_intent=facts_and_intent
        )
        
        start_time = time.time()
        try:
            result = primary_client.generate(prompt, system_instruction=f"You are playing the role of {persona['name']}.")
            latency = time.time() - start_time
            self.audit_logger.log("Step 3 (Primary)", primary_config.get("model"), "Success", latency)
            return result
        except Exception as e:
            latency = time.time() - start_time
            self.audit_logger.log("Step 3 (Primary)", primary_config.get("model"), f"Failed: {str(e)}", latency, "Switching to Secondary")
            
            # Fallback to Secondary
            secondary_config = step_config.get("secondary", {})
            secondary_client = self._create_client(secondary_config)
            
            start_time_sec = time.time()
            try:
                result = secondary_client.generate(prompt, system_instruction=f"You are playing the role of {persona['name']}.")
                latency_sec = time.time() - start_time_sec
                self.audit_logger.log("Step 3 (Secondary)", secondary_config.get("model"), "Success", latency_sec)
                return result
            except Exception as e2:
                latency_sec = time.time() - start_time_sec
                self.audit_logger.log("Step 3 (Secondary)", secondary_config.get("model"), f"Failed: {str(e2)}", latency_sec)
                raise e2

    # --- Step 4: Quality Gate (Primary with Fallback) ---
    def quality_gate(self, persona: Dict, draft_tweet: str) -> str:
        step_config = self.config.get("step4_refinement", {})
        threshold = step_config.get("threshold_score", 85)
        
        primary_config = step_config.get("primary", {})
        secondary_config = step_config.get("secondary")
        
        prompt = QUALITY_GATE_JSON_PROMPT.format(
            persona_name=persona["name"],
            persona_description=persona["description"],
            draft_tweet=draft_tweet
        )
        
        def process_result(result_json: str, role_name: str, latency: float):
            try:
                # Clean up markdown code blocks if present
                clean_json = result_json.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)
                
                score = data.get("score", 0)
                self.audit_logger.log("Step 4", role_name, "Success", latency, f"Score: {score}")
                
                if score >= threshold:
                    return f"[PASSED] (Score: {score}) {draft_tweet}"
                else:
                    rewritten = data.get("rewritten_tweet", draft_tweet)
                    return f"[REWRITTEN] (Score: {score}) {rewritten}"
            except json.JSONDecodeError as e:
                self.audit_logger.log("Step 4", role_name, "JSON Parse Error", latency, str(e))
                raise e # Re-raise to trigger fallback if applicable

        # 1. Try Primary
        client_primary = self._create_client(primary_config)
        start_t = time.time()
        try:
            res_primary = client_primary.generate(prompt, system_instruction="You are a QA bot.", json_mode=True)
            lat_primary = time.time() - start_t
            return process_result(res_primary, f"Primary ({primary_config.get('model')})", lat_primary)
            
        except Exception as e:
            lat_primary = time.time() - start_t
            self.audit_logger.log("Step 4", f"Primary ({primary_config.get('model')})", f"Failed: {str(e)}", lat_primary, "Switching to Secondary")
            
            # 2. Try Secondary (if configured)
            if secondary_config and secondary_config.get("provider"):
                client_secondary = self._create_client(secondary_config)
                start_t_sec = time.time()
                try:
                    res_secondary = client_secondary.generate(prompt, system_instruction="You are a QA bot.", json_mode=True)
                    lat_sec = time.time() - start_t_sec
                    return process_result(res_secondary, f"Secondary ({secondary_config.get('model')})", lat_sec)
                except Exception as e2:
                    lat_sec = time.time() - start_t_sec
                    self.audit_logger.log("Step 4", f"Secondary ({secondary_config.get('model')})", f"Failed: {str(e2)}", lat_sec)
                    return f"[ERROR] Both Quality Gate models failed. {draft_tweet}"
            else:
                return f"[ERROR] Primary Quality Gate failed and no Secondary configured. {draft_tweet}"

    def get_audit_logs(self):
        return self.audit_logger.get_logs()
