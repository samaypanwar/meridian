interface ReadingStep {
  section?: string;
  action?: string;
  why?: string;
}

export default function ReadingPlan({ steps }: { steps: unknown[] }) {
  const items = steps.filter(
    (s): s is ReadingStep => typeof s === "object" && s !== null,
  );

  if (items.length === 0) return null;

  return (
    <ol className="reading-plan">
      {items.map((step, index) => (
        <li key={`${step.section ?? index}-${step.action ?? index}`} className="reading-plan__item">
          <div className="reading-plan__header">
            <span className={`reading-plan__action reading-plan__action--${step.action ?? "read"}`}>
              {step.action ?? "read"}
            </span>
            <span className="reading-plan__section">{step.section ?? "Section"}</span>
          </div>
          {step.why && <p className="reading-plan__why">{step.why}</p>}
        </li>
      ))}
    </ol>
  );
}
