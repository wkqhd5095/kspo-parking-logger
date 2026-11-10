# kspo-parking-logger

올림픽공원 **실시간 주차현황 API**(한국체육산업개발(주), 동2/남2/북2 합계)를
GitHub Actions로 **5분마다** 호출해 기록한다. 원 API는 현재 값만 주고 이력을 제공하지 않으므로,
분석용 시계열을 직접 쌓기 위한 저장소다.

- 2026 한국체육산업개발(주) 공공데이터 활용 경진대회 출품 프로젝트의 데이터 수집 모듈
- 운영비 0원 (공개 저장소의 GitHub Actions는 무료)

## 데이터 위치
수집 결과는 **`parking-data` 브랜치**의 `data/parking/YYYY-MM-DD.csv`(KST 날짜별)에 쌓인다.
main 브랜치에는 코드만 둔다(커밋 기록이 데이터로 뒤덮이지 않게).

| 컬럼 | 의미 |
|---|---|
| fetched_at_utc / fetched_at_kst | **실제** 호출 시각 (예약 시각과 다를 수 있음) |
| parking_sum | 동2·남2·북2 주차대수 합계 |
| http_status, latency_ms, attempt | 응답 코드, 응답 시간, 몇 번째 시도에서 받았는지 |
| error | 실패 사유 (성공 시 빈칸) — 실패도 행으로 남겨 결측을 드러냄 |
| raw | 원 응답 앞 300자 (형식 변경 감지용) |

## 분석할 때 주의
- GitHub 예약 실행은 몇 분 밀리거나 건너뛸 수 있다 → 간격이 일정하다고 가정하지 말고 `fetched_at_kst` 기준으로 리샘플링한다.
- 기관이 밝힌 대로 장기주차 출차 누락이 있어 `parking_sum`은 실제보다 크게 누적될 수 있다.

## 설정 (최초 1회)
1. Settings → Secrets and variables → Actions → `PARKING_API_KEY` 등록 (기관 홈페이지 공공데이터 개방목록에 공개된 키)
2. `parking-data` 브랜치 생성
3. Actions 탭 → collect-parking → Run workflow 로 수동 테스트

## 로컬 실행
```bash
PARKING_API_KEY=... OUT_DIR=data/parking python3 scripts/collect_parking.py
```

## 데이터 출처
한국체육산업개발(주) 올림픽공원 실시간 주차현황 API (https://www.ksponco.or.kr/pubData/64?mid=a10106020000)
