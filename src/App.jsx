import { useState, useEffect } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import Dashboard from "./components/Dashboard/Dashboard";
import "./App.css";

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
        setPatchList(data);

        if (data.length > 0) {
          setSelectedPatch(data[0]);
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
      .catch(() => setPatchData(null))
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