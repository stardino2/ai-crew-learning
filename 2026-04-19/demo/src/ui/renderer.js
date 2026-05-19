const BALL_COLORS = [
  { max: 10, bg: "#fbc400", text: "#000" },
  { max: 20, bg: "#69c8f2", text: "#000" },
  { max: 30, bg: "#ff7272", text: "#fff" },
  { max: 40, bg: "#aaa", text: "#fff" },
  { max: 45, bg: "#b0d840", text: "#000" },
];

function ballColor(n) {
  return BALL_COLORS.find((c) => n <= c.max);
}

function makeBall(n) {
  const { bg, text } = ballColor(n);
  const span = document.createElement("span");
  span.className = "ball";
  span.textContent = n;
  span.style.cssText = `
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px; height: 44px;
    border-radius: 50%;
    background: ${bg};
    color: ${text};
    font-weight: 700;
    font-size: 15px;
    margin: 4px;
    box-shadow: 0 2px 6px rgba(0,0,0,.25);
  `;
  return span;
}

export function renderGames(numbers2d, container) {
  container.innerHTML = "";
  numbers2d.forEach((numbers, i) => {
    const row = document.createElement("div");
    row.className = "game-row";
    row.style.cssText = "display:flex; align-items:center; margin: 6px 0;";

    const label = document.createElement("span");
    label.textContent = `게임 ${i + 1}`;
    label.style.cssText =
      "min-width: 52px; font-size: 13px; color: #666; margin-right: 8px;";
    row.appendChild(label);

    numbers.forEach((n) => row.appendChild(makeBall(n)));
    container.appendChild(row);
  });
}
