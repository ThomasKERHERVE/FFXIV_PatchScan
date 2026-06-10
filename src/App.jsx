import { useState, useEffect } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import Dashboard from "./components/Dashboard/Dashboard";
import "./App.css";

// Gather the patch version number
function getPatchVersion(title) {
  const match = title.match(/Patch\s+(\d+)(?:\.(\d+))?/i);

  if (!match) {
    return { major: 0, minor: 0 };
  }

  return {
    major: parseInt(match[1], 10),
    minor: parseInt(match[2] || "0", 10),
  };
}

export default function App() {
  const [patchList, setPatchList] = useState([]);
  const [selectedPatch, setSelectedPatch] = useState(null);
  const [patchData, setPatchData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Load patch index on mount
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/index.json`)
      .then((res) => res.json())
      .then((data) => {
        const sorted = [...data].sort((a, b) => {
          const va = getPatchVersion(a.title);
          const vb = getPatchVersion(b.title);

          if (va.major !== vb.major) {
            return vb.major - va.major;
          }

          return vb.minor - va.minor;
        });

         console.log("TOP 20 PATCHES :");
          sorted.slice(0, 20).forEach((p) => {
          console.log(p.title);
          });


        setPatchList(sorted);

        if (sorted.length > 0) {
          setSelectedPatch(sorted[0]);
        }
      })
      .catch(() => setPatchList([]));
  }, []);

  // Load selected patch data
  useEffect(() => {
    if (!selectedPatch) return;

    setLoading(true);
    setPatchData(null);

    fetch(
      `${import.meta.env.BASE_URL}data/patches/${selectedPatch.file}`
    )
      .then((res) => res.json())
      .then((data) => setPatchData(data))
      .finally(() => setLoading(false));
  }, [selectedPatch]);

  return (
    <div className="app">
      <div className="bg-grid" />
      <div className="bg-glow" />

      <Header />

      <div className="layout">
        <Sidebar
          patches={patchList}
          selected={selectedPatch}
          onSelect={setSelectedPatch}
        />

        <main className="main">
          {loading && <div className="loading">Loading...</div>}

          {patchData && <Dashboard data={patchData} />}

          {!loading && !patchData && (
            <div className="placeholder">
              Select a patch to view its details.
            </div>
          )}
        </main>
      </div>
    </div>
  );
}