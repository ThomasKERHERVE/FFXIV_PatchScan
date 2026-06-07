import JobsCard from "./JobsCard";
import PnjCard from "./PnjCard";
import ContentCard from "./ContentCard";
import "./Dashboard.css";

export default function Dashboard({ data }) {
  return (
    <div className="dashboard">
      <div className="patch-meta">
        <h2 className="patch-title">{data.patch_title || "Patch Notes"}</h2>
        {data.patch_date && <span className="patch-date">{data.patch_date}</span>}
      </div>

      <div className="dashboard-grid">
        <JobsCard title="PvE Job Adjustments" icon="⚔️" jobs={data.jobs_pve || []} accent="#e8a0a0" />
        <JobsCard title="PvP Job Adjustments" icon="🛡️" jobs={data.jobs_pvp || []} accent="#a0b8e8" />
        <PnjCard pnjs={data.pnj_locations || []} />
        <ContentCard contents={data.new_content || []} />
      </div>
    </div>
  );
}