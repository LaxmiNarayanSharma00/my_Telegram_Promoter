import logging
import asyncio
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict
from .user_manager import UserManager
from .response_analyzer import ResponseAnalyzer
from telethon.errors import RPCError
import random

class ConversationHandler:
    """Handle DM conversations with users"""
    
    def __init__(self, client_manager, user_manager: UserManager):
        self.logger = logging.getLogger(__name__)
        self.client_manager = client_manager
        self.user_manager = user_manager
        
        config_path = Path(__file__).parent.parent / "config" / "level_messages.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    async def send_level_0_messages(self, max_count: int = 5) -> Dict[str, int]:
        """Send initial greeting to level -1 users"""
        stats = {"sent": 0, "failed": 0}
        
        users = self.user_manager.get_users_by_level(-1)
        users = users[:max_count]
        
        # message = self.config['levels']['level_0']['message']
        message = random.choice(self.config['levels']['level_0']['messages'])
        
        client = self.client_manager.get_client()
        # try to pre-warm entity cache to reduce get_input_entity failures
        try:
            if client is not None:
                await client.get_dialogs()
        except Exception:
            pass

        for user in users:
            if await self._send_dm(user['user_id'], message):
                self.user_manager.update_user_level(user['user_id'], 0)
                stats['sent'] += 1
            else:
                stats['failed'] += 1
            
            await asyncio.sleep(random.randint(10, 20))
        
        self.logger.info(f"Level 0: {stats['sent']} sent, {stats['failed']} failed")
        return stats
    
    async def send_level_4_messages(self) -> Dict[str, int]:
        """Send the AI-generated level 3 response to level 3 users as confirmation"""
        stats = {"sent": 0, "failed": 0}
        
        users = self.user_manager.get_users_by_level(3)

        client = self.client_manager.get_client()
        try:
            if client is not None:
                await client.get_dialogs()
        except Exception:
            pass

        for user in users:
            # Get the AI-generated response from level 3
            ai_response = user.get('level_3_ai_response')
            
            if ai_response and ai_response.strip():
                if await self._send_dm(user['user_id'], ai_response):
                    stats['sent'] += 1
                else:
                    stats['failed'] += 1
                await asyncio.sleep(0.5)
                self.user_manager.update_user_level(user['user_id'], 4)
            else:
                self.logger.warning(f"No AI response stored for user {user['user_id']}, skipping level 4")
            
            await asyncio.sleep(1)
        
        self.logger.info(f"Level 4: {stats['sent']} sent, {stats['failed']} failed")
        return stats
    
    async def send_level_2_messages(self) -> Dict[str, int]:
        """Send emails, tips and channel link to level 1 users"""
        stats = {"sent": 0, "failed": 0}
        
        users = self.user_manager.get_users_by_level(1)

        client = self.client_manager.get_client()
        try:
            if client is not None:
                await client.get_dialogs()
        except Exception:
            pass
        
        messages = self.config['levels']['level_2']['messages']
        ct = 13
        for user in users:
            for msg in messages:
                if msg == "[EMAIL_XLSX]":
                    if await self._send_document(user['user_id']):
                        stats['sent'] += 1
                    else:
                        stats['failed'] += 1
                else:
                    if await self._send_dm(user['user_id'], msg):
                        stats['sent'] += 1
                    else:
                        stats['failed'] += 1
                
                await asyncio.sleep(0.5)
            
            self.user_manager.update_user_level(user['user_id'], 2)
            await asyncio.sleep(ct)
            ct -= 3
        
        self.logger.info(f"Level 2: {stats['sent']} sent, {stats['failed']} failed")
        return stats
    
    async def _send_dm(self, user_id: int, message: str) -> bool:
        """Send single DM, resolving entity if needed"""
        client = self.client_manager.get_client()
        if client is None:
            raise RuntimeError("Telegram client not initialized")

        try:
            # Prefer cached input entity (no network when possible)
            try:
                entity = await client.get_input_entity(user_id)
            except ValueError:
                # Not in cache: try to lookup using stored username first
                entity = None
                user = self.user_manager.get_user(user_id)
                username = user.get('username') if user else None

                if username:
                    try:
                        entity = await client.get_entity(username)
                    except Exception:
                        entity = None

                # Last resort: try to populate cache (dialogs) and retry
                if entity is None:
                    try:
                        await client.get_dialogs()
                        entity = await client.get_input_entity(user_id)
                    except Exception:
                        entity = None

            if entity is None:
                # Mark user as unreachable in sheet and skip
                try:
                    self.user_manager.update_user_response(user_id, '', 'unreachable')
                except Exception:
                    pass
                self.logger.warning(f"Failed to resolve entity for {user_id}")
                return False

            await client.send_message(entity, message)
            self.logger.info(f"Sent DM to {user_id}: {message[:50]}...")
            return True
        except RPCError as e:
            # Telethon RPC errors (privacy, peer invalid, flood, etc.)
            self.logger.warning(f"Telethon RPC error sending DM to {user_id}: {e}")
            try:
                self.user_manager.update_user_response(user_id, '', 'unreachable')
            except Exception:
                pass
            return False
        except Exception as e:
            self.logger.warning(f"Failed to send DM to {user_id}: {e}")
            return False

    
    async def _send_document(self, user_id: int) -> bool:
        """Send Excel document"""
        try:
            assets_root = Path(__file__).resolve().parents[2]
            print(f"Assets root: {assets_root}")
            excel_path = assets_root / "assets" / "promo_contacts.png"

            if not excel_path.exists():
                self.logger.warning(f"Asset file not found: {excel_path}")
                return False
            client = self.client_manager.get_client()
            if client is None:
                raise RuntimeError("Telegram client not initialized")            
            await client.send_file(user_id, str(excel_path))
            self.logger.info(f"Sent Excel to {user_id}")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to send Excel to {user_id}: {e}")
            return False
