"""
Satellite Data Service — Provider Router
==========================================

Routes satellite data requests to the configured provider.
Controlled by the SATELLITE_PROVIDER environment variable:
  - 'sentinel' (default) — Uses Sentinel Hub API
  - 'gee' — Uses Google Earth Engine (pending credentials)

Usage:
    from app.services.satellite_service import satellite_service
    result = await satellite_service.get_ndvi(latitude=..., longitude=...)
"""

from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.services.sentinel_service import SentinelService
from app.services.gee_service import GEEService


class SatelliteService:
    """
    Unified satellite data interface.
    Delegates to the active provider based on SATELLITE_PROVIDER config.
    """

    @staticmethod
    def _get_provider() -> str:
        return settings.SATELLITE_PROVIDER.lower()

    @staticmethod
    async def get_ndvi(
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        boundary: Optional[Dict[str, Any]] = None,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
    ) -> Dict[str, Any]:
        provider = SatelliteService._get_provider()
        if provider == "sentinel":
            return await SentinelService.get_ndvi(
                latitude=latitude, longitude=longitude,
                boundary=boundary, date_start=date_start, date_end=date_end,
            )
        elif provider == "gee":
            return await GEEService.get_ndvi(
                boundary=boundary, latitude=latitude, longitude=longitude,
                date_start=date_start, date_end=date_end,
            )
        else:
            return {"status": "error", "message": f"Unknown satellite provider: {provider}"}

    @staticmethod
    async def get_satellite_imagery(
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        boundary: Optional[Dict[str, Any]] = None,
        bands: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        provider = SatelliteService._get_provider()
        if provider == "sentinel":
            return await SentinelService.get_satellite_imagery(
                latitude=latitude, longitude=longitude,
                boundary=boundary, bands=bands,
            )
        elif provider == "gee":
            return await GEEService.get_satellite_imagery(
                boundary=boundary, latitude=latitude, longitude=longitude, bands=bands,
            )
        else:
            return {"status": "error", "message": f"Unknown satellite provider: {provider}"}

    @staticmethod
    async def get_crop_health_timeseries(
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        boundary: Optional[Dict[str, Any]] = None,
        months: int = 6,
    ) -> Dict[str, Any]:
        provider = SatelliteService._get_provider()
        if provider == "sentinel":
            return await SentinelService.get_crop_health_timeseries(
                latitude=latitude, longitude=longitude,
                boundary=boundary, months=months,
            )
        elif provider == "gee":
            return await GEEService.get_crop_health_timeseries(
                boundary=boundary, months=months,
            )
        else:
            return {"status": "error", "message": f"Unknown satellite provider: {provider}"}


# Singleton-style export for easy importing
satellite_service = SatelliteService()
