# Week 01 — Linux & Docker

리눅스 커맨드와 셸 스크립트부터 Docker 이미지 빌드, 최적화, Compose 환경 구성까지의 1주차 실습 산출물입니다.

## 구성

| 경로 | 설명 |
| --- | --- |
| docker-compose.yml | PostgreSQL, pgAdmin, 파이썬 앱을 실행하는 주차 산출물 |
| app/Dockerfile | 의존성 파일을 먼저 복사해 레이어 캐시를 활용하는 기본 이미지 |
| app/Dockerfile.bad | 소스 전체를 먼저 복사하는 캐시 비효율 비교용 |
| app/Dockerfile.fat | 전체 Python 베이스 이미지 크기 비교용 |
| app/Dockerfile.multi | 멀티 스테이지 빌드 비교용 |
| app/app.py | 실행 환경과 Python 버전을 출력하는 실습 앱 |
| app/requirements.txt | 파이썬 의존성 |
| compose-test/docker-compose.yml | nginx와 curl 컨테이너의 별도 네트워크 실습 |

Dockerfile.bad, Dockerfile.fat, Dockerfile.multi는 비교 실험용이며 Compose 통합 환경은 기본 Dockerfile을 사용합니다. Dockerfile.save는 중복 백업본이라 산출물에서 제외했습니다.

## 실행 환경

- Docker Desktop 또는 Docker Engine이 실행 중이어야 합니다.
- Docker가 동작하는 터미널에서 버전을 확인합니다.

    docker version
    docker compose version

## 통합 환경 실행

저장소 루트가 아니라 이 README가 있는 week01 디렉터리에서 실행합니다.

    cd week01
    docker compose config
    docker compose up -d --build
    docker compose ps -a
    docker compose logs app

db와 admin은 계속 실행됩니다. app은 시작 시 메시지를 출력하고 종료하는 일회성 컨테이너이므로 Exited (0)은 정상입니다.

### 접속 정보

| 서비스 | 주소 | 실습 계정 |
| --- | --- | --- |
| pgAdmin | http://localhost:8081 | admin@example.com / admin123 |
| PostgreSQL (호스트 PC) | localhost:5432 | engineer / engineer123, DB pipeline |
| PostgreSQL (Compose 네트워크) | db:5432 | engineer / engineer123, DB pipeline |

pgAdmin에서 서버를 추가할 때 General 탭에 이름(예: pipeline-db)을 입력하고, Connection 탭에 Host=db, Port=5432, Maintenance database=pipeline, Username=engineer, Password=engineer123을 입력합니다.

위 계정은 로컬 학습용 예시입니다. 실제 서비스나 공개 운영 환경에서 재사용하지 마세요.
pgAdmin 컨테이너에는 설정 볼륨을 연결하지 않았으므로 컨테이너를 새로 만들면 등록한 서버 설정이 초기화될 수 있습니다.

## 확인한 실행 결과

2026-09-30에 Docker Compose 설정 검사를 통과했습니다. 기존 실습 스택과 포트·볼륨이 겹치지 않도록 임시 검증 프로젝트를 15432/18081 포트로 실행했습니다.

- db와 admin 서비스가 실행 중인 것을 확인했습니다.
- app은 안내 메시지와 Python 3.12.14를 출력한 뒤 Exited (0)으로 종료했습니다.
- 테스트 테이블과 1주차 완료 행을 넣고 docker compose down 후 다시 올린 다음에도 행이 남아 있는 것을 확인했습니다.
- 검증용 컨테이너와 볼륨은 확인 후 정리했습니다. 사용자의 기존 week1 스택과 데이터는 건드리지 않았습니다.
- pgAdmin에서 서버를 등록하는 브라우저 절차와 Dockerfile별 크기·재빌드 시간 비교값은 아직 이 README에 기록하지 않았습니다.

## 볼륨 데이터 보존 확인

