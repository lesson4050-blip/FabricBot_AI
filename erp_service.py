import logging
import aiohttp
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory catalog simulating 1C / BAS ERP responses
MOCK_1C_STOCK: Dict[str, Dict[str, Any]] = {
    "SIENA 05-BIRCH": {
        "sku": "FAB-SN-05",
        "name": "SIENA 05-Birch",
        "category": "Портьєрна тканина",
        "in_stock": True,
        "balance_meters": 42.5,
        "warehouse": "Центральний склад (Київ)",
        "price_per_meter_uah": 680.0
    },
    "FLORENCE 02-IVORY": {
        "sku": "FAB-FL-02",
        "name": "Florence 02-Ivory",
        "category": "Тюль / льон",
        "in_stock": True,
        "balance_meters": 118.0,
        "warehouse": "Склад №2 (Львів)",
        "price_per_meter_uah": 450.0
    },
    "VERONA 14-ANTHRACITE": {
        "sku": "FAB-VR-14",
        "name": "Verona 14-Anthracite",
        "category": "Блекаут (Blackout)",
        "in_stock": False,
        "balance_meters": 0.0,
        "warehouse": "Центральний склад (Київ)",
        "price_per_meter_uah": 820.0
    }
}

class ERP1CService:
    """Handles communication with 1C:Enterprise / BAS HTTP-Services."""

    def __init__(self):
        self.base_url = settings.erp_1c_base_url
        self.auth = aiohttp.BasicAuth(settings.erp_1c_username, settings.erp_1c_password)
        self.timeout = aiohttp.ClientTimeout(total=settings.erp_1c_timeout_sec)

    async def check_stock(self, article: str, shade: Optional[str] = None) -> Dict[str, Any]:
        """Query 1C HTTP endpoint for available stock balances."""
        key = f"{article.strip().upper()} {shade.strip().upper() if shade else ''}".strip()
        
        # If in live production with active 1C URL
        if settings.erp_1c_base_url and not "example.com" in settings.erp_1c_base_url and not "localhost" in settings.erp_1c_base_url:
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    params = {"article": article}
                    if shade:
                        params["shade"] = shade
                    async with session.get(f"{self.base_url}/get_balance", params=params, auth=self.auth) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        logger.warning("1C HTTP-service returned status %s", resp.status)
            except Exception as e:
                logger.error("Failed to query 1C HTTP-service: %s", e)

        # Fallback to local catalog for demo/offline verification
        for stock_key, data in MOCK_1C_STOCK.items():
            if article.upper() in stock_key:
                if not shade or shade.upper() in stock_key:
                    return data

        return {
            "sku": "NOT_FOUND",
            "name": f"{article} {shade or ''}".strip(),
            "in_stock": False,
            "balance_meters": 0.0,
            "warehouse": "Не знайдено в базі 1С",
            "price_per_meter_uah": 0.0
        }

erp_service = ERP1CService()
