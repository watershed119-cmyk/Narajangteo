# 나라장터 키워드 입찰공고 이메일 알림

매일 아침 공공데이터포털의 `조달청_나라장터 입찰공고정보서비스`를 호출해 지정한 키워드가 들어간 입찰공고를 모으고, 중복 발송을 제외한 **신규 공고가 있을 때만** 이메일 요약본을 보내는 Python 앱입니다.

## 기능

- 여러 키워드를 쉼표로 지정해 나라장터 입찰공고 검색
- 최근 N일 범위 조회(`LOOKBACK_DAYS`, 기본 1일)
- 공고번호와 차수 기준 중복 제거 및 발송 이력 저장
- 텍스트/HTML 이메일 동시 생성
- 신규 공고가 있을 때만 이메일 발송 (없으면 메일 생략)
- 로컬 실행, Docker 실행, GitHub Actions 평일 아침 예약 실행 지원

## 준비물

1. 공공데이터포털에서 `조달청_나라장터 입찰공고정보서비스` 활용 신청 후 **일반 인증키(Encoding이 아닌 Decoding 키 권장)**를 발급받습니다.
2. SMTP 발송 계정을 준비합니다. Gmail을 쓰는 경우 앱 비밀번호를 사용하는 것을 권장합니다.

## 환경 변수

| 변수 | 필수 | 예시 | 설명 |
| --- | --- | --- | --- |
| `NARA_API_KEY` | 예 | `abc123...` | 공공데이터포털 일반 인증키 |
| `NARA_KEYWORDS` | 예 | `홈페이지,AI,클라우드` | 검색할 입찰공고명 키워드 CSV |
| `EMAIL_TO` | 예 | `sales@example.com,ceo@example.com` | 수신자 CSV |
| `SMTP_HOST` | 예 | `smtp.gmail.com` | SMTP 서버 |
| `SMTP_PORT` | 아니오 | `587` | 기본값 587 |
| `SMTP_USERNAME` | 아니오 | `sender@example.com` | SMTP 로그인 ID |
| `SMTP_PASSWORD` | 아니오 | `app-password` | SMTP 로그인 비밀번호 |
| `SMTP_SENDER` | 아니오 | `sender@example.com` | 발신자 주소. 없으면 `SMTP_USERNAME` 사용 |
| `SMTP_USE_TLS` | 아니오 | `true` | STARTTLS 사용 여부. 기본값 true |
| `LOOKBACK_DAYS` | 아니오 | `1` | 조회 기간(최근 N일) |
| `NARA_NUM_ROWS` | 아니오 | `100` | 키워드별 최대 조회 건수 |
| `STATE_FILE` | 아니오 | `.narajangteo_state.json` | 발송 이력 파일 경로 |

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

export NARA_API_KEY="4bf226438dd94bee684facc29f0031a26e31b08a7853eaf2b828548b03130c7c"
export NARA_KEYWORDS="수질,수생태,생태하천,유역,물환경,어도,종적 연결성,횡적 연속성"
export EMAIL_TO="watershed119@gmail.com"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="watershed119@gmail.com"
export SMTP_PASSWORD="xmqsthxeqlaudczl"

narajangteo --dry-run  # 이메일 발송 없이 내용 확인
narajangteo            # 이메일 발송 및 발송 이력 저장
```

## Docker 실행

```bash
docker build -t narajangteo .
docker run --rm --env-file .env -v "$PWD/.state:/app/.state" narajangteo
```

`STATE_FILE=/app/.state/state.json`처럼 컨테이너 내부의 볼륨 경로를 지정하면 중복 발송 이력을 보존할 수 있습니다.

## GitHub Actions로 평일 아침 실행

`.github/workflows/daily-digest.yml`은 월~금 07:00 KST(22:00 UTC)에 실행되도록 설정되어 있습니다. 토·일·공휴일에는 자동 실행되지 않습니다. 저장소 Secrets에 아래 값을 등록하세요.

- `NARA_API_KEY`
- `NARA_KEYWORDS`
- `EMAIL_TO`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_SENDER`(선택)

> 참고: GitHub Actions의 기본 예시는 저장소 캐시로 발송 이력 파일을 보존합니다. 운영 환경에서는 작은 VPS/서버의 cron 또는 영구 볼륨이 있는 컨테이너 작업을 권장합니다.

### 실행·오류 확인

- **신규 공고 없음**: 메일은 오지 않지만 Actions 실행은 **초록색(성공)** 으로 끝납니다. 로그에 `No new notices; email skipped`가 보입니다.
- **API/SMTP 오류 등**: Actions 실행이 **빨간색(실패)** 으로 표시됩니다. 저장소 **Actions** 탭에서 해당 실행의 로그를 확인하세요.
- GitHub **Settings → Notifications**에서 **Actions** 실패 알림을 켜 두면, 메일이 없어도 오류를 이메일로 받을 수 있습니다.

## 운영 팁

- 공고명 검색 파라미터(`bidNtceNm`)를 사용하므로 키워드는 너무 길게 쓰기보다 핵심 명사 위주로 나누는 편이 좋습니다.
- 공공데이터포털 인증키 오류가 나면 Encoding 키가 아닌 Decoding 키를 `NARA_API_KEY`에 넣었는지 확인하세요.
- 메일이 스팸함으로 가면 `SMTP_SENDER` 도메인의 SPF/DKIM 설정을 확인하세요.
