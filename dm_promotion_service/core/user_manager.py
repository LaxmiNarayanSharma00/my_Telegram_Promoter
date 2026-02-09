import logging
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List


class UserManager:
    """Handle Excel-based user tracking and management"""
    
    def __init__(self, excel_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        
        if excel_path is None:
            excel_path = Path(__file__).parent.parent / "data" / "users_engagement.xlsx"
        
        self.excel_path = excel_path
        self._ensure_excel_exists()
        self.df = self._load_excel()
    
    def _ensure_excel_exists(self):
        """Create Excel if it doesn't exist"""
        if not self.excel_path.exists():
            self.excel_path.parent.mkdir(parents=True, exist_ok=True)
            
            df = pd.DataFrame(columns=[
                'user_id',
                'username',
                'level',
                'last_message_date',
                'last_response',
                'response_status',
                'subscription_checked',
                'decision',
                'notes'
            ])
            df.to_excel(self.excel_path, index=False)
            self.logger.info(f"Created new Excel file: {self.excel_path}")
    
    def _load_excel(self) -> pd.DataFrame:
        """Load Excel into DataFrame"""
        try:
            df = pd.read_excel(self.excel_path)
            df = df.astype({
                'user_id': 'Int64',   # nullable integer
                'level': 'Int64',
                'username': 'string',
                'last_message_date': 'string',
                'last_response': 'string',
                'response_status': 'string',
                'subscription_checked': 'boolean',
                'decision': 'string',
                'notes': 'string'
            })

            return df
        except Exception as e:
            self.logger.error(f"Failed to load Excel: {e}")
            return pd.DataFrame()
    
    def _save_excel(self):
        """Save DataFrame to Excel"""
        try:
            self.df.to_excel(self.excel_path, index=False)
        except Exception as e:
            self.logger.error(f"Failed to save Excel: {e}")
    
    def add_user(self, user_id: int, username: str) -> bool:
        """Add new user with level -1 (not contacted)"""
        if self._user_exists(user_id):
            return False
        
        new_row = {
            'user_id': user_id,
            'username': username,
            'level': -1,
            'last_message_date': None,
            'last_response': None,
            'response_status': None,
            'subscription_checked': False,
            'decision': None,
            'notes': 'Added during extraction'
        }
        
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
        self._save_excel()
        self.logger.info(f"Added user {username} ({user_id})")
        return True
    
    def _user_exists(self, user_id: int) -> bool:
        """Check if user already exists"""
        return (self.df['user_id'] == user_id).any()
    
    def get_users_by_level(self, level: int) -> List[Dict]:
        """Get all users at specific level"""
        users = self.df[self.df['level'] == level].to_dict('records')
        return users
    
    def update_user_level(self, user_id: int, new_level: int, message_date: Optional[datetime] = None):
        """Update user level and message date"""
        mask = self.df['user_id'] == user_id
        
        if message_date is None:
            message_date = datetime.now(timezone.utc)
        
        self.df.loc[mask, 'level'] = new_level
        self.df.loc[mask, 'last_message_date'] = message_date.isoformat()
        self._save_excel()
    
    def update_user_response(self, user_id: int, response_text: str, status: str):
        """Update user response and status (yes/no/unclear)"""
        mask = self.df['user_id'] == user_id
        self.df.loc[mask, 'last_response'] = response_text
        self.df.loc[mask, 'response_status'] = status
        self._save_excel()
    
    def update_user_subscription(self, user_id: int, is_subscribed: bool, decision: str = None):
        """Update subscription status and decision"""
        mask = self.df['user_id'] == user_id
        self.df.loc[mask, 'subscription_checked'] = is_subscribed
        if decision:
            self.df.loc[mask, 'decision'] = decision
        self._save_excel()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get specific user by ID"""
        users = self.df[self.df['user_id'] == user_id].to_dict('records')
        return users[0] if users else None
    
    def reload(self):
        """Reload DataFrame from Excel"""
        self.df = self._load_excel()
