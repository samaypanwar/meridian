const STEPS = ["Reflect", "Draft", "Save"];

export default function StepIndicator({ active }: { active: 0 | 1 | 2 }) {
  return (
    <ol className="step-indicator">
      {STEPS.map((label, index) => (
        <li
          key={label}
          className={
            index === active
              ? "step-indicator__item step-indicator__item--active"
              : index < active
                ? "step-indicator__item step-indicator__item--done"
                : "step-indicator__item"
          }
        >
          {label}
        </li>
      ))}
    </ol>
  );
}
