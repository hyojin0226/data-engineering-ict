"""quotes.toscrape.com을 fetch → parse → load 단계로 수집합니다."""

from __future__ import annotations

import os
import time
from datetime import datetime
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import pymysql
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://quotes.toscrape.com"
ROBOTS_URL = f"{BASE_URL}/robots.txt"
USER_AGENT = "data-eng-class-crawler/1.0 (learning purpose)"
DELAY_SEC = 1.0
TIMEOUT_SEC = 10
MAX_PAGES = 3

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "dataeng123")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "shop")


def check_robots() -> tuple[bool, float]:
    """robots.txt 허용 여부와 적용할 최소 요청 간격을 반환합니다."""
    response = requests.get(
        ROBOTS_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_SEC,
    )
    if response.status_code == 404:
        print("robots.txt가 HTTP 404입니다. 정책 파일이 없어 1초 간격으로 진행합니다.")
        return True, DELAY_SEC

    response.raise_for_status()

    parser = RobotFileParser()
    parser.set_url(ROBOTS_URL)
    parser.parse(response.text.splitlines())

    allowed = parser.can_fetch(USER_AGENT, f"{BASE_URL}/")
    robots_delay = parser.crawl_delay(USER_AGENT)
    delay = max(DELAY_SEC, float(robots_delay or 0))
    return allowed, delay


def fetch(url: str) -> str:
    """페이지 HTML을 가져옵니다."""
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_SEC,
    )
    response.raise_for_status()
    return response.text


def parse(html: str) -> tuple[list[dict[str, str]], str | None]:
    """명언, 저자, 태그를 추출하고 다음 페이지 주소를 반환합니다."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []

    for quote in soup.select("div.quote"):
        author = quote.select_one("small.author")
        quote_text = quote.select_one("span.text")
        if author is None or quote_text is None:
            continue

        rows.append(
            {
                "author": author.get_text(strip=True),
                "quote_text": quote_text.get_text(strip=True),
                "tags": ",".join(
                    tag.get_text(strip=True) for tag in quote.select("a.tag")
                ),
            }
        )

    next_link = soup.select_one("li.next a")
    next_url = urljoin(BASE_URL, next_link["href"]) if next_link else None
    return rows, next_url


def load(rows: list[dict[str, str]]) -> int:
    """DB에 넣고, UNIQUE 제약과 INSERT IGNORE로 중복을 건너뜁니다."""
    connection = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        autocommit=False,
    )

    try:
        with connection.cursor() as cursor:
            saved = 0
            for row in rows:
                saved += cursor.execute(
                    "INSERT IGNORE INTO quotes "
                    "(author, quote_text, tags, crawled_at) "
                    "VALUES (%s, %s, %s, %s)",
                    (
                        row["author"],
                        row["quote_text"],
                        row["tags"],
                        datetime.now(),
                    ),
                )
        connection.commit()
        return saved
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def run(max_pages: int = MAX_PAGES) -> None:
    if max_pages < 1:
        raise ValueError("max_pages는 1 이상이어야 합니다.")

    allowed, delay = check_robots()
    if not allowed:
        raise RuntimeError("robots.txt에서 수집을 허용하지 않아 종료합니다.")

    url = f"{BASE_URL}/"
    for page_number in range(1, max_pages + 1):
        html = fetch(url)
        rows, next_url = parse(html)
        saved = load(rows)
        print(f"page {page_number}: parsed {len(rows)}, saved {saved}")

        if not next_url or page_number == max_pages:
            break

        url = next_url
        time.sleep(delay)


if __name__ == "__main__":
    run()