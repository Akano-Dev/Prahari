"""Incident report generation.

Renders a :class:`RiskAssessment` (+ its call) to a self-contained HTML report
always, and to a PDF when ``reportlab`` is installed (optional). The report
carries transcript, timeline, risk score, scam type, evidence, highlighted
sentences, recommended action and a timestamp — the spec's required contents.
"""
from __future__ import annotations

import html
from datetime import datetime, timezone

from scamshield_ai import RiskAssessment

from ..domain.models import Call


def _highlight(text: str, snippets: list[str]) -> str:
    out = html.escape(text)
    for snip in sorted(set(snippets), key=len, reverse=True):
        if not snip:
            continue
        esc = html.escape(snip)
        out = out.replace(esc, f"<mark>{esc}</mark>")
    return out


def render_html(assessment: RiskAssessment, call: Call) -> str:
    a = assessment
    evidence = [e.text for s in a.signals for e in s.evidence]
    rows_signals = "".join(
        f"<tr><td>{html.escape(s.label)}</td><td>{s.weight}</td>"
        f"<td>{html.escape(', '.join(e.text for e in s.evidence))}</td></tr>"
        for s in a.signals)
    timeline = "".join(
        f"<li><b>#{t.index}</b> [{html.escape(t.kind)}] {html.escape(t.label)}"
        + (f" — {html.escape(t.detail)}" if t.detail else "") + "</li>"
        for t in a.timeline)
    transcript = "".join(
        f"<p class='utt'>{_highlight(u, evidence)}</p>" for u in call.utterances)
    scam_type = a.top_scam_type.label if a.top_scam_type else "—"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>ScamShield Incident Report — {html.escape(call.id)}</title>
<style>
 body{{font-family:system-ui,Segoe UI,Arial;margin:32px;color:#111}}
 h1{{margin:0}} .muted{{color:#666}} mark{{background:#ffe08a}}
 .score{{font-size:42px;font-weight:800;color:{'#c0392b' if a.is_scam else '#2e7d32'}}}
 table{{border-collapse:collapse;width:100%;margin:8px 0}}
 td,th{{border:1px solid #ddd;padding:6px 8px;text-align:left;font-size:13px}}
 .utt{{background:#f6f7fb;padding:8px 10px;border-radius:6px;margin:6px 0}}
 .box{{border:1px solid #eee;border-radius:8px;padding:14px 16px;margin:14px 0}}
</style></head><body>
<h1>🛡 ScamShield Incident Report</h1>
<p class="muted">Call {html.escape(call.id)} · caller {html.escape(call.caller_number)} · generated {ts}</p>
<div class="box"><div class="score">{a.risk_score}/100 — {html.escape(a.band.value)}</div>
<p><b>Verdict:</b> {'LIKELY SCAM' if a.is_scam else 'No strong scam indicators'} ·
<b>Detected scam type:</b> {html.escape(scam_type)} · <b>Confidence:</b> {a.confidence}</p>
<p><b>Reasoning:</b> {html.escape(a.reasoning)}</p>
<p><b>Recommended action:</b> {html.escape(a.recommendation)}</p></div>
<div class="box"><h3>Evidence — fired signals</h3>
<table><tr><th>Signal</th><th>Severity</th><th>Matched text</th></tr>{rows_signals}</table></div>
<div class="box"><h3>Transcript (highlighted)</h3>{transcript or '<p class=muted>No transcript.</p>'}</div>
<div class="box"><h3>Timeline</h3><ul>{timeline}</ul></div>
</body></html>"""


def render_pdf(assessment: RiskAssessment, call: Call) -> tuple[bytes, str]:
    """Return (bytes, content_type). PDF if reportlab is present, else HTML."""
    html_doc = render_html(assessment, call)
    try:
        from reportlab.lib.pagesizes import A4  # lazy optional dep
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
        import io
    except ImportError:
        return html_doc.encode("utf-8"), "text/html; charset=utf-8"

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 2 * cm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, y, "ScamShield Incident Report")
    y -= 1 * cm
    c.setFont("Helvetica", 11)
    for line in [
        f"Call {call.id} · caller {call.caller_number}",
        f"Risk {assessment.risk_score}/100 — {assessment.band.value}",
        f"Scam type: {assessment.top_scam_type.label if assessment.top_scam_type else '—'}",
        f"Recommendation: {assessment.recommendation}",
        "", "Reasoning:", assessment.reasoning,
        "", "Transcript:",
        *call.utterances,
    ]:
        for chunk in (line[i:i + 95] for i in range(0, max(len(line), 1), 95)):
            c.drawString(2 * cm, y, chunk)
            y -= 0.6 * cm
            if y < 2 * cm:
                c.showPage(); y = height - 2 * cm; c.setFont("Helvetica", 11)
    c.showPage(); c.save()
    return buf.getvalue(), "application/pdf"
