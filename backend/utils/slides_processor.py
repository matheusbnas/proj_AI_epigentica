from typing import Dict, List, Any
import json
from .router_llm import LLMRouter  # Now correctly importing LLMRouter
from .cache_manager import SlidesCacheManager
import asyncio
import logging

logger = logging.getLogger(__name__)

class SlidesProcessor:
    def __init__(self, llm_router: LLMRouter, batch_size=5):
        self.llm_router = llm_router
        self.cache_manager = SlidesCacheManager()
        self.batch_size = batch_size

    async def process_report_data(self, report_data: Dict[str, Any], progress_callback=None) -> List[Dict[str, Any]]:
        logger.info("Verificando cache dos slides")
        cache_key = self.cache_manager.get_cache_key(report_data)
        cached_slides = self.cache_manager.get_cached_slides(cache_key)
        
        if cached_slides:
            logger.info("Slides encontrados em cache")
            if progress_callback:
                await progress_callback(100, "Loaded from cache")
            return cached_slides

        logger.info("No cache found, processing slides")
        slides = []
        total_pages = len(report_data.get("paginas", []))
        logger.info(f"Processando {total_pages} páginas no total")
        
        # Process in batches
        for i in range(0, total_pages, self.batch_size):
            batch = report_data["paginas"][i:i + self.batch_size]
            logger.info(f"Processing batch {i//self.batch_size + 1}, pages {i+1}-{i+len(batch)}")
            batch_slides = await self._process_batch(batch)
            slides.extend(batch_slides)
            
            if progress_callback:
                progress = int((i + len(batch)) / total_pages * 100)
                await progress_callback(progress, f"Processing pages {i+1}-{i+len(batch)}")

        logger.info("Caching processed slides")
        self.cache_manager.cache_slides(cache_key, slides)
        
        return slides

    async def _process_batch(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        slides = []
        tasks = []
        
        for page in pages:
            tasks.append(self._process_page(page))
            
        batch_results = await asyncio.gather(*tasks)
        slides.extend([slide for slide in batch_results if slide])
        
        return slides

    async def _process_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        # Extract title and content
        text = page.get("texto", "")
        title_match = text.split("\n")[0] if text else ""
        
        if title_match.startswith("# "):
            title = title_match[2:]
            content = "\n".join(text.split("\n")[1:])
        else:
            title = ""
            content = text
        
        # Create slide
        slide = {
            "type": "section",
            "title": title,
            "content": content
        }
        
        # Add images if present
        if page.get("imagens"):
            slide["images"] = page["imagens"]
        
        return slide
