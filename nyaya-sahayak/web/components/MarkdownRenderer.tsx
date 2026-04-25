"use client";

/**
 * Lightweight markdown renderer for LLM responses.
 * Handles: **bold**, *italic*, ## headings, numbered/bullet lists, `code`, tables, and BNS section references.
 * No external dependency (react-markdown) — zero bundle cost.
 */

interface MarkdownRendererProps {
  text: string;
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function highlightBNSSections(html: string): string {
  // Highlight "BNS Section 123" or "Section 123" references
  return html.replace(
    /\b(BNS\s+)?Section\s+(\d{1,4}[A-Z]?)\b/gi,
    '<span class="bns-ref">$1Section $2</span>'
  );
}

function highlightIPCSections(html: string): string {
  // Highlight "IPC Section 123" or "IPC 123" references
  return html.replace(
    /\bIPC\s+(?:Section\s+)?(\d{1,4}[A-Z]?)\b/gi,
    '<span class="ipc-ref">IPC $1</span>'
  );
}

function parseInline(text: string): string {
  let html = escapeHtml(text);
  // Bold: **text**
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // Italic: *text*
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  // Code: `text`
  html = html.replace(/`(.+?)`/g, '<code class="inline-code">$1</code>');
  // Highlight legal references
  html = highlightBNSSections(html);
  html = highlightIPCSections(html);
  return html;
}

function renderMarkdownToHtml(text: string): string {
  const lines = text.split("\n");
  const out: string[] = [];
  let inList = false;
  let inTable = false;
  let listType: "ol" | "ul" = "ul";

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Empty line
    if (!trimmed) {
      if (inList) {
        out.push(listType === "ol" ? "</ol>" : "</ul>");
        inList = false;
      }
      if (inTable) {
        out.push("</tbody></table>");
        inTable = false;
      }
      out.push("<br/>");
      continue;
    }

    // Headings
    if (trimmed.startsWith("### ")) {
      if (inList) { out.push(listType === "ol" ? "</ol>" : "</ul>"); inList = false; }
      out.push(`<h4 class="md-h4">${parseInline(trimmed.slice(4))}</h4>`);
      continue;
    }
    if (trimmed.startsWith("## ")) {
      if (inList) { out.push(listType === "ol" ? "</ol>" : "</ul>"); inList = false; }
      out.push(`<h3 class="md-h3">${parseInline(trimmed.slice(3))}</h3>`);
      continue;
    }
    if (trimmed.startsWith("# ")) {
      if (inList) { out.push(listType === "ol" ? "</ol>" : "</ul>"); inList = false; }
      out.push(`<h2 class="md-h2">${parseInline(trimmed.slice(2))}</h2>`);
      continue;
    }

    // Horizontal rule
    if (/^[-*_]{3,}$/.test(trimmed)) {
      out.push('<hr class="md-hr"/>');
      continue;
    }

    // Table row (| col | col |)
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      const cells = trimmed.split("|").filter(c => c.trim()).map(c => c.trim());
      // Check if separator row
      if (cells.every(c => /^[-:]+$/.test(c))) {
        continue; // skip separator
      }
      if (!inTable) {
        out.push('<table class="md-table"><tbody>');
        inTable = true;
        // First row as header
        out.push("<tr>" + cells.map(c => `<th>${parseInline(c)}</th>`).join("") + "</tr>");
        continue;
      }
      out.push("<tr>" + cells.map(c => `<td>${parseInline(c)}</td>`).join("") + "</tr>");
      continue;
    } else if (inTable) {
      out.push("</tbody></table>");
      inTable = false;
    }

    // Numbered list: 1. or 1)
    const numMatch = trimmed.match(/^(\d+)[.)]\s+(.*)$/);
    if (numMatch) {
      if (!inList || listType !== "ol") {
        if (inList) out.push("</ul>");
        out.push('<ol class="md-ol">');
        inList = true;
        listType = "ol";
      }
      out.push(`<li>${parseInline(numMatch[2])}</li>`);
      continue;
    }

    // Bullet list: - or •
    const bulletMatch = trimmed.match(/^[-•*]\s+(.*)$/);
    if (bulletMatch) {
      if (!inList || listType !== "ul") {
        if (inList) out.push("</ol>");
        out.push('<ul class="md-ul">');
        inList = true;
        listType = "ul";
      }
      out.push(`<li>${parseInline(bulletMatch[1])}</li>`);
      continue;
    }

    // Close list if we have a non-list line
    if (inList) {
      out.push(listType === "ol" ? "</ol>" : "</ul>");
      inList = false;
    }

    // Regular paragraph
    out.push(`<p class="md-p">${parseInline(trimmed)}</p>`);
  }

  // Close any open list
  if (inList) out.push(listType === "ol" ? "</ol>" : "</ul>");
  if (inTable) out.push("</tbody></table>");

  return out.join("\n");
}

export default function MarkdownRenderer({ text }: MarkdownRendererProps) {
  const html = renderMarkdownToHtml(text);
  return (
    <div
      className="markdown-content"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
