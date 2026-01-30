post="""Company name: Cisco
Role: Software Engineer Intern
Batch Eligible: 2028 graduates
Expected Stipend: INR 98K per month
Location: Bangalore, India 

Apply Link: https://bit.ly/4bdqFoi 

Do share with your Juniors too 

Do like the post for LinkedIn Algorithm 😊 and provide your support for more such updates 😇

_Source: Jobs and Internships | Date: 2026-01-22 14:53:28 UTC_"""

import re

def handle_source_1(text: str) -> str:
        if not text:
            return ""

        if re.search(
            r"Do like the post for LinkedIn Algorithm",
            text,
            flags=re.IGNORECASE
        ):
            return "hi"

        if re.search(
            r"https?://(www\.)?whatsapp\.com/\S+",
            text,
            flags=re.IGNORECASE
        ):
            return "hi"

        cleaned = text

        cleaned = re.sub(
            r"Community for Jobs\s*&\s*Internships Updates:\s*https?://\S+",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # ✅ Normalize spacing
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        return cleaned

print(handle_source_1(post))