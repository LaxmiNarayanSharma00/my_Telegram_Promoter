import logging
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict
from .user_manager import UserManager
from .conversation_handler import ConversationHandler
from .response_analyzer import ResponseAnalyzer
import yaml
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError
from pathlib import Path

BASE_DIR= Path(__file__).parent.parent

class LevelProcessor:
    """Process users at each level and manage transitions"""
    
    def __init__(self, client_manager, user_manager: UserManager, conv_handler: ConversationHandler):
        self.logger = logging.getLogger(__name__)
        self.client_manager = client_manager
        self.user_manager = user_manager
        self.conv_handler = conv_handler
        self.analyzer = ResponseAnalyzer()
    
    async def process_all_levels(self, max_per_day: int = 5) -> Dict:
        """Process all user levels in sequence"""
        results = {}
        
        results['level_0'] = await self.conv_handler.send_level_0_messages(max_per_day)
        await asyncio.sleep(2)
        
        results['level_1'] = await self._process_level_1()
        await asyncio.sleep(2)
        
        results['level_2'] = await self.conv_handler.send_level_2_messages()
        await asyncio.sleep(2)
        
        results['level_3'] = await self._process_level_3()
        await asyncio.sleep(2)
        
        results['level_4'] = await self.conv_handler.send_level_4_messages()
        await asyncio.sleep(2)
        
        results['level_5_check'] = await self._process_level_4()
        await asyncio.sleep(2)
        
        results['level_5_final'] = await self._check_level_5()
        
        self.logger.info(f"Level processing complete: {results}")
        return results
    
    async def _process_level_1(self) -> Dict[str, int]:
        """Check level 0 users for affirmative responses"""
        stats = {"promoted": 0, "no_response": 0, "declined": 0, "unclear": 0}
        
        users = self.user_manager.get_users_by_level(0)
        
        for user in users:
            response = await self._get_latest_message(user['user_id'])
            
            if response:
                status = self.analyzer.analyze_response(response, level='level_1')
                self.user_manager.update_user_response(user['user_id'], response, status)
                
                if status == "yes":
                    self.user_manager.update_user_level(user['user_id'], 1)
                    stats['promoted'] += 1
                elif status == "no":
                    stats['declined'] += 1
                elif status == "unclear":
                    stats['unclear'] += 1
            else:
                stats['no_response'] += 1
            
            await asyncio.sleep(0.5)
        
        self.logger.info(f"Level 1 processing: {stats}")
        return stats
    
    async def _process_level_3(self) -> Dict[str, int]:
        """Check level 2 users for affirmative responses (provide emails)"""
        stats = {"promoted": 0, "no_response": 0, "declined": 0, "unclear": 0}
        
        users = self.user_manager.get_users_by_level(2)
        
        for user in users:
            response = await self._get_latest_message(user['user_id'])
            print(f"User {user['user_id']} response at level 3: '{response}'")
            
            if response:
                ai_response = self.analyzer.give_response(response, level='level_3')
                print(f"AI analysis for user {user['user_id']} at level 3: '{ai_response}'")
                CONFIG_PATH = BASE_DIR / "config" / "level_messages.yaml"
                with open(CONFIG_PATH, "r") as f:
                        data = yaml.safe_load(f)
                
                data['levels']['level_4'] = ai_response

                with open(CONFIG_PATH, "w") as f:
                        yaml.safe_dump(data, f)
                
                self.user_manager.update_user_response(user['user_id'], response, "yes")

                self.user_manager.update_user_level(user['user_id'], 3)

            else:
                stats['no_response'] += 1
            
            await asyncio.sleep(0.5)
        
        self.logger.info(f"Level 3 processing: {stats}")
        return stats
    
    async def _process_level_4(self) -> Dict[str, int]:
        """Check level 4 users for channel subscription"""
        stats = {"subscribed": 0, "not_subscribed": 0, "sent_l5": 0}
        
        users = self.user_manager.get_users_by_level(4)
        
        for user in users:
            is_member = await self._check_channel_member(user['user_id'])
            
            if is_member:
                self.user_manager.update_user_subscription(
                    user['user_id'],
                    True,
                    decision="success"
                )
                stats['subscribed'] += 1
            else:
                last_msg_date = user.get('last_message_date')
                
                if last_msg_date:
                    try:
                        from datetime import datetime
                        msg_date = datetime.fromisoformat(last_msg_date)
                        days_passed = (datetime.now(timezone.utc) - msg_date).days
                        
                        if days_passed >= 1:
                            # message = "While applying the job updates try to contact me if possible I will provide the referral through my contact"
                            message = self.config['levels']['level_5']['messages']
                            if await self.conv_handler._send_dm(user['user_id'], message):
                                self.user_manager.update_user_level(user['user_id'], 5)
                                stats['sent_l5'] += 1
                    except:
                        pass
                
                stats['not_subscribed'] += 1
            
            await asyncio.sleep(0.5)
        
        self.logger.info(f"Level 4 (subscription check): {stats}")
        return stats
    
    async def _get_latest_message(self, user_id: int) -> str:
        """Get latest message from user"""
        try:
            messages = []
            client = self.client_manager.get_client()
            if client is None:
                 raise RuntimeError("Telegram client not initialized")            
            user = self.user_manager.get_user(user_id)
            if not user or not user.get('last_message_date'):
                return ""
            

            last_bot_message_time = datetime.fromisoformat(user['last_message_date'])
            
            user_messages = []
            async for msg in client.iter_messages(user_id, reverse=False):
                if msg.text:
                    msg_time = msg.date
                    
                    # Only messages AFTER bot's last message
                    if msg_time > last_bot_message_time:
                        # Only from user, not from bot
                        if msg.sender_id == user_id:
                            user_messages.append(msg.text)
            
            # Return concatenated user responses
            if user_messages:
                return " ".join(reversed(user_messages))
            return ""
            
        except Exception as e:
            self.logger.warning(f"Failed to get message from {user_id}: {e}")
            return None

    async def _check_channel_member(self, user_id: int) -> bool:
        client = self.client_manager.get_client()
        if client is None:
            raise RuntimeError("Telegram client not initialized")

        try:
            channel = await client.get_entity("Jobs_Lelo")
            await client(GetParticipantRequest(channel, user_id))
            return True
        except UserNotParticipantError:
            return False
        except Exception as e:
            self.logger.warning(f"Membership check failed for {user_id}: {e}")
            return False

    
    async def _check_level_5(self) -> Dict[str, int]:
        """Check level 5 users for channel subscription (no messages sent)"""
        stats = {"subscribed": 0, "not_subscribed": 0}
        
        users = self.user_manager.get_users_by_level(5)
        
        for user in users:
            is_member = await self._check_channel_member(user['user_id'])
            
            if is_member:
                self.user_manager.update_user_subscription(
                    user['user_id'],
                    True,
                    decision="success"
                )
                stats['subscribed'] += 1
            else:
                stats['not_subscribed'] += 1
            
            await asyncio.sleep(0.5)
        
        self.logger.info(f"Level 5 (final check): {stats}")
        return stats
