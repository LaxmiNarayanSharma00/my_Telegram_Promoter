import pandas as pd
from pathlib import Path
import yaml
from datetime import datetime, timedelta
from .model_provider import ProviderRegistry
import os
BASE_DIR = Path(__file__).resolve().parent
LIMITS_FILE = BASE_DIR / "Limits.xlsx"
CONFIG_FILE = BASE_DIR / "config.yaml"



class LoadBalancer:
    def __init__(self):
        self.data = pd.read_excel(LIMITS_FILE)
        self.config = self.load_config(CONFIG_FILE)
        # Ensure Last_Reset column exists
        if "Last_Reset" not in self.data.columns:
            self.data["Last_Reset"] = datetime.now().isoformat()
            self.data.to_excel(LIMITS_FILE, index=False)

    @staticmethod   
    def load_config(config_path:Path):
        with open(CONFIG_FILE,'r') as F:
            return yaml.safe_load(F)
        
    @staticmethod
    def estimate_tokens(text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)
    
    def _reset_if_needed(self):
        """Reset daily counters if 24 hours have passed since last reset"""
        now = datetime.now()
        for idx, row in self.data.iterrows():
            try:
                last_reset = datetime.fromisoformat(row["Last_Reset"])
                if now - last_reset >= timedelta(hours=24):
                    # Reset daily counters
                    self.data.at[idx, "Current_Ct_Day"] = 0
                    self.data.at[idx, "Current_Ct_Tokens"] = 0
                    self.data.at[idx, "Current_Pct_Ct"] = 0.0
                    self.data.at[idx, "Current_Pct_Tokens"] = 0.0
                    self.data.at[idx, "Last_Reset"] = now.isoformat()
            except:
                pass  # Skip if Last_Reset is invalid; will be set on next update

    def start(self, text: str, max_output_tokens: int):
                # Try env variable first (GitHub Actions)
        env_key_name = self.config['users'][user_email][platform_name].get('env_key')

        if env_key_name:
            api_key = os.getenv(env_key_name)

        # Fallback to YAML (local development)
        if not api_key:
            api_key = self.config['users'][user_email][platform_name]['api_keys'][0]['key']


        data=self.get_next_endpoint(text, max_output_tokens)
        if data is None:
                raise Exception("No available API endpoint meets the criteria.")
        platform_name=data['Platform']
        user_email=data['User_ID']
        model=data['Model']
        api_key = self.config['users'][user_email][platform_name]['api_keys'][0]['key']

        provider_class=ProviderRegistry.get(platform_name)
        provider_instance=provider_class(api_key=api_key,model=model)
        # llm_client=provider_instance.get_model()
        # print(model,platform_name)
        return provider_instance
    
    def get_next_endpoint(self, text: str, max_output_tokens: int):
        # Check and reset counters if 24 hours have passed
        self._reset_if_needed()
        
        prompt_tokens = self.estimate_tokens(text)

        eligible_rows = []

        for idx, row in self.data.iterrows():
            total_tokens_needed = prompt_tokens + max_output_tokens
            # print(row['Category'],type_model)
            Current_Ct_Day=0
            Current_Ct_Tokens=0
            if row["Current_Ct_Tokens"] is None:
                Current_Ct_Tokens=0
            if row["Current_Ct_Day"] is None:
                Current_Ct_Day=0    
            if (
                Current_Ct_Tokens + total_tokens_needed <= row["Tokens per Day"]
                and Current_Ct_Day + 1 <= row["Requests per Day"] 

            ):
                eligible_rows.append(idx)

        if not eligible_rows:
            return None

        # 🔹 Select row with min %tokens used → then min %requests/day
        selected_idx = min(
            eligible_rows,
            key=lambda i: (
                
                self.data.at[i, "Current_Pct_Ct"],
                self.data.at[i, "Current_Pct_Tokens"]
            ),
        )

        # 🔹 Update counters
        self.data.at[selected_idx, "Current_Ct_Tokens"] += (
            prompt_tokens + max_output_tokens
        )
        self.data.at[selected_idx, "Current_Ct_Day"] += 1

        # 🔹 Recalculate percentages
        self.data.at[selected_idx, "Current_Pct_Tokens"] = (
            self.data.at[selected_idx, "Current_Ct_Tokens"]
            / self.data.at[selected_idx, "Tokens per Day"]
        )

        self.data.at[selected_idx, "Current_Pct_Ct"] = (
            self.data.at[selected_idx, "Current_Ct_Day"]
            / self.data.at[selected_idx, "Requests per Day"]
        )
        
        # 🔹 Ensure Last_Reset is set
        if pd.isna(self.data.at[selected_idx, "Last_Reset"]):
            self.data.at[selected_idx, "Last_Reset"] = datetime.now().isoformat()

        # 🔹 Persist updates
        self.data.to_excel(LIMITS_FILE, index=False)

        return self.data.loc[selected_idx]
