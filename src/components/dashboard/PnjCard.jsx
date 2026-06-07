import "./PnjCard.css";

export default function PnjCard({ pnjs }) {
  return (
    <div className="card" style={{ "--accent": "#5ca878" }}>
      <div className="card-head">
        <span className="card-icon">📍</span>
        <span className="card-title">NPC Locations</span>
        <span className="card-badge">{pnjs.length}</span>
      </div>
      <div className="card-body">
        {pnjs.length === 0 ? (
          <p className="card-empty">No notable NPC locations in this patch.</p>
        ) : (
          pnjs.map((p, i) => (
            <div className="pnj-entry" key={i}>
              <span className="pnj-loc">{p.location}</span>
              <div className="pnj-info">
                <span className="pnj-name">{p.npc_name}</span>
                {p.role && <span className="pnj-role"> — {p.role}</span>}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}