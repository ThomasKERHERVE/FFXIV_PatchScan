import "./ContentCard.css";

export default function ContentCard({ contents }) {
  return (
    <div className="card card-wide" style={{ "--accent": "#c8a96e" }}>
      <div className="card-head">
        <span className="card-icon">✨</span>
        <span className="card-title">New Content</span>
        <span className="card-badge">{contents.length}</span>
      </div>

      <div className="card-body content-grid">
        {contents.length === 0 ? (
          <p className="card-empty">No major new content in this patch.</p>
        ) : (
          contents.map((c, i) => (
            <div className="content-entry" key={i}>
              <div className="content-name">✦ {c.name}</div>

              {c.description && (
                <div className="content-desc">{c.description}</div>
              )}

              {c.location && (
                <div className="content-location">
                  📍 {c.location}
                </div>
              )}

              {c.npc_location && (
                <div className="content-npc">
                  👤 {c.npc_location}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}