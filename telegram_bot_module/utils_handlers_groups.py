import re
class UtilsHandlersGroups:
    def __init__(self):
        pass
    def handle_source_1(self, text: str) -> str:
        if not text:
            return ""

        if re.search(
            r"Do like the post for LinkedIn Algorithm",
            text,
            flags=re.IGNORECASE
        ):
            return ""

        if re.search(
            r"https?://(www\.)?whatsapp\.com/\S+",
            text,
            flags=re.IGNORECASE
        ):
            return ""

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