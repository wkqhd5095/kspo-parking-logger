"""올림픽공원 실시간 주차현황 API를 한 번 호출해 CSV에 한 줄 추가한다.

- API: 한국체육산업개발(주) 실시간 주차현황 (동2/남2/북2 합계)
- 키: 환경변수 PARKING_API_KEY (GitHub Secrets로 주입, 코드에 적지 않음)
- 저장: data/parking/YYYY-MM-DD.csv (KST 날짜 기준, 하루 1파일)
- 실패해도 오류 행을 남긴다 → 결측 구간이 데이터에 그대로 드러나게 하기 위함
- 표준 라이브러리만 사용 (설치할 패키지 없음)
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API_URL = "https://www.ksponco.or.kr/online/main/parkingorsApi.do"
KST = timezone(timedelta(hours=9))
FIELDS = ["fetched_at_utc", "fetched_at_kst", "parking_sum", "http_status",
          "latency_ms", "attempt", "error", "raw"]
OUT_DIR = Path(os.environ.get("OUT_DIR", "data/parking"))
RETRIES = 3


def fetch(api_key: str) -> dict:
    """API를 호출해 결과 dict를 돌려준다. 실패 시 error 필드를 채운다."""
    url = f"{API_URL}?apiKey={api_key}"
    last = {}
    for attempt in range(1, RETRIES + 1):
        t0 = time.monotonic()
        row = {"attempt": attempt, "parking_sum": "", "http_status": "",
               "error": "", "raw": ""}
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "kspo-parking-logger/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode("utf-8", errors="replace").strip()
                row["http_status"] = resp.status
            row["raw"] = body[:300]
            data = json.loads(body)
            # 정상 응답 형태: [{"parking_sum": 1865}]
            value = data[0]["parking_sum"] if isinstance(data, list) else data["parking_sum"]
            row["parking_sum"] = int(value)
            row["latency_ms"] = round((time.monotonic() - t0) * 1000)
            return row
        except urllib.error.HTTPError as e:
            row["http_status"] = e.code
            row["error"] = f"HTTPError {e.code}"
        except Exception as e:  # 네트워크 오류, JSON 형식 변경 등
            row["error"] = f"{type(e).__name__}: {e}"[:200]
        row["latency_ms"] = round((time.monotonic() - t0) * 1000)
        last = row
        if attempt < RETRIES:
            time.sleep(5 * attempt)
    return last


def append(row: dict, now_utc: datetime) -> Path:
    now_kst = now_utc.astimezone(KST)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{now_kst:%Y-%m-%d}.csv"
    new = not path.exists()
    row = {"fetched_at_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "fetched_at_kst": now_kst.strftime("%Y-%m-%d %H:%M:%S"), **row}
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in FIELDS})
    return path


def main() -> int:
    api_key = os.environ.get("PARKING_API_KEY")
    if not api_key:
        print("::error::환경변수 PARKING_API_KEY가 없습니다 (GitHub Secrets 확인)")
        return 1
    now_utc = datetime.now(timezone.utc)
    row = fetch(api_key)
    path = append(row, now_utc)
    if row["error"]:
        print(f"::warning::수집 실패 → {row['error']} (오류 행 기록: {path})")
    else:
        print(f"OK parking_sum={row['parking_sum']} → {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
