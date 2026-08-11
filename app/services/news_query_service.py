from app.models.security import SecurityMaster
from app.services.security_master_service import SecurityMasterService


class NewsQueryService:
    def aliases(self, security: SecurityMaster) -> list[str]:
        aliases = SecurityMasterService().search_aliases(security)
        precise = [
            alias
            for alias in aliases
            if len(alias) > 3 or not alias.isascii() or " " in alias
        ]
        return (precise or aliases)[:4]

    def query(self, security: SecurityMaster) -> str:
        aliases = self.aliases(security)
        return " OR ".join(f'"{alias}"' for alias in aliases)
