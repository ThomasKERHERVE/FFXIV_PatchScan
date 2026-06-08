import "./HousingCard.css";

export default function HousingCard({ items }) {
  return (
    <div className="card" style={{ "--accent": "#9b7ec8" }}>
      <div className="card-head">
        <span className="card-icon">🏠</span>
        <span className="card-title">Housing Items</span>
        <span className="card-badge">{items.length}</span>
      </div>
      <div className="card-body">
        {items.length === 0 ? (
          <p className="card-empty">No new housing items in this patch.</p>
        ) : (
          items.map((item, i) => (
            <div className="item-entry" key={i}>
              <div className="item-name">{item.name}</div>
              {item.description && <div className="item-desc">{item.description}</div>}
            </div>
          ))
        )}
      </div>
    </div>
  );
}