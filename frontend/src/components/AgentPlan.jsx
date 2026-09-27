export default function AgentPlan({ plan }) {
  if (!plan.length) return null;
  return (
    <section className="panel">
      <h2>Plan</h2>
      <ol>
        {plan.map((step, i) => (
          <li key={i}>{step}</li>
        ))}
      </ol>
    </section>
  );
}
