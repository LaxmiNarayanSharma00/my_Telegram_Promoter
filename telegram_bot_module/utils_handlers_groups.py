import re
class UtilsHandlersGroups:
    def __init__(self):
        pass
    def handle_source_1(self, text: str) -> str:
        if not text:
            return ""

        # ❌ LinkedIn algorithm / engagement bait
        if re.search(
            r"Do like the post for LinkedIn Algorithm",
            text,
            flags=re.IGNORECASE
        ):
            return ""

        # ❌ WhatsApp promotions
        if re.search(
            r"https?://(www\.)?whatsapp\.com/\S+",
            text,
            flags=re.IGNORECASE
        ):
            return ""

        # ❌ LinkedIn profile follow / connect posts
        if re.search(
            r"You can follow me on LinkedIn|linkedin\.com/in/",
            text,
            flags=re.IGNORECASE
        ):
            return ""

        # ❌ Awareness / initiative / tagging placement cells (not jobs)
        if re.search(
            r"An initiative to help|Do Tag your College Placement Cells|Placement Cell|TPO",
            text,
            flags=re.IGNORECASE
        ):
            return ""

        cleaned = text

        # Remove community footer
        cleaned = re.sub(
            r"Community for Jobs\s*&\s*Internships Updates:\s*https?://\S+",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # Normalize spacing
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        return cleaned


    def handle_source_2(self, text: str) -> str:
        if not text:
            return ""


        if re.search(
            r"https?://\S*internfreak\.\S+",
            text,
            flags=re.IGNORECASE
        ):
            return ""

        return text

    def handle_source_3(self, text: str) -> str:
        if not text:
            return ""

        # Remove post if it contains YouTube or Instagram links
        if re.search(r"https?://(www\.)?(youtube\.com|youtu\.be)/\S+", text, flags=re.IGNORECASE):
            return ""
        if re.search(r"https?://(www\.)?instagram\.com/\S+", text, flags=re.IGNORECASE):
            return ""

        cleaned = text

        # Optional: normalize spacing
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        return cleaned
    
    def handle_source_4(self, text: str) -> str:
        if not text:
            return ""

        cleaned = text

        # Remove WhatsApp links
        cleaned = re.sub(
            r"https?://(www\.)?whatsapp\.com/\S+",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # Remove AccioJob links
        cleaned = re.sub(
            r"https?://go\.acciojob\.com/\S+",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # Remove AccioJob promo text
        cleaned = re.sub(
            r"₹\s*\d+LPA\s*to\s*₹\s*\d+LPA.*?Register\s*free:?(\s*)",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # Remove standalone WhatsApp Channel line
        cleaned = re.sub(
            r"WhatsApp\s*Channel\s*-?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # Normalize spacing
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        return cleaned
    

    def handle_source_5(self, text: str) -> str:
        if not text:
            return ""

        # ❌ Remove entire post if PlacementLelo links exist (apply/register/hackathons)
        if re.search(
            r"https?://(www\.)?placementlelo\.in/\S+",
            text,
            flags=re.IGNORECASE
        ):
            return ""

        # ❌ Remove entire post if resume builder / resume promo exists
        if re.search(
            r"resume\s*(builder|enhancer)|resume\s*tool|resume\s*link|bit\.ly/\S+",
            text,
            flags=re.IGNORECASE
        ):
            return ""

        cleaned = text

        # ❌ Remove Telegram links only (keep post otherwise)
        cleaned = re.sub(
            r"Telegram\s*:\s*https?://(t\.me|telegram\.me)/\S+",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # ❌ Remove WhatsApp links always
        cleaned = re.sub(
            r"https?://(www\.)?whatsapp\.com/\S+",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # Normalize spacing
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        return cleaned

    def handle_source_6(self, text: str) -> str:
        if not text:
            return ""

        cleaned = text

        # ❌ Remove Telegram invite/channel links (including your specific one)
        cleaned = re.sub(
            r"https?://(t\.me|telegram\.me)/join_Daily_Jobs_Placement_Update\S*",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # ❌ Remove lines like "Telegram link 👇👇"
        cleaned = re.sub(
            r"Telegram\s*link\s*👇+",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # Normalize spacing
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        return cleaned

