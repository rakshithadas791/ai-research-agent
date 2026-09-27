import { useState } from "react";

export default function TaskInput({ onStart, disabled }) {
  const [goal, setGoal] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (goal.trim()) onStart(goal.trim());
  };

  return (
    <form className="task-input" onSubmit={handleSubmit}>
      <label htmlFor="goal">Research Topic</label>
      <input
        id="goal"
        type="text"
        placeholder="e.g. Applications of computer vision in agriculture"
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !goal.trim()}>
        {disabled ? "Researching…" : "Start Research"}
      </button>
    </form>
  );
}
