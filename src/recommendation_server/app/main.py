from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from database.config import load_settings
from database.registry import DistrictRegistry
from database.client import GovAnimalApiClient
from database.service import SeoulAnimalSyncService
from database.storage import AnimalRepository

from .recommender import recommend_animals

app = FastAPI(title="Recommendation Server")

PROTOTYPE_HTML = """<!DOCTYPE html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Recommendation Prototype</title>
    <style>
      :root {
        --bg: #f6f1e8;
        --panel: #fffaf2;
        --line: #d7c8b3;
        --text: #2f2418;
        --muted: #7d6d5c;
        --accent: #a8522d;
        --accent-soft: #f0d9cb;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "Pretendard", "Noto Sans KR", sans-serif;
        color: var(--text);
        background:
          radial-gradient(circle at top left, #f8d8bc 0, transparent 28%),
          linear-gradient(180deg, #f7f1e6 0%, #f3ede3 100%);
      }
      .wrap {
        max-width: 1200px;
        margin: 0 auto;
        padding: 32px 20px 56px;
      }
      .hero {
        margin-bottom: 24px;
      }
      .hero h1 {
        margin: 0 0 8px;
        font-size: 36px;
        line-height: 1.1;
      }
      .hero p {
        margin: 0;
        color: var(--muted);
        font-size: 15px;
      }
      .grid {
        display: grid;
        grid-template-columns: 420px minmax(0, 1fr);
        gap: 20px;
      }
      .panel {
        background: rgba(255, 250, 242, 0.96);
        border: 1px solid var(--line);
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(85, 56, 24, 0.08);
      }
      .controls {
        padding: 20px;
      }
      .controls h2,
      .results h2 {
        margin: 0 0 12px;
        font-size: 18px;
      }
      .actions {
        display: flex;
        gap: 10px;
        margin-bottom: 14px;
      }
      button {
        border: 0;
        border-radius: 999px;
        padding: 12px 16px;
        font-size: 14px;
        font-weight: 700;
        cursor: pointer;
      }
      .primary {
        background: var(--accent);
        color: white;
      }
      .secondary {
        background: var(--accent-soft);
        color: var(--accent);
      }
      textarea {
        width: 100%;
        min-height: 420px;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 16px;
        font: 13px/1.5 "SFMono-Regular", Consolas, monospace;
        resize: vertical;
        background: #fffdf9;
        color: var(--text);
      }
      .hint, .status {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.5;
      }
      .status {
        min-height: 20px;
        margin-top: 12px;
      }
      .results {
        padding: 20px;
      }
      .results-head {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: baseline;
        margin-bottom: 14px;
      }
      .count {
        color: var(--accent);
        font-size: 14px;
        font-weight: 700;
      }
      .cards {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 14px;
      }
      .card {
        border: 1px solid var(--line);
        border-radius: 18px;
        overflow: hidden;
        background: #fffdf9;
      }
      .thumb {
        aspect-ratio: 4 / 3;
        background: linear-gradient(135deg, #ead7c1, #f9f2e6);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--muted);
        font-size: 13px;
      }
      .thumb img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
      }
      .body {
        padding: 14px;
      }
      .title {
        margin: 0 0 8px;
        font-size: 17px;
      }
      .score {
        display: inline-flex;
        background: var(--accent-soft);
        color: var(--accent);
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 12px;
        font-weight: 700;
        margin-bottom: 10px;
      }
      .meta {
        margin: 0;
        font-size: 13px;
        line-height: 1.7;
        color: var(--muted);
      }
      .raw {
        margin-top: 18px;
        border-top: 1px solid var(--line);
        padding-top: 18px;
      }
      pre {
        margin: 0;
        padding: 16px;
        border-radius: 16px;
        overflow: auto;
        background: #2c241d;
        color: #fef5ea;
        font-size: 12px;
        line-height: 1.5;
      }
      @media (max-width: 980px) {
        .grid { grid-template-columns: 1fr; }
        textarea { min-height: 280px; }
      }
    </style>
  </head>
  <body>
    <div class="wrap">
      <section class="hero">
        <h1>Animal Recommendation Prototype</h1>
        <p>요청 body를 바로 보내고, 추천 결과와 이미지 URL 응답을 한 화면에서 확인할 수 있습니다.</p>
      </section>
      <div class="grid">
        <section class="panel controls">
          <h2>Request Body</h2>
          <div class="actions">
            <button class="secondary" id="sync-btn" type="button">DB Sync</button>
            <button class="primary" id="recommend-btn" type="button">Run Recommend</button>
          </div>
          <textarea id="payload">{
  "preferredAnimal": "강아지",
  "preferredSize": "소형견",
  "preferredSpecies": "포메라니안",
  "preferredAgeGroup": "",
  "activityLevel": "",
  "sexCd": "",
  "neuterYn": "",
  "userPreference": {}
}</textarea>
          <p class="hint">빈 문자열이나 빠진 값은 필터를 건너뜁니다.</p>
          <p class="status" id="status">준비됨</p>
        </section>
        <section class="panel results">
          <div class="results-head">
            <h2>Response</h2>
            <span class="count" id="count-label">0 results</span>
          </div>
          <div class="cards" id="cards"></div>
          <div class="raw">
            <pre id="raw-json">{}</pre>
          </div>
        </section>
      </div>
    </div>
    <script>
      const payloadEl = document.getElementById("payload");
      const statusEl = document.getElementById("status");
      const countLabelEl = document.getElementById("count-label");
      const cardsEl = document.getElementById("cards");
      const rawJsonEl = document.getElementById("raw-json");

      document.getElementById("sync-btn").addEventListener("click", async () => {
        statusEl.textContent = "서울 전체 데이터를 동기화하는 중...";
        try {
          const response = await fetch("/sync", { method: "POST" });
          const data = await response.json();
          rawJsonEl.textContent = JSON.stringify(data, null, 2);
          statusEl.textContent = response.ok
            ? `동기화 완료: ${data.animalCount}건`
            : `동기화 실패: ${data.detail || response.status}`;
        } catch (error) {
          statusEl.textContent = `동기화 실패: ${error.message}`;
        }
      });

      document.getElementById("recommend-btn").addEventListener("click", async () => {
        let body;
        try {
          body = JSON.parse(payloadEl.value || "{}");
        } catch (error) {
          statusEl.textContent = `JSON 파싱 실패: ${error.message}`;
          return;
        }

        statusEl.textContent = "추천 요청 중...";
        cardsEl.innerHTML = "";
        countLabelEl.textContent = "loading...";

        try {
          const response = await fetch("/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          });
          const data = await response.json();
          rawJsonEl.textContent = JSON.stringify(data, null, 2);

          if (!response.ok) {
            countLabelEl.textContent = "error";
            statusEl.textContent = `요청 실패: ${data.detail || response.status}`;
            return;
          }

          const recommendations = data.recommendations || [];
          countLabelEl.textContent = `${recommendations.length} results`;
          statusEl.textContent = "추천 완료";
          cardsEl.innerHTML = recommendations.map(renderCard).join("");
        } catch (error) {
          countLabelEl.textContent = "error";
          statusEl.textContent = `요청 실패: ${error.message}`;
        }
      });

      function renderCard(item) {
        const imageUrl = [
          item.popfile1, item.popfile2, item.popfile3, item.popfile4,
          item.popfile5, item.popfile6, item.popfile7, item.popfile8
        ].find(Boolean);

        const thumb = imageUrl
          ? `<img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(item.kindNm || "animal")}" />`
          : `<span>이미지 없음</span>`;

        return `
          <article class="card">
            <div class="thumb">${thumb}</div>
            <div class="body">
              <div class="score">Score ${item.score ?? 0}</div>
              <h3 class="title">${escapeHtml(item.kindNm || "이름 없음")}</h3>
              <p class="meta">
                공고번호: ${escapeHtml(item.noticeNo || "-")}<br />
                보호소: ${escapeHtml(item.careNm || "-")}<br />
                종류: ${escapeHtml(item.upKindNm || "-")} / ${escapeHtml(item.Size || "-")}<br />
                나이대: ${escapeHtml(item.AgeGroup || "-")}<br />
                성별/중성화: ${escapeHtml(item.sexCd || "-")} / ${escapeHtml(item.neuterYn || "-")}<br />
                상태: ${escapeHtml(item.processState || "-")}<br />
                특징: ${escapeHtml(item.specialMark || "-")}
              </p>
            </div>
          </article>
        `;
      }

      function escapeHtml(value) {
        return String(value)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#39;");
      }
    </script>
  </body>
</html>
"""


