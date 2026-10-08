"""quotes.toscrape.com의 robots.txt 정책을 확인합니다."""

from urllib.robotparser import RobotFileParser

import requests

BASE_URL = "https://quotes.toscrape.com"
ROBOTS_URL = f"{BASE_URL}/robots.txt"
USER_AGENT = "data-eng-class-crawler/1.0 (learning purpose)"
TIMEOUT_SEC = 10
DELAY_SEC = 1.0


def main() -> None:
    response = requests.get(
        ROBOTS_URL,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_SEC,
    )

    if response.status_code == 404:
        print("robots.txt 상태: HTTP 404 (정책 파일 없음)")
        print("수집 가능 여부: True (robots 정책 파일이 없어 진행)")
        print("이 크롤러 요청 간격: 1초")
        return

    response.raise_for_status()

    parser = RobotFileParser()
    parser.set_url(ROBOTS_URL)
    parser.parse(response.text.splitlines())

    target_url = f"{BASE_URL}/"
    allowed = parser.can_fetch(USER_AGENT, target_url)
    crawl_delay = parser.crawl_delay(USER_AGENT)

    print(f"수집 가능 여부: {allowed}")
    print(
        "robots.txt 권고 간격: "
        f"{crawl_delay if crawl_delay is not None else '미지정'}초"
    )
    print(f"이 크롤러 요청 간격: {max(DELAY_SEC, float(crawl_delay or 0))}초")

    if not allowed:
        raise SystemExit("robots.txt에서 수집을 허용하지 않아 종료합니다.")


if __name__ == "__main__":
    main()