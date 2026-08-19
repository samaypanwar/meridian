import type { ReactNode } from "react";

const TOKEN_RE = /(\*\*[^*]+\*\*|`[^`]+`)/g;

export function renderInlineMarkdown(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = TOKEN_RE.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith("**")) {
      parts.push(<strong key={`${match.index}-b`}>{token.slice(2, -2)}</strong>);
    } else {
      parts.push(
        <code key={`${match.index}-c`} className="inline-code">
          {token.slice(1, -1)}
        </code>,
      );
    }
    lastIndex = TOKEN_RE.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
}

export default function InlineMarkdown({ text }: { text: string }) {
  return <>{renderInlineMarkdown(text)}</>;
}
