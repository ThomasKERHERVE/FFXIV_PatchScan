import "./Header.css";

export default function Header() {
  return (
    <header className="header">
      <div className="header-ornament">
        <span className="diamond" />
        <span className="line" />
        <span className="diamond sm" />
      </div>
      <h1 className="header-title">
        FFXIV <span className="accent">PATCH</span>SCAN
      </h1>
    </header>
  );
}