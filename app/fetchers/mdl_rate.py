import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.fetchers.base import Fetcher, FetchResult

logger = logging.getLogger(__name__)

KYIV_TZ = ZoneInfo("Europe/Kyiv")


class MdlRateFetcher(Fetcher):
    key = "mdl_rate"

    def fetch(self, topic: dict, now: datetime) -> FetchResult | None:
        config = topic.get("config", {})
        days_ahead = config.get("days_ahead", 1)

        kyiv_now = now.astimezone(KYIV_TZ)
        target_date = (kyiv_now + timedelta(days=days_ahead)).date()
        date_str = target_date.strftime("%d.%m.%Y")

        url = f"https://bank.gov.ua/ua/markets/exchangerates?date={date_str}&period=daily"
        logger.info("Fetching MDL rate for %s from %s", date_str, url)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Network error fetching NBU page: %s", e)
            return None

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            rate = self._extract_mdl_rate(soup)
        except Exception as e:
            logger.error("Parsing error: %s", e)
            return None

        if rate is None:
            logger.warning("MDL rate not found for %s", date_str)
            return None

        content_key = f"mdl_rate:{target_date.isoformat()}"
        text = (
            f"📅 *Курс MDL на {target_date.strftime('%d.%m.%Y')}*\n"
            f"🇲🇩 1 MDL = *{rate:.4f} UAH*"
        )

        return FetchResult(
            content_key=content_key,
            text=text,
            parse_mode="Markdown",
            metadata={"rate": rate, "date": target_date.isoformat()},
        )

    def _extract_mdl_rate(self, soup: BeautifulSoup) -> float | None:
        """Extract MDL rate from the NBU exchange rates page."""
        rows = soup.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2 and cells[1].text.strip() == "MDL":
                rate_text = cells[-1].text.strip().replace(",", ".")
                return float(rate_text)
        return None

    def next_run_after(self, topic: dict, now: datetime) -> datetime:
        """Next weekday at 17:00 Kyiv time."""
        kyiv_now = now.astimezone(KYIV_TZ)
        tomorrow = kyiv_now + timedelta(days=1)

        # Skip weekends: if tomorrow is Saturday, jump to Monday
        while tomorrow.weekday() >= 5:  # 5=Saturday, 6=Sunday
            tomorrow += timedelta(days=1)

        next_run = tomorrow.replace(hour=17, minute=0, second=0, microsecond=0)
        return next_run.astimezone(tz=None)  # Convert back to UTC