PostgreSQL 데이터는 named volume인 pgdata에 저장됩니다. 다음 명령으로 데이터를 만든 뒤 컨테이너를 내리고 다시 올려 행이 남는지 확인합니다.

    docker compose exec db psql -U engineer -d pipeline -c "CREATE TABLE IF NOT EXISTS week1 (memo TEXT);"
    docker compose exec db psql -U engineer -d pipeline -c "INSERT INTO week1 VALUES ('1주차 완료');"
    docker compose down
    docker compose up -d
    docker compose exec db psql -U engineer -d pipeline -c '\dt'
    docker compose exec db psql -U engineer -d pipeline -c "SELECT * FROM week1;"

표 week1과 1주차 완료 행이 조회되면 일반 종료 후에도 볼륨이 데이터를 보존한 것입니다. docker compose down -v는 볼륨과 그 안의 실습 데이터를 삭제하므로 데이터 보존을 확인하기 전에는 사용하지 않습니다.

## 이미지 크기와 빌드 캐시 비교

week01 디렉터리에서 다음 이미지들을 각각 빌드하고 비교합니다.

    docker build -t data-app:good ./app
    docker build -t data-app:bad -f app/Dockerfile.bad ./app
    docker build -t data-app:fat -f app/Dockerfile.fat ./app
    docker build -t data-app:multi -f app/Dockerfile.multi ./app
    docker images data-app

캐시 비교는 같은 Dockerfile을 처음 빌드한 결과와 app.py만 수정한 뒤 다시 빌드한 결과를 비교합니다. 기본 Dockerfile은 requirements.txt를 먼저 복사해 의존성 설치 레이어를 유지하고, Dockerfile.bad는 소스 파일을 먼저 복사해 코드 변경 시 설치 레이어까지 다시 실행되는 구조입니다.

| 이미지 | Dockerfile | 실제 크기 | 코드만 변경한 재빌드 시간 |
| --- | --- | --- | --- |
| good | Dockerfile | 미기록 | 미기록 |
| bad | Dockerfile.bad | 미기록 | 미기록 |
| fat | Dockerfile.fat | 미기록 | 미기록 |
| multi | Dockerfile.multi | 미기록 | 미기록 |

크기와 시간은 Docker 버전, 운영체제, 캐시 상태에 따라 달라집니다. 로컬에서 측정하지 않은 수치는 채워 넣지 않았습니다.

## 실습 중 만난 문제와 해결

### Dockerfile 내용을 터미널에 입력

FROM, WORKDIR, COPY, RUN, CMD를 터미널 명령처럼 입력해 FROM: command not found 등의 오류가 발생했습니다. 이 단어들은 Linux 명령이 아니라 Dockerfile 지시어입니다.

해결: app 디렉터리에서 nano Dockerfile로 파일을 열고 지시어를 파일에 저장합니다. 터미널에서는 docker build 같은 명령을 실행합니다.

### Compose YAML을 터미널에 입력

services:, image:, environment: 등을 터미널에 입력해 services:: command not found 등의 오류가 발생했습니다. 이 항목들은 Compose 설정 파일 안에서 해석되는 YAML 키입니다.

해결: week01 루트에 docker-compose.yml 파일을 만들고 YAML 내용을 저장합니다. 터미널에서는 docker compose up, docker compose config 등을 실행합니다.

### Compose 설정 파일을 찾지 못함

docker compose config 실행 시 no configuration file provided: not found가 나왔습니다. 당시 디렉터리에는 app과 compose-test만 있고 루트 설정 파일이 없었습니다. 별도 실습용 compose-test/docker-compose.yml은 week01의 통합 설정을 대신하지 않습니다.

해결: docker-compose.yml을 week01 루트에 두고, 그 디렉터리에서 docker compose config를 실행합니다.

| 내용 | 작성 위치 |
| --- | --- |
| cd, ls, docker build, docker compose | 터미널 |
| FROM, RUN, COPY, CMD | Dockerfile |
| services, image, environment, ports | docker-compose.yml |
| print, import 등 | app.py |

## 정리

설정 문법은 각 설정 파일에 저장하고, 터미널에는 실행 명령을 입력합니다. Compose 설정 파일의 위치와 실행 디렉터리도 함께 확인해야 합니다.
