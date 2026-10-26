import sqlite3
import os
import re
import csv
import webbrowser
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "job_tracker.db")

def resolve_document_file(output_dir: str, company: str, doc_type: str = "CV") -> Optional[str]:
    """
    Resuelve el nombre del archivo PDF de CV o Cover Letter en output_dir,
    incluso si el nombre de empresa en la BD incluye detalles como 'Porvenir (Grupo Aval)' o 'Experis Colombia'.
    """
    if not os.path.exists(output_dir):
        return None
    files = set(os.listdir(output_dir))
    safe_comp = "".join(c for c in company if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    exact = f"CV_Santiago_Ochoa_{safe_comp}.pdf" if doc_type == "CV" else f"Cover_Letter_{safe_comp}.pdf"
    if exact in files:
        return exact

    # Búsqueda por primera palabra clave (ej. Porvenir, Experis)
    first_word = re.split(r'[\s\(\)_-]+', company.strip())[0]
    candidate = f"CV_Santiago_Ochoa_{first_word}.pdf" if doc_type == "CV" else f"Cover_Letter_{first_word}.pdf"
    if candidate in files:
        return candidate

    return None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL,
        position TEXT NOT NULL,
        track TEXT NOT NULL,
        fit_score INTEGER NOT NULL,
        url TEXT,
        status TEXT DEFAULT 'PENDING_REVIEW', -- 'PENDING_REVIEW', 'APPLIED', 'INTERVIEW', 'REJECTED', 'OFFER'
        date_added TEXT,
        notes TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_application(company: str, position: str, track: str, fit_score: int, url: str = "", notes: str = "") -> int:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("""
    INSERT INTO applications (company, position, track, fit_score, url, status, date_added, notes)
    VALUES (?, ?, ?, ?, ?, 'PENDING_REVIEW', ?, ?)
    """, (company, position, track, fit_score, url, today, notes))
    app_id = cur.lastrowid
    conn.commit()
    conn.close()
    return app_id

def list_applications(status: Optional[str] = None) -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM applications WHERE status = ? ORDER BY id DESC", (status,))
    else:
        cur.execute("SELECT * FROM applications ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def update_status(app_id: int, new_status: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE applications SET status = ? WHERE id = ?", (new_status, app_id))
    conn.commit()
    conn.close()

def export_dashboard() -> str:
    """
    Exporta la base de datos a un Dashboard HTML interactivo y a CSV,
    y lo abre automáticamente en el navegador web de Windows.
    """
    apps = list_applications()
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    html_path = os.path.join(output_dir, "dashboard_seguimiento.html")
    csv_path = os.path.join(output_dir, "seguimiento_postulaciones.csv")

    # 1. Exportar a CSV para Excel
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Empresa", "Cargo", "Track", "Fit Score (%)", "Estado", "Fecha", "URL Oferta", "Notas"])
        for a in apps:
            writer.writerow([
                a["id"], a["company"], a["position"], a["track"],
                a["fit_score"], a["status"], a["date_added"],
                a.get("url", ""), a.get("notes", "")
            ])

    # 2. Generar Dashboard HTML profesional
    total_apps = len(apps)
    avg_fit = round(sum(a["fit_score"] for a in apps) / total_apps, 1) if total_apps > 0 else 0
    pending = sum(1 for a in apps if a["status"] == "PENDING_REVIEW")
    interviews = sum(1 for a in apps if a["status"] == "INTERVIEW")

    rows_html = []
    for a in apps:
        score = a["fit_score"]
        if score >= 85:
            badge_score = f'<span class="badge badge-success">{score}% MATCH</span>'
        elif score >= 75:
            badge_score = f'<span class="badge badge-primary">{score}% MATCH</span>'
        else:
            badge_score = f'<span class="badge badge-secondary">{score}%</span>'

        status = a["status"]
        status_classes = {
            "PENDING_REVIEW": "badge-warning",
            "APPLIED": "badge-info",
            "INTERVIEW": "badge-success",
            "REJECTED": "badge-danger",
            "OFFER": "badge-success"
        }
        status_badge = f'<span class="badge {status_classes.get(status, "badge-secondary")}">{status}</span>'

        cv_file = resolve_document_file(output_dir, a["company"], "CV")
        cl_file = resolve_document_file(output_dir, a["company"], "Cover_Letter")
        
        cv_button = f'<a href="{cv_file}" target="_blank" class="btn btn-sm btn-outline">📄 Ver CV</a>' if cv_file else '<span class="text-muted">—</span>'
        cl_button = f'<a href="{cl_file}" target="_blank" class="btn btn-sm btn-outline">✉️ Carta</a>' if cl_file else ''
        apply_button = f'<a href="{a["url"]}" target="_blank" class="btn btn-sm btn-primary">🌐 Oferta ↗</a>' if a.get("url") else '<span class="text-muted">—</span>'

        rows_html.append(f"""
        <tr>
            <td><strong>#{a['id']}</strong></td>
            <td><strong>{a['company']}</strong></td>
            <td>{a['position']}</td>
            <td><span class="badge badge-track">{a['track']}</span></td>
            <td>{badge_score}</td>
            <td>{status_badge}</td>
            <td class="text-muted">{a.get('date_added', '')[:10]}</td>
            <td style="white-space: nowrap;">{apply_button} {cv_button} {cl_button}</td>
        </tr>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Tracker Dashboard - Santiago Ochoa Quesada</title>
    <style>
        :root {{
            --bg: #0F172A;
            --card-bg: #1E293B;
            --text: #F8FAFC;
            --text-muted: #94A3B8;
            --primary: #38BDF8;
            --primary-hover: #0EA5E9;
            --success: #34D399;
            --warning: #FBBF24;
            --danger: #F87171;
            --border: #334155;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            padding: 2rem;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1.5rem;
        }}
        .header h1 {{ font-size: 1.8rem; font-weight: 700; color: #FFF; }}
        .header p {{ color: var(--text-muted); font-size: 0.95rem; margin-top: 0.2rem; }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.2rem;
            margin-bottom: 2rem;
        }}
        .metric-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
        }}
        .metric-card .title {{ font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }}
        .metric-card .val {{ font-size: 2rem; font-weight: 700; margin-top: 0.3rem; color: #FFF; }}
        .table-container {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.92rem;
        }}
        th {{
            background: #182234;
            padding: 1rem 1.2rem;
            color: var(--text-muted);
            font-weight: 600;
            border-bottom: 1px solid var(--border);
        }}
        td {{
            padding: 1rem 1.2rem;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
        }}
        tr:hover td {{ background: rgba(255, 255, 255, 0.02); }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-success {{ background: rgba(52, 211, 153, 0.15); color: #34D399; border: 1px solid rgba(52, 211, 153, 0.3); }}
        .badge-primary {{ background: rgba(56, 189, 248, 0.15); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.3); }}
        .badge-warning {{ background: rgba(251, 191, 36, 0.15); color: #FBBF24; border: 1px solid rgba(251, 191, 36, 0.3); }}
        .badge-info {{ background: rgba(96, 165, 250, 0.15); color: #60A5FA; border: 1px solid rgba(96, 165, 250, 0.3); }}
        .badge-track {{ background: rgba(148, 163, 184, 0.1); color: #CBD5E1; border: 1px solid rgba(148, 163, 184, 0.2); }}
        .btn {{
            display: inline-block;
            text-decoration: none;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s ease;
            margin-right: 0.3rem;
        }}
        .btn-primary {{ background: var(--primary); color: #0F172A; }}
        .btn-primary:hover {{ background: var(--primary-hover); }}
        .btn-outline {{ border: 1px solid var(--border); color: var(--text); background: transparent; }}
        .btn-outline:hover {{ background: rgba(255, 255, 255, 0.05); border-color: var(--text-muted); }}
        .text-muted {{ color: var(--text-muted); }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>Dashboard de Postulaciones Laborales</h1>
            <p>Santiago Alejandro Ochoa Quesada &bull; Ingeniero de Proyectos | AI, Cloud & Hardware Systems</p>
        </div>
        <div>
            <span class="badge badge-primary">SQLite: job_tracker.db</span>
        </div>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="title">Total Vacantes Preparadas</div>
            <div class="val">{total_apps}</div>
        </div>
        <div class="metric-card">
            <div class="title">Afinidad Promedio</div>
            <div class="val" style="color: var(--success);">{avg_fit}%</div>
        </div>
        <div class="metric-card">
            <div class="title">Listas para Aplicar</div>
            <div class="val" style="color: var(--warning);">{pending}</div>
        </div>
        <div class="metric-card">
            <div class="title">En Proceso / Entrevistas</div>
            <div class="val">{interviews}</div>
        </div>
    </div>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Empresa</th>
                    <th>Cargo</th>
                    <th>Track</th>
                    <th>Fit Score</th>
                    <th>Estado</th>
                    <th>Fecha</th>
                    <th style="min-width: 270px;">Documentos & Acciones</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_path

if __name__ == "__main__":
    init_db()
    h = export_dashboard()
    print("Dashboard generado en:", h)
