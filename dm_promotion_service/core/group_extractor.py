import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Set
import yaml
from pathlib import Path
from .user_manager import UserManager
from .response_analyzer import ResponseAnalyzer


class GroupExtractor:
    """Extract users from groups and categorize them"""
    
    def __init__(self, client_manager, user_manager: UserManager):
        self.logger = logging.getLogger(__name__)
        self.client_manager = client_manager
        self.user_manager = user_manager
        self.analyzer = ResponseAnalyzer()
        
        config_path = Path(__file__).parent.parent / "config" / "extraction_groups.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    async def extract_and_categorize(self) -> Dict[str, int]:
        """Extract users from groups and categorize as job-seekers"""
        stats = {"added": 0, "skipped": 0}
        extracted_users: Set[int] = set()
        
        groups = self.config['extraction']['groups']
        max_additions = (
            self.config['dm_limits']['max_per_day'] * 
            self.config['extraction']['frequency_days']
        )
        client = self.client_manager.get_client()
        if client is None:
            raise RuntimeError("Telegram client not initialized")
        for group in groups:
            try:
                messages = []
                async for message in client.iter_messages(
                    group['username'],
                    limit=20,
                    reverse=False
                ):
                    if message.text and message.sender_id:
                        messages.append({
                            'text': message.text,
                            'sender_id': message.sender_id,
                            'username': message.sender.username if message.sender else None
                        })
                
                for msg in messages:
                    if msg['sender_id'] in extracted_users:
                        continue
                    
                    if stats['added'] >= max_additions:
                        break
                    
                    is_seeker = await self.analyzer.categorize_user(msg['text'])
                    
                    if is_seeker:
                        added = self.user_manager.add_user(
                            msg['sender_id'],
                            msg['username'] or f"user_{msg['sender_id']}"
                        )
                        if added:
                            stats['added'] += 1
                            extracted_users.add(msg['sender_id'])
                        else:
                            stats['skipped'] += 1
                
                self.logger.info(f"Extracted from {group['name']}: {len(extracted_users)} unique users")
                
            except Exception as e:
                self.logger.error(f"Error extracting from {group['username']}: {e}")
        
        self.logger.info(f"Extraction complete: {stats['added']} added, {stats['skipped']} skipped")
        return stats
