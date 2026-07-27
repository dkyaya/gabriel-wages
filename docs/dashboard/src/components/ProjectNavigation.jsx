const SECTIONS = [
  ["overview", "Overview"],
  ["project-phase", "Project phase"],
  ["geography", "Historical coverage"],
  ["priorities", "Historical priority tiers"],
  ["operations", "Historical operations"],
  ["candidate-queue", "Historical candidate queue"],
  ["verification", "Verification"],
  ["state-yield", "Historical state yield"],
  ["reports", "Reports"],
  ["methodology", "Definitions"],
  ["descriptive-analysis", "Analysis plan"],
  ["next-steps", "Next steps"],
];

export function ProjectNavigation({ open, onToggle, onNavigate }) {
  return (
    <nav className={`project-nav no-print ${open ? "project-nav-open" : ""}`} aria-label="Project hub sections">
      <div className="project-nav-inner">
        <button
          type="button"
          className="project-nav-toggle"
          aria-expanded={open}
          aria-controls="project-nav-links"
          onClick={onToggle}
        >
          <span>Explore project status</span>
          <span aria-hidden="true">{open ? "Close" : "Menu"}</span>
        </button>
        <div id="project-nav-links" className="project-nav-links">
          {SECTIONS.map(([id, label]) => (
            <button type="button" key={id} onClick={() => onNavigate(id)}>
              {label}
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}
