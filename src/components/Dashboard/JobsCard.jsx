import "./JobsCard.css";

export default function JobsCard({ title, icon, jobs, accent }) {
  return (
    <div className="card" style={{ "--accent": accent }}>
      <div className="card-head">
        <span className="card-icon">{icon}</span>
        <span className="card-title">{title}</span>
        <span className="card-badge">{jobs.length}</span>
      </div>
      <div className="card-body">
        {jobs.length === 0 ? (
          <p className="card-empty">No adjustments in this patch.</p>
        ) : (
          jobs.map((j, i) => (
            <div className="job-entry" key={i}>
              <div className="job-name">{j.job}</div>
              <ul className="job-changes">
                {j.changes.map((c, ci) => <li key={ci}>{c}</li>)}
              </ul>
            </div>
          ))
        )}
      </div>
    </div>
  );
}