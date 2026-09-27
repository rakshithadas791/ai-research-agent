export default function AgentSteps({ plan, currentStep, completedSteps }) {
  if (!plan.length) return null;
  return (
    <section className="panel">
      <h2>Execution</h2>
      <ul className="step-list">
        {plan.map((step, i) => {
          const num = i + 1;
          const status = completedSteps.includes(num)
            ? "done"
            : num === currentStep
            ? "active"
            : "pending";
          const icon = status === "done" ? "✓" : status === "active" ? "●" : "○";
          return (
            <li key={i} className={`step step-${status}`}>
              <span className="step-icon">{icon}</span> {step}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
