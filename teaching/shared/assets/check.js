document.querySelectorAll("[data-check]").forEach((node) => {
  const button = node.querySelector("button");
  const input = node.querySelector("input");
  const feedback = node.querySelector(".feedback");
  const answer = (node.dataset.answer || "").trim().toLowerCase();
  const alt = (node.dataset.alt || "").trim().toLowerCase();

  const grade = () => {
    const guess = input.value.trim().toLowerCase();
    const ok = guess === answer || (alt && guess === alt);
    feedback.className = `feedback ${ok ? "good" : "bad"}`;
    feedback.textContent = ok
      ? "Correct."
      : `Not quite. Expected: ${node.dataset.answer}.`;
  };

  button.addEventListener("click", grade);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      grade();
    }
  });
});
