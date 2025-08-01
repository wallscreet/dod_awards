from pydantic import BaseModel
from dataclasses import dataclass, field
from typing import Optional, List
from urllib.parse import urlencode
import feedparser


class Entity(BaseModel):
    name: str
    contract_id: str
    location: str


class ContractingAgency(BaseModel):
    name: str
    location: str


class DodContractInfo(BaseModel):
    """
    Pydantic model to extract contract details from text extracted from DOD awards/contracts URL extracted from the DOD contracts RSS feed.
    """
    contractors: list[Entity]
    purpose: str
    amount: float
    contracting_agency: ContractingAgency


@dataclass
class Feed:
    """
    Base class for rss feeds.
    """
    name: str
    base_url: str
    description: str = ""
    content_type: Optional[str] = None
    site: Optional[str] = None
    max: Optional[int] = None
    url: str = field(init=False)

    def __post_init__(self):
        params = {}
        if self.site is not None:
            params["Site"] = self.site
        if self.content_type is not None:
            params["ContentType"] = self.content_type
        if self.max is not None:
            params["Max"] = str(self.max)

        query_string = urlencode(params)
        self.url = f"{self.base_url}?{query_string}" if query_string else self.base_url


@dataclass
class BaseRSS:
    """
    Base class for RSS sources to contain their feeds.
    """
    feeds: List[Feed]

    def get_url_by_name(self, name: str) -> Optional[str]:
        feed = next((f for f in self.feeds if f.name == name), None)
        if not feed:
            raise ValueError(f"No feed found with name '{name}'")
        return feed.url


@dataclass
class DOD_RSS(BaseRSS):
    """
    RSS feeds for the United States Department of Defense (DOD).
    """
    feeds: list[Feed] = field(default_factory=lambda: [
            Feed(
                name="Feature Stories",
                content_type="800",
                base_url= "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx",
                site="945",
                max=10,
                description="Feature stories from the Department of Defense."
            ),
            Feed(
                name="News",
                content_type="1",
                base_url="https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx",
                site="945",
                max=10,
                description="News from the Department of Defense."
            ),
            Feed(
                name="Releases",
                content_type="9",
                base_url="https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx",
                site="945",
                max=10,
                description="Press releases from the Department of Defense."
            ),
            Feed(
                name="Contract Announcements",
                content_type="400",
                base_url="https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx",
                site="945",
                max=10,
                description="U.S. Department of Defense Contracts valued at $7.5 million or more are announced each business day at 5 p.m."
            ),
            Feed(
                name="Advisories",
                content_type="500",
                base_url="https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx",
                max=10,
                description="Advisories from the Department of Defense."
            )
    ])

    def get_contract_announcements_feed(self) -> list[str]:
        """ Contract Announcements
        Returns a list of entries containing links for daily contract announcements.
        """
        contracts_rss_url = self.get_url_by_name("Contract Announcements")
        entries = feedparser.parse(contracts_rss_url)

        return entries