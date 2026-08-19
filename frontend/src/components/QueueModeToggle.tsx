import type { QueueMode } from "../lib/queueMode";

export default function QueueModeToggle({
  mode,
  onChange,
}: {
  mode: QueueMode;
  onChange: (mode: QueueMode) => void;
}) {
  return (
    <div className="queue-controls__group" role="group" aria-label="Queue ranking mode">
      <button
        type="button"
        className={`queue-controls__btn${mode === "goals" ? " queue-controls__btn--active" : ""}`}
        onClick={() => onChange("goals")}
        title="Rank by goal alignment (exploit)"
      >
        Goals
      </button>
      <button
        type="button"
        className={`queue-controls__btn queue-controls__btn--curiosity${mode === "curiosity" ? " queue-controls__btn--active" : ""
          }`}
        onClick={() => onChange("curiosity")}
        title="Rank by intrinsic curiosity (explore)"
      >
        Curiosity
      </button>
    </div>
  );
}
