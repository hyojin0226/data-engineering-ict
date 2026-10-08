# 2주차 산출물 — 쇼핑몰 ERD 설계와 크롤링 파이프라인

## 구성

| 파일 | 설명 |
|---|---|
| [ERD_설계서.md](ERD_설계서.md) | 쇼핑몰 4개 테이블의 ERD, 관계, 정규화와 반정규화 근거 |
| [ERD.png](ERD.png) | 설계서에 삽입한 ERD 제출 이미지 |
| [check_robots.py](check_robots.py) | 크롤링 전에 robots.txt 허용 여부 확인 |
| [crawler_pipeline.py](crawler_pipeline.py) | fetch → parse → load 3단계 크롤링 |
| [schema.sql](schema.sql) | 중복 방지 제약이 있는 `quotes` 테이블 생성 |

## 실행 환경 준비

Docker Desktop과 Python 3.10 이상이 필요합니다. 수업에서 준비한 MySQL 컨테이너를 시작합니다.

```bash
docker start de-mysql
```

프로젝트 루트에서 가상환경을 만들고 의존성을 설치합니다.

Windows PowerShell:

```powershell
cd week02
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install requests beautifulsoup4 pymysql
```

macOS, Linux 또는 WSL:

```bash
cd week02
python3 -m venv .venv
source .venv/bin/activate
python -m pip install requests beautifulsoup4 pymysql
```

## 데이터베이스 준비

아래 예시는 수업용 컨테이너의 계정이 `root/dataeng123`인 경우입니다. 계정이 다르면 `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` 환경 변수로 연결 정보를 지정할 수 있습니다. `MYSQL_DATABASE` 기본값은 `shop`입니다.

Windows PowerShell에서 `week02` 디렉터리 기준:

```powershell
Get-Content -Raw .\schema.sql | docker exec -i de-mysql mysql -uroot -pdataeng123
```

macOS, Linux 또는 WSL:

```bash
docker exec -i de-mysql mysql -uroot -pdataeng123 < schema.sql
```

`schema.sql`은 데이터베이스와 테이블을 없애지 않고, 없을 때만 생성합니다. `UNIQUE(author, quote_text)` 제약이 같은 명언의 중복 저장을 막습니다.

## 실행

먼저 수집 허용 여부를 확인하고, 허용된 경우 3페이지를 수집합니다.

```bash
python check_robots.py
python crawler_pipeline.py
```

크롤러는 User-Agent를 보내고, robots.txt에서 더 긴 간격을 요구하면 그 간격을 따릅니다. 현재 quotes.toscrape.com의 robots.txt는 HTTP 404를 반환하므로 정책 파일이 없는 경우로 처리하고, 페이지 요청 사이에 최소 1초 쉽니다. 5xx나 네트워크 오류에서는 안전을 위해 실행을 멈춥니다.

## 실행 검증 결과

2026-10-08 사용자 WSL 환경에서 실행한 결과입니다.

- robots.txt는 HTTP 404였고, 정책 파일이 없는 경우로 처리해 수집을 진행했습니다. 요청 간격은 1초였습니다.
- 1~3페이지에서 각각 명언 10개를 읽었고, 모두 이미 저장된 행이라 페이지마다 saved 0을 출력했습니다.
- 실행 뒤 quotes 테이블 건수는 30건으로 유지됐습니다.

실행 전부터 같은 데이터 30건이 있었으므로 이번 결과는 재실행 중복 방지와 건수 유지를 확인합니다. 빈 테이블에서 첫 실행하면 3페이지 각각 10건을 저장해 총 30건이 되고, 이후 재실행은 추가 저장 0건이 되는 것이 기대 결과입니다.
## 남은 개선점

- 현재 `tags`는 쉼표로 연결한 문자열입니다. 태그별 검색과 집계를 위해 `tags`와 `quote_tags` 교차 테이블로 정규화할 수 있습니다.
- 페이지 하나가 실패하면 전체 실행이 중단됩니다. 재시도 횟수와 실패 페이지 로그를 추가하면 장시간 수집에 더 적합합니다.