from Free_API_Load_balancer import generate
from enum import Enum as ENUM
import re
from enum import Enum
from .utils_handlers_groups import UtilsHandlersGroups

class SenderList(Enum):
    JOBS_AND_INTERNSHIPS = "Jobs and Internships"
    JOBS_AND_INTERNSHIPS_1 = "Jobs and Internships1"
    INTERN_FREAK = "InternFreak"
    TECH_UPRISE = "Tech Uprise"
    DOT_AWARE = "Dot Aware"
    GO_CAREERS = "Go Careers"
    TORCHBEARER_CORE = "Torchbearer Core"
    TORCHBEARER = "Torchbearer"
    OFF_CAMPUS_JOBS_AND_INTERNSHIPS = "Off Campus Jobs and Internships"
    FRESHERS_HUNT = "Freshers Hunt"
    GET_JOBS = "Get Jobs"
    FRESHER_OFFCAMPUS_DRIVES = "Fresher Offcampus Drives"
    FRESHER_JOBS_ADDA = "Fresher Jobs Adda"
    OFFCAMPUS_PHODENGE = "Offcampus Phodenge"
    FRESHER_OFFCAMPUS = "Fresher Offcampus"
    FRESHERS_JOBS_UPDATES = "Freshers Jobs Updates"


class AIService:
    """AI-based content refinement service"""

    def __init__(self):
                
        self.prompt_refine = """
            You are given a post text scraped from social media.
          
            Task:
            - Extract and keep ONLY core job information.
            - Remove all promotional content (WhatsApp, Telegram, emojis, YouTube Links).
            - Rewrite in a clean, professional, neutral tone.
            - Output in the following fixed format:

            Company:
            Position:
            Experience:
            Qualification:
            Location:
            Apply Link:

            Rules:
            - Do NOT add new information.
            - If a field is missing, infer only if explicitly obvious, else keep as provided.
            - Keep output concise and factual.

        """
        self.prompt_classification="classify whether the following post is a job posting or promotional content. You have to Respond  with one word  'Job' or 'Promo' .\n\nPost:"
        
    def refine_posts(self, posts):
        refined = []
        handler=UtilsHandlersGroups()
        for post in posts:

            if post and post.source == SenderList.JOBS_AND_INTERNSHIPS.value:
                post.text = handler.handle_source_1(post.text)
                if not post.text:
                    continue
            elif post and post.source == SenderList.INTERN_FREAK.value:
                post.text = handler.handle_source_2(post.text)

            elif post and post.source == SenderList.TORCHBEARER.value:
                post.text = handler.handle_source_3(post.text)
                
            elif post and post.source == SenderList.DOT_AWARE.value:
                post.text = handler.handle_source_4(post.text)
            
            elif post and post.source == SenderList.OFF_CAMPUS_JOBS_AND_INTERNSHIPS.value:
                post.text = handler.handle_source_5(post.text)


            elif post and post.source == SenderList.TECH_UPRISE.value:
                post.text = post.text
            
            elif post and post.source == SenderList.GO_CAREERS.value:
                post.text = post.text    
            
            elif post and post.source == SenderList.JOBS_AND_INTERNSHIPS_1.value:
                post.text = post.text       
            
            refined.append(post)

        return refined





