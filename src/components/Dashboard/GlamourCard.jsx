import "./GlamourCard.css";

export default function GlamourCard({ items }) {
  return (
    <div className="card" style={{ "--accent": "#c88a8a" }}>
      <div className="card-head">
        <span className="card-icon">👗</span>
        <span className="card-title">Glamour</span>
        <span className="card-badge">{items.length}</span>
      </div>
      <div className="card-body">
        {items.length === 0 ? (
          <p className="card-empty">No new glamour items in this patch.</p>
        ) : (
          items.map((item, i) => (
            <div className="glamour-entry" key={i}>
              <div className="glamour-name">{item.name}</div>
              {item.description && <div className="glamour-desc">{item.description}</div>}
            </div>
          ))
        )}
      </div>
    </div>
  );
}