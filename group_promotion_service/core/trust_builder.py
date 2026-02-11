import logging
import asyncio

import random
from typing import Dict
from .message_selector import MessageSelector
from telethon import functions, types
from Free_API_Load_balancer import generate
class TrustBuilder:
    """Handle Phase 1-2 actions: reactions and replies"""
    
    def __init__(self, client_manager, group_manager, message_selector: MessageSelector):
        self.logger = logging.getLogger(__name__)
        self.client_manager = client_manager
        self.group_manager = group_manager
        self.message_selector = message_selector
    
    async def phase_1_react(self, entity: str, max_reactions: int = 3) -> Dict[str, int]:
        """Phase 1: React to recent messages with emoji"""
        stats = {"reacted": 0, "failed": 0}
        client = self.client_manager.get_client()
        try:
            # Fetch recent messages
            messages = []
            async for msg in client.iter_messages(entity, limit=20, reverse=True):
                if msg.text and not msg.from_scheduled:
                    messages.append(msg)
            
            if not messages:
                self.logger.info(f"No messages to react in {entity}")
                return stats
            
            # Select random K messages to react
            target_count = min(max_reactions, len(messages))
            selected_msgs = random.sample(messages, target_count)
            
            for msg in selected_msgs:
                # Check if already reacted
                if self.group_manager.has_reacted_to_message(entity, msg.id):
                    self.logger.info(f"Already reacted to message {msg.id}, skipping")
                    continue
                
                emoji = self.message_selector.select_reaction_emoji()
                
                if await self._add_reaction(entity, msg.id, emoji):
                    self.group_manager.add_reacted_message(entity, msg.id)
                    stats['reacted'] += 1
                    self.group_manager.update_last_action(entity, 'reaction')
                else:
                    stats['failed'] += 1
                
                await asyncio.sleep(random.uniform(1, 3))
        
        except Exception as e:
            self.logger.error(f"Error in phase_1_react: {e}")
        
        self.logger.info(f"Phase 1 reactions: {stats['reacted']} reacted, {stats['failed']} failed")
        return stats
    
    async def phase_2_reply(self, entity: str, max_replies: int = 2) -> Dict[str, int]:
        """Phase 2: Reply to recent messages with natural text"""
        stats = {"replied": 0, "failed": 0}
        client = self.client_manager.get_client()
        try:
            # Fetch recent messages
            messages = []
            async for msg in client.iter_messages(entity, limit=20, reverse=True):
                if msg.text and not msg.from_scheduled and msg.sender_id:
                    messages.append(msg)
            
            if not messages:
                self.logger.info(f"No messages to reply in {entity}")
                return stats
            
            # Select random K messages to reply
            target_count = min(max_replies, len(messages))
            selected_msgs = random.sample(messages, target_count)
            
            for msg in selected_msgs:
                # Check if already replied
                if self.group_manager.has_replied_to_message(entity, msg.id):
                    self.logger.info(f"Already replied to message {msg.id}, skipping")
                    continue
                
                # reply_text = self.message_selector.select_reply_message(entity, no_repeat_days)
                prompt_template = self.message_selector.config.get('ai_reply_prompt', "Reply to: {message_text}")
                
                prompt = prompt_template.format(message_text=msg.text)
                print(prompt)
                reply_text = generate(prompt=prompt, max_output_tokens=10)

                if await self._send_reply(entity, msg.id, reply_text):
                    self.group_manager.add_replied_message(entity, msg.id)
                    stats['replied'] += 1
                    self.group_manager.update_last_action(entity, 'reply')
                else:
                    stats['failed'] += 1
                
                await asyncio.sleep(random.uniform(2, 4))
        
        except Exception as e:
            self.logger.error(f"Error in phase_2_reply: {e}")
        
        self.logger.info(f"Phase 2 replies: {stats['replied']} replied, {stats['failed']} failed")
        return stats
    
    async def phase_2_react(self, entity: str, max_reactions: int = 5) -> Dict[str, int]:
        """Phase 2: Also react to messages"""
        return await self.phase_1_react(entity, max_reactions)
    
    async def _add_reaction(self, entity: str, message_id: int, emoji: str) -> bool:
        """Add emoji reaction to message"""
        client = self.client_manager.get_client()
        # print(f"Adding reaction {emoji} to message {message_id} in {entity}")
        try:
            await client(functions.messages.SendReactionRequest(
            peer=entity,
            msg_id=message_id,
            reaction=[types.ReactionEmoji(emoticon=emoji)]
        ))
            self.logger.info(f"Reacted with {emoji} to message {message_id} in {entity}")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to react to message {message_id}: {e}")
            return False
    
    async def _send_reply(self, entity: str, message_id: int, reply_text: str) -> bool:
        """Send threaded reply to message"""
        client = self.client_manager.get_client()
        try:
            await client.send_message(entity, reply_text, reply_to=message_id)
            self.logger.info(f"Replied to message {message_id} in {entity}")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to reply to message {message_id}: {e}")
            return False
