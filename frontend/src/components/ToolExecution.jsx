export default function ToolExecution({ logs }) {
  if (!logs.length) return null;
  return (
    <section className="panel">
      <h2>Tool Activity</h2>
      <div className="tool-log">
        {logs.map((log, i) => (
          <div key={i} className={`tool-log-line tool-log-${log.type}`}>
            {log.type === "tool_call" && `🔧 ${log.data.tool}(${JSON.stringify(log.data.input)})`}
            {log.type === "observation" && `↳ ${log.data.result}`}
            {log.type === "thought" && `💭 ${log.data.text}`}
          </div>
        ))}
      </div>
    </section>
  );
}
