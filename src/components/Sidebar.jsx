import "./Sidebar.css";

export default function Sidebar({ patches, selected, onSelect }) {

  const sorted = [...patches].sort((a, b) => {
    const va = getPatchVersion(a.title);
    const vb = getPatchVersion(b.title);

    if (va.major !== vb.major) {
      return vb.major - va.major;
    }

    return vb.minor - va.minor;
  });

  return (
    <aside className="sidebar">
      <div className="sidebar-title">Patch History</div>

      <ul className="patch-list">
        {sorted.length === 0 && (
          <li className="patch-empty">No patches yet.</li>
        )}

        {sorted.map((patch) => (
          <li
            key={patch.file}
            className={`patch-item ${
              selected?.file === patch.file ? "active" : ""
            }`}
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