import logging
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from .core import UserManager, GroupExtractor, ConversationHandler, LevelProcessor


class DMPromotionService:
    """Main service for DM-based channel promotion"""
    
    def __init__(self, client_manager):
        self.logger = logging.getLogger(__name__)
        self.client_manager = client_manager
        
        self.user_manager = UserManager()
        self.group_extractor = GroupExtractor(client_manager, self.user_manager)
        self.conv_handler = ConversationHandler(client_manager, self.user_manager)
        self.level_processor = LevelProcessor(client_manager, self.user_manager, self.conv_handler)
        
        self.last_extraction = None
        self.extraction_interval_days = 2
    
    async def run(self):
        """Main execution loop"""
        self.logger.info("Starting DM Promotion Service")
        
        should_extract = self._should_extract()
        print(should_extract)
        if should_extract:
            self.logger.info("Running user extraction and categorization")
            await self.group_extractor.extract_and_categorize()
            self.last_extraction = datetime.now(timezone.utc)
        
        self.logger.info("Processing user levels")
        await self.level_processor.process_all_levels(max_per_day=5)
        
        self.logger.info("DM Promotion Service completed")
    
    def _should_extract(self) -> bool:
        """Check if enough time has passed for another extraction"""
        extraction_log = Path(__file__).parent / "data" / "extraction_log.txt"
        print(extraction_log)
        if not extraction_log.exists():
            extraction_log.write_text(datetime.now(timezone.utc).isoformat())
            return True
        print(extraction_log)
        try:
            last_time = extraction_log.read_text().strip()
            
            last_extraction = datetime.fromisoformat(last_time)
            
            time_diff = (datetime.now(timezone.utc) - last_extraction).days
            
            if time_diff >= self.extraction_interval_days:
                extraction_log.write_text(datetime.now(timezone.utc).isoformat())
                return True
        except:
            extraction_log.write_text(datetime.now(timezone.utc).isoformat())
            return True
        
        return False
