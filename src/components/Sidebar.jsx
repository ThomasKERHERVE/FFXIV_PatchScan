import "./Sidebar.css";

export default function Sidebar({ patches, selected, onSelect }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-title">Patch History</div>
      <ul className="patch-list">
        {patches.length === 0 && (
          <li className="patch-empty">No patches yet.</li>
        )}
        {patches.map((patch) => (
          <li
            key={patch.file}
            className={`patch-item ${selected?.file === patch.file ? "active" : ""}`}
            onClick={() => onSelect(patch)}
          >
            <span className="patch-name">{patch.title}</span>
            <span className="patch-date">{patch.date}</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}