class RecommendationRequest(BaseModel):
    preferredAnimal: Optional[str] = None
    preferredSize: Optional[str] = None
    preferredSpecies: Optional[str] = None
    preferredAgeGroup: Optional[str] = None
    sexCd: Optional[str] = None
    neuterYn: Optional[str] = None
    activityLevel: Optional[str] = None
    userPreference: Dict[str, bool] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    count: int
    recommendations: List[Dict[str, Any]]

class SyncResponse(BaseModel):
    databasePath: str
    districtCount: int
    animalCount: int
    summaries: List[Dict[str, Any]]


@app.get("/", response_class=HTMLResponse)
def prototype() -> str:
    return PROTOTYPE_HTML


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sync", response_model=SyncResponse)
def sync() -> SyncResponse:
    settings = load_settings()
    repository = AnimalRepository(settings.database_path)
    registry = DistrictRegistry.from_json(settings.district_registry_path)
    service = SeoulAnimalSyncService(
        GovAnimalApiClient(settings),
        registry,
        repository,
    )
    summaries = service.sync_all_seoul()
    return SyncResponse(
        databasePath=str(settings.database_path),
        districtCount=len(summaries),
        animalCount=repository.animal_count(),
        summaries=[asdict(summary) for summary in summaries],
    )


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    settings = load_settings()
    repository = AnimalRepository(settings.database_path)
    animals = repository.list_animals(process_state="보호중")
    if not animals:
        raise HTTPException(status_code=400, detail="Database is empty. Run POST /sync first.")

    recommendations = recommend_animals(
        animals=animals,
        preferred_animal=request.preferredAnimal,
        preferred_size=request.preferredSize,
        preferred_species=request.preferredSpecies,
        preferred_age_group=request.preferredAgeGroup,
        sex_cd=request.sexCd,
        neuter_yn=request.neuterYn,
        activity_level=request.activityLevel,
        user_preference=request.userPreference,
    )
    return RecommendationResponse(
        count=len(recommendations),
        recommendations=recommendations,
    )
