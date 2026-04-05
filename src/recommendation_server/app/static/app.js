const payloadEl = document.getElementById("payload");
const statusEl = document.getElementById("status");
const cardsEl = document.getElementById("cards");
const rawEl = document.getElementById("raw");

document.getElementById("send").addEventListener("click", async () => {
  let body;

  try {
    body = JSON.parse(payloadEl.value || "{}");
  } catch (error) {
    statusEl.textContent = "JSON 파싱 실패: " + error.message;
    return;
  }

  statusEl.textContent = "요청 중...";
  cardsEl.innerHTML = "";

  try {
    const response = await fetch("/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    rawEl.textContent = JSON.stringify(data, null, 2);

    if (!response.ok) {
      statusEl.textContent = "요청 실패";
      return;
    }

    statusEl.textContent = `완료: ${data.count}건`;
    cardsEl.innerHTML = (data.recommendations || []).map(renderCard).join("");
  } catch (error) {
    statusEl.textContent = "요청 실패: " + error.message;
  }
});

function renderCard(item) {
  const imageUrl = [
    item.popfile1,
    item.popfile2,
    item.popfile3,
    item.popfile4,
    item.popfile5,
    item.popfile6,
    item.popfile7,
    item.popfile8,
  ].find(Boolean);

  const image = imageUrl
    ? `<img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(item.kindNm || "animal")}" />`
    : `<div class="empty">이미지 없음</div>`;

  return `
    <article class="card">
      ${image}
      <div class="meta">
        <div class="score">Score ${item.score ?? 0}</div>
        <div>${escapeHtml(item.kindNm || "-")}</div>
        <div>${escapeHtml(item.careNm || "-")}</div>
        <div>${escapeHtml(item.AgeGroup || "-")} / ${escapeHtml(item.Size || "-")}</div>
        <div>${escapeHtml(item.sexCd || "-")} / ${escapeHtml(item.neuterYn || "-")}</div>
        <div>${escapeHtml(item.specialMark || "-")}</div>
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
