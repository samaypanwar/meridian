import { Link } from "react-router-dom";
import { displayTitle, type SourceDetail } from "../api";

export default function DuplicateSourceNotice({
  existing,
  onDismiss,
}: {
  existing: SourceDetail;
  onDismiss: () => void;
}) {
  return (
    <div className="duplicate-notice panel" role="status">
      <p className="duplicate-notice__message">
        This source is already in Meridian.
      </p>
      <p className="duplicate-notice__title">{displayTitle(existing)}</p>
      <div className="duplicate-notice__actions">
        <Link to={`/sources/${existing.source.id}`} className="btn btn--primary">
          View source
        </Link>
        <button type="button" className="btn" onClick={onDismiss}>
          Dismiss
        </button>
      </div>
    </div>
  );
}
