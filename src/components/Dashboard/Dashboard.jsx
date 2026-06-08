import JobsCard from "./JobsCard";
import ContentCard from "./ContentCard";
import HousingCard from "./HousingCard";
import GlamourCard from "./GlamourCard";
import "./Dashboard.css";

export default function Dashboard({ data }) {
  return (
    <div className="dashboard">
      <div className="patch-meta">
        <div>
          <h2 className="patch-title">{data.patch_title || "Patch Notes"}</h2>
          {data.patch_date && <span className="patch-date">{data.patch_date}</span>}
        </div>
        {data.patch_url && (
          <a href={data.patch_url} target="_blank" rel="noreferrer" className="patch-link">
            → To the patch notes
          </a>
        )}
      </div>

      <div className="dashboard-grid">
        <JobsCard title="PvE Job Adjustments" icon="⚔️" jobs={data.jobs_pve || []} accent="#e8a0a0" />
        <JobsCard title="PvP Job Adjustments" icon="🛡️" jobs={data.jobs_pvp || []} accent="#a0b8e8" />
        <ContentCard contents={data.new_content || []} />
        <HousingCard items={data.housing || []} />
        <GlamourCard items={data.glamour || []} />
      </div>
    </div>
  );
}