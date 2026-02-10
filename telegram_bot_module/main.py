"""Bot main orchestrator - minimal"""
import logging
import asyncio
from .config_manager import ConfigManager
from .telegram_client import TelegramClientManager
from .post_fetcher import PostFetcher
from .post_distributor import PostDistributor
from .post_distributer_channels import PostDistributorChannels
from .ai_service import AIService
from dm_promotion_service import DMPromotionService
from group_promotion_service import GroupPromotionService


class TelegramBot:
    """Bot orchestrator"""

    def __init__(self, config_path=None):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)
        
        self.config = ConfigManager(config_path)
        # self.config_promotion=ConfigManager(config_path="config_promotion.yaml")
        assert self.config.validate(), "Config validation failed"
        
        tg_config = self.config.get_telegram_config()
        self.client_mgr = TelegramClientManager(
            tg_config["api_id"],
            tg_config["api_hash"],
            tg_config["session_name"]
        )
        
        self.fetcher = PostFetcher(self.client_mgr, self.config)
        self.distributor = PostDistributor(self.client_mgr, self.config)
        self.distributor_channels = PostDistributorChannels(self.client_mgr)
        self.ai_service = AIService()
        self.dm_promotion_service = DMPromotionService(self.client_mgr)
        self.group_promotion_service = GroupPromotionService(self.client_mgr)
        self.logger.info("Bot initialized")

    async def initialize(self) -> bool:
        """Init and connect"""
        if not await self.client_mgr.initialize():
            self.logger.error("Client init failed")
            return False
        self.logger.info("Connected")
        return True

    async def shutdown(self):
        """Disconnect"""
        await self.client_mgr.disconnect()

    async def run_once(self):
        """Fetch and distribute once"""
        if not await self.initialize():
            return False
        
        try:

            posts = await self.fetcher.fetch_all()
            refined_posts = self.ai_service.refine_posts(posts)

            # with open("refined_posts.txt", "w", encoding="utf-8") as f:
            #     for original, refined in zip(posts, refined_posts):
            #         f.write("Original Post:\n")
            #         f.write(original.text + "\n")
            #         f.write("Refined Post:\n")
            #         f.write(refined.text + "\n")
            #         f.write("-" * 40 + "\n")

            # await self.distributor_channels.send_posts()

            if posts:
                await self.distributor.send_posts(refined_posts)
            else:
                self.logger.info("No posts to distribute")
            
            await self.dm_promotion_service.run()
            await self.group_promotion_service.run()
            
            return True
        finally:
            await self.shutdown()

