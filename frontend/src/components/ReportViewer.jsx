export default function ReportViewer({ report, path }) {
  if (!report) return null;
  return (
    <section className="panel report-panel">
      <h2>Research Report</h2>
      <pre className="report-content">{report}</pre>
      {path && <p className="report-path">Saved to: {path}</p>}
    </section>
  );
}
