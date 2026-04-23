import scrapy
from urllib.parse import urlencode
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DATASETS = {
    "secop_ii": "jbjy-vk9h",
    "secop_integrado": "rpmr-utcd",
    "secop_i": "f789-7hwg",
    "secop_ii_2025": "dmgg-8hin",
}


class SecopSpider(scrapy.Spider):
    name = "secop"

    def __init__(
        self,
        dataset: str = "secop_ii",
        limit: int = 50000,
        output: str = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.dataset = dataset
        self.resource_id = DATASETS[dataset]
        self.limit = limit
        self.output_file = output
        self.collected = []

    def start_requests(self):
        base_url = f"https://www.datos.gov.co/resource/{self.resource_id}.json"

        for offset in range(0, self.limit, 1000):
            params = {"$limit": 1000, "$offset": offset}
            url = f"{base_url}?{urlencode(params)}"
            yield scrapy.Request(url, callback=self.parse, meta={"offset": offset})

    def parse(self, response):
        try:
            data = json.loads(response.text)
            if not data:
                return

            self.collected.extend(data)
            logger.info(f"Recibidos: {len(data)}, Total: {len(self.collected)}")

            if len(data) < 1000:
                logger.info(f"Completo: {len(self.collected)} registros")

        except json.JSONDecodeError as e:
            logger.error(f"Error decode: {e}")

    def closed(self, reason):
        if self.output_file and self.collected:
            with open(self.output_file, "w") as f:
                json.dump(self.collected, f)
            logger.info(f"Guardado: {self.output_file}")


def run_spider(dataset: str, limit: int = 50000, output: str = None):
    """Ejecuta el spider desde código."""
    from scrapy.crawler import CrawlerProcess
    from scrapy.settings import Settings

    settings = Settings()
    settings.set("LOG_LEVEL", "INFO")
    settings.set("REQUEST_FINGERPRINTER_IMPLEMENTATION", "2.7")
    settings.set(
        "TWISTED_REACTOR", "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
    )

    process = CrawlerProcess(settings)

    crawler = process.create_crawler(SecopSpider)
    process.crawl(crawler, dataset=dataset, limit=limit, output=output)

    process.start()


if __name__ == "__main__":
    import sys

    dataset = sys.argv[1] if len(sys.argv) > 1 else "secop_ii"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
    output = (
        sys.argv[3]
        if len(sys.argv) > 3
        else f"datalake/raw/contratacion/{dataset}.json"
    )

    run_spider(dataset, limit, output)
