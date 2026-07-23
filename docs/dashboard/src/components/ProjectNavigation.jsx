const SECTIONS = [
  ["overview", "Overview"],
  ["geography", "Coverage"],
  ["priorities", "Priority tiers"],
  ["operations", "Operations"],
  ["candidate-queue", "Candidate queue"],
  ["verification", "Verification"],
  ["state-yield", "State yield"],
  ["reports", "Reports"],
  ["methodology", "Definitions"],
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
