import { Link } from "react-router-dom";
import { defaultIndicatorTargets } from "../lib/goalsParse";

export default function CycleStrip({
  captures = 0,
  passRate = 0,
}: {
  captures?: number;
  passRate?: number;
}) {
  const targets = defaultIndicatorTargets();
  return (
    <Link to="/goals" className="cycle-strip">
      <span className="cycle-strip__label">Cycle progress</span>
      <span className="cycle-strip__stat">
        {captures}/{targets.capturesPerCycle} captures
      </span>
      <span className="cycle-strip__dot" aria-hidden>
        ·
      </span>
      <span className="cycle-strip__stat">{Math.round(passRate * 100)}% review pass</span>
    </Link>
  );
}
