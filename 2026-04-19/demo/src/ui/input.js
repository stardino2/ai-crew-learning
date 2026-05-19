import { generateLotto } from "../engine/lotto.js";
import { renderGames } from "./renderer.js";

export function bindControls({ drawBtn, countSel, output }) {
  drawBtn.addEventListener("click", () => {
    const count = parseInt(countSel.value, 10);
    const games = [];
    for (let i = 0; i < count; i++) {
      games.push(generateLotto());
    }
    renderGames(games, output);
  });
}
