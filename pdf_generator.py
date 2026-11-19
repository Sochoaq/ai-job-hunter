import os
import re
import json
import subprocess
import fitz  # PyMuPDF fallback
from typing import Dict, Any, List


def _load_pdf_candidate_config() -> Dict[str, Any]:
    """Load candidate template data from local config first, falling back to example config."""
    base_dir = os.path.dirname(__file__)
    for filename in ("candidate_config.local.json", "candidate_config.example.json"):
        cfg_path = os.path.join(base_dir, filename)
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
    return {
        "file_prefix": "Candidate",
        "candidate_header": {
            "name": "[YOUR_NAME]",
            "title": "AI Systems & MLOps Engineer",
            "email": "candidate@example.com",
            "phone": "+00 000 000 0000",
            "location": "City, Country",
            "linkedin": "linkedin.com/in/your-profile",
            "github": "github.com/your-username",
        },
        "default_summary_latex": "\\textbf{AI Systems \\& MLOps Engineer} specializing in multi-agent LLM orchestration, automated evaluation, and scalable Python/Docker systems.",
        "core_experience_bullets_latex": [
            "    \\item Architected multi-agent LLM evaluation and document synthesis pipelines with Pydantic structured schemas.",
            "    \\item Built containerized MLOps and telemetry workflows using Python, Docker, SQL, and automated Pytest verification.",
            "    \\item Integrated edge signal acquisition and cloud pipelines with automated anomaly reporting.",
        ],
        "experience_entries_latex": {
            "primary": {
                "role": "[CURRENT_ROLE]",
                "company": "[CURRENT_COMPANY]",
                "location": "City, Country",
                "period": "MM/YYYY - Present",
                "fallback_role": "[CURRENT_ROLE] | [CURRENT_COMPANY]",
                "exclude_keywords": [],
            },
            "secondary_latex": "",
        },
        "education_entry_latex": "\\cventry{[DEGREE]}{[UNIVERSITY]}{City, Country}{YYYY - YYYY}\n{\n    \\item Focus on Machine Learning, Signal Processing, Cloud Architecture, and Distributed Systems.\n}",
        "default_projects_latex": [
            "\\cventry{Multi-Agent LLM Orchestration Engine}{Python, Gemini / Claude APIs, Pydantic}{Remote}{2026}\n{\n    \\item Designed a structured multi-agent pipeline separating fit scoring, semantic routing, and automated PDF verification.\n}"
        ],
        "skills_badges": [
            "Multi-Agent AI \\& LLMs",
            "Python",
            "Pydantic",
            "PyTorch",
            "Docker",
            "CI/CD GitHub Actions",
            "SQL",
            "Pytest \\& QA",
        ],
        "languages_latex": "\\begin{itemize}[label={}, leftmargin=0.3cm, itemsep=4pt]\n    \\item \\textbf{English} \\hfill Professional \\quad \\textcolor{accent}{\\faCircle \\faCircle \\faCircle \\faCircle \\faCircle}\n\\end{itemize}",
        "certifications_latex": "\\begin{itemize}[label={\\color{accentblue}\\faAward}, leftmargin=0.6cm, itemsep=4pt]\n    \\item \\textbf{[CERTIFICATION_NAME]} --- [ISSUER] \\hfill \\textit{YYYY}\n\\end{itemize}",
        "summary_bold_terms": ["AI Systems"],
    }


def escape_latex(text: str) -> str:
    """Escapa caracteres especiales de LaTeX preservando coherencia de texto."""
    if not text:
        return ""
    # Evitar doble escape
    text = text.replace("\\&", "&").replace("&", "\\&")
    text = text.replace("\\%", "%").replace("%", "\\%")
    text = text.replace("\\$", "$").replace("$", "\\$")
    text = text.replace("\\#", "#").replace("#", "\\#")
    text = text.replace("\\_", "_").replace("_", "\\_")
    # Limpiar prefijos de metodología STAR
    text = re.sub(r"^(situation|task|action|result|situaci[oó]n|tarea|acci[oó]n|resultado):\s*", "", text.strip(), flags=re.IGNORECASE)
    return text.strip()

def generate_latex_timeline_source(candidate_info: Dict[str, Any], application_data: Dict[str, Any]) -> str:
    """
    Construye el código fuente en LaTeX para la plantilla Timeline ejecutiva de 2 páginas
    con tipografía Charter, nodos TikZ, badges de habilidades y certificaciones configurables.
    Garantiza una distribución perfectamente balanceada en ambas páginas sin espacios en blanco excesivos.
    """
    cfg = _load_pdf_candidate_config()
    exp_cfg = cfg.get("experience_entries_latex", {})
    primary_exp = exp_cfg.get("primary", {})
    secondary_exp_latex = exp_cfg.get("secondary_latex", "")
    core_bullets = cfg.get("core_experience_bullets_latex", [])

    summary = escape_latex(application_data.get("cv_summary", ""))
    if not summary or len(summary) < 80:
        summary = cfg.get("default_summary_latex", "")
    else:
        for term in cfg.get("summary_bold_terms", []):
            summary = summary.replace(term, f"\\textbf{{{term}}}")

    raw_exp = application_data.get("tailored_experience", [])
    exclude_keywords = [kw.lower() for kw in primary_exp.get("exclude_keywords", [])]
    primary_bullets = []
    for b in raw_exp:
        if any(kw in b.lower() for kw in exclude_keywords):
            continue
        clean_b = escape_latex(b)
        if clean_b and len(clean_b) > 20:
            primary_bullets.append(f"    \\item {clean_b}")

    for core_b in core_bullets:
        if len(primary_bullets) >= 5:
            break
        core_sample = core_b[15:45].lower()
        if not any(core_sample in b.lower() for b in primary_bullets):
            primary_bullets.append(core_b)

    primary_bullets = primary_bullets[:5]

    raw_proj = application_data.get("tailored_projects", [])
    proj_code_blocks = []
    default_city = candidate_info.get("location", cfg.get("candidate_header", {}).get("location", "Remote")).split(",")[0].strip()
    if raw_proj:
        for p in raw_proj[:2]:
            p_name = p.get("name", "Technical Project") if isinstance(p, dict) else getattr(p, "name", "Technical Project")
            p_desc = p.get("description", "") if isinstance(p, dict) else getattr(p, "description", "")
            p_name = escape_latex(p_name)
            p_desc = escape_latex(p_desc)
            proj_code_blocks.append(f"""\\cventry{{{p_name}}}{{Ingeniería de Proyectos y Analítica}}{{{escape_latex(default_city)}}}{{2026}}
{{
    \\item {p_desc}
    \\item Implementación de flujos de análisis, validación de señales y automatización de reportes operativos mediante Python y SQL.
    \\item Desarrollo de componentes para almacenamiento, consulta, visualización y documentación de los resultados, facilitando la trazabilidad operativa.
}}""")

    if len(proj_code_blocks) < 2 and cfg.get("default_projects_latex"):
        proj_code_blocks = cfg["default_projects_latex"]

    projects_latex = "\n\n".join(proj_code_blocks)

    hdr_cfg = cfg.get("candidate_header", {})
    c_name = escape_latex(candidate_info.get("name") or hdr_cfg.get("name", "[YOUR_NAME]")).upper()
    c_email = candidate_info.get("email") or hdr_cfg.get("email", "candidate@example.com")
    c_phone = escape_latex(candidate_info.get("phone") or hdr_cfg.get("phone", "+00 000 000 0000"))
    c_location = escape_latex(candidate_info.get("location") or hdr_cfg.get("location", "City, Country"))
    c_linkedin = candidate_info.get("linkedin") or hdr_cfg.get("linkedin", "linkedin.com/in/your-profile")
    c_github = candidate_info.get("github") or hdr_cfg.get("github", "github.com/your-username")
    c_linkedin_url = c_linkedin if c_linkedin.startswith("http") else f"https://{c_linkedin}"
    c_github_url = c_github if c_github.startswith("http") else f"https://{c_github}"

    skills_badges_latex = "\n".join(f"\\skillbadge{{{badge}}}" for badge in cfg.get("skills_badges", []))
    education_latex = cfg.get("education_entry_latex", "")
    languages_latex = cfg.get("languages_latex", "")
    certifications_latex = cfg.get("certifications_latex", "")

    latex_source = f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[margin=0.55in, top=0.45in, bottom=0.45in]{{geometry}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{charter}}
\\usepackage{{fontawesome5}}
\\usepackage{{xcolor}}
\\usepackage{{titlesec}}
\\usepackage{{enumitem}}
\\usepackage{{tikz}}
\\usepackage{{hyperref}}
\\usepackage{{tcolorbox}}
\\tcbuselibrary{{skins, breakable}}
\\usepackage{{microtype}}

\\definecolor{{headerbg}}{{HTML}}{{FFFFFF}}
\\definecolor{{accent}}{{HTML}}{{1E3A5F}}     % Professional Dark Navy
\\definecolor{{accentblue}}{{HTML}}{{2B6CB0}} % Slate Blue
\\definecolor{{lightgray}}{{HTML}}{{F3F4F6}}
\\definecolor{{darktext}}{{HTML}}{{1F2937}}
\\definecolor{{skillbg}}{{HTML}}{{374151}}
\\definecolor{{bulletline}}{{HTML}}{{9CA3AF}}
\\definecolor{{subtletext}}{{HTML}}{{4B5563}}

\\hypersetup{{colorlinks=true, linkcolor=accentblue, urlcolor=accentblue}}

\\titleformat{{\\section}}{{\\large\\bfseries\\color{{accent}}}}{{}}{{0em}}{{}}[\\vspace{{1pt}}\\titlerule]
\\titlespacing{{\\section}}{{0pt}}{{9pt}}{{5pt}}

\\newtcbox{{\\skillbadge}}{{
    on line, box align=base,
    colback=skillbg, colframe=skillbg,
    colupper=white,
    fontupper=\\small\\bfseries,
    arc=4pt, boxrule=0pt,
    left=6pt, right=6pt, top=3pt, bottom=3pt,
    boxsep=0pt
}}

\\newtcolorbox{{timelineentry}}{{
    blanker,
    breakable,
    borderline west={{1.5pt}}{{0pt}}{{bulletline}},
    left=1.2em,
    top=0pt,
    bottom=0pt,
    before skip=0.4ex,
    after skip=1.8ex
}}

\\newcommand{{\\cventry}}[5]{{%
  \\noindent
  \\begin{{minipage}}{{\\textwidth}}
    \\vspace{{0pt}}%
    \\tikz[baseline=-0.7ex]{{\\node[draw=accent, fill=white, circle, inner sep=2.5pt, line width=1.5pt] {{}};}}%
    \\hspace{{0.5em}}%
    {{\\large\\bfseries\\color{{accent}} #1}}%
    \\hfill{{\\small\\bfseries\\color{{accentblue}} #4}}\\par
    \\vspace{{0.2ex}}%
    \\hspace{{1.5em}}{{\\normalsize\\bfseries\\color{{darktext}} #2}}%
    \\hfill{{\\small\\color{{subtletext}}\\textit{{#3}}}}\\par
  \\end{{minipage}}\\par
  \\vspace{{0.3ex}}%
  \\begin{{timelineentry}}
    \\small\\color{{darktext}}
    \\begin{{itemize}}[label={{\\color{{accentblue}}\\raisebox{{0.2ex}}{{\\tiny\\faCircle}}}}, leftmargin=1.2em, itemsep=0.3ex, parsep=0pt, topsep=0pt, partopsep=0pt]
      #5
    \\end{{itemize}}
  \\end{{timelineentry}}
}}

\\begin{{document}}
\\thispagestyle{{empty}}
\\color{{darktext}}

% Encabezado
\\begin{{center}}
    {{\\Huge \\bfseries\\color{{accent}} {c_name}}} \\\\[4pt]
    {{\\small\\color{{darktext}}
    \\faEnvelope\\ \\href{{mailto:{c_email}}}{{{escape_latex(c_email)}}}
    \\quad\\textcolor{{bulletline}}{{\\textbar}}\\quad
    \\faPhone\\ {c_phone}
    \\quad\\textcolor{{bulletline}}{{\\textbar}}\\quad
    \\faMapMarker*\\ {c_location} \\\\[3pt]
    \\faLinkedin\\ \\href{{{c_linkedin_url}}}{{LinkedIn}}
    \\quad\\textcolor{{bulletline}}{{\\textbar}}\\quad
    \\faGithub\\ \\href{{{c_github_url}}}{{GitHub}}
    }}
\\end{{center}}
\\vspace{{2pt}}

\\section{{Perfil Profesional}}
{summary}

\\section{{Experiencia Profesional}}

\\cventry{{{escape_latex(primary_exp.get('role', '[CURRENT_ROLE]'))}}}{{{escape_latex(primary_exp.get('company', '[CURRENT_COMPANY]'))}}}{{{escape_latex(primary_exp.get('location', default_city))}}}{{{escape_latex(primary_exp.get('period', 'MM/YYYY - Present'))}}}
{{
{chr(10).join(primary_bullets)}
}}

{secondary_exp_latex}

\\section{{Educación}}

{education_latex}

\\newpage

\\section{{Proyectos Relevantes}}

{projects_latex}

\\section{{Habilidades Técnicas y Metodologías}}
\\begin{{tcolorbox}}[colback=lightgray, colframe=lightgray, boxrule=0pt, arc=6pt, left=8pt, right=8pt, top=8pt, bottom=8pt]
\\noindent
\\linespread{{1.6}}\\selectfont
{skills_badges_latex}
\\end{{tcolorbox}}

\\section{{Idiomas}}
{languages_latex}

\\section{{Certificaciones}}
{certifications_latex}

\\end{{document}}
"""
    return latex_source

def build_pdf(candidate_info: Dict[str, Any], application_data: Dict[str, Any], output_path: str) -> str:
    """
    Genera el CV utilizando la plantilla LaTeX Timeline ejecutiva (Charter + TikZ + 2 páginas).
    Compila directamente con tools/tectonic.exe y genera tanto el .pdf como el .tex editable.
    Si Tectonic no está disponible, realiza un fallback automático a PyMuPDF.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    base_name = os.path.splitext(output_path)[0]
    tex_path = f"{base_name}.tex"

    latex_code = generate_latex_timeline_source(candidate_info, application_data)
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_code)

    tectonic_exe = os.path.join(os.path.dirname(__file__), "tools", "tectonic.exe")
    if os.path.exists(tectonic_exe):
        try:
            out_dir = os.path.dirname(output_path)
            cmd = [tectonic_exe, tex_path, "--outdir", out_dir]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            compiled_pdf = os.path.join(out_dir, f"{os.path.splitext(os.path.basename(tex_path))[0]}.pdf")
            if os.path.exists(compiled_pdf) and compiled_pdf != output_path:
                import shutil
                shutil.move(compiled_pdf, output_path)
            return output_path
        except Exception as e:
            print(f"[!] Aviso: Compilación con Tectonic falló ({e}), usando motor de respaldo PyMuPDF...")

    # Fallback PyMuPDF (solo en caso de error extremo de LaTeX)
    return build_pymupdf_fallback(candidate_info, application_data, output_path)

def build_pymupdf_fallback(candidate_info: Dict[str, Any], application_data: Dict[str, Any], output_path: str) -> str:
    doc = fitz.open()
    page = doc.new_page(width=595.27, height=841.89)
    font_regular = "helv"
    font_bold = "hebo"

    if os.path.exists("C:/Windows/Fonts/arial.ttf"):
        font_regular = "arial"
        page.insert_font(fontname="arial", fontfile="C:/Windows/Fonts/arial.ttf")
    if os.path.exists("C:/Windows/Fonts/arialbd.ttf"):
        font_bold = "arialbd"
        page.insert_font(fontname="arialbd", fontfile="C:/Windows/Fonts/arialbd.ttf")

    C_PRIMARY = (0.12, 0.23, 0.37)
    C_TEXT = (0.12, 0.16, 0.22)
    C_MUTED = (0.35, 0.40, 0.48)

    cfg = _load_pdf_candidate_config()
    hdr_cfg = cfg.get("candidate_header", {})
    primary_exp = cfg.get("experience_entries_latex", {}).get("primary", {})

    margin_x = 40
    y = 40
    name = (candidate_info.get("name") or hdr_cfg.get("name", "[YOUR_NAME]")).upper()
    page.insert_text((margin_x, y), name, fontsize=15.5, fontname=font_bold, color=C_PRIMARY)
    y += 18
    title = candidate_info.get("title") or hdr_cfg.get("title", "AI Systems & MLOps Engineer")
    page.insert_text((margin_x, y), title, fontsize=10.0, fontname=font_bold, color=C_TEXT)
    y += 14
    contact_line = (
        f"{candidate_info.get('email', hdr_cfg.get('email', 'candidate@example.com'))} | "
        f"{candidate_info.get('phone', hdr_cfg.get('phone', '+00 000 000 0000'))} | "
        f"{candidate_info.get('location', hdr_cfg.get('location', 'City, Country'))} | "
        f"{candidate_info.get('linkedin', hdr_cfg.get('linkedin', 'linkedin.com/in/your-profile'))}"
    )
    page.insert_text((margin_x, y), contact_line, fontsize=8.0, fontname=font_regular, color=C_MUTED)
    y += 10
    page.draw_line((margin_x, y), (595 - margin_x, y), color=C_PRIMARY, width=1.4)
    y += 14

    page.insert_text((margin_x, y), "RESUMEN PROFESIONAL", fontsize=9.5, fontname=font_bold, color=C_PRIMARY)
    y += 12
    summary = application_data.get("cv_summary", "")
    rect_sum = fitz.Rect(margin_x, y, 595 - margin_x, y + 40)
    page.insert_textbox(rect_sum, summary, fontsize=8.2, fontname=font_regular, color=C_TEXT)
    y += 45

    page.insert_text((margin_x, y), "EXPERIENCIA PROFESIONAL", fontsize=9.5, fontname=font_bold, color=C_PRIMARY)
    y += 12
    role_line = primary_exp.get(
        "fallback_role",
        f"{primary_exp.get('role', '[CURRENT_ROLE]')} | {primary_exp.get('company', '[CURRENT_COMPANY]')}",
    )
    page.insert_text((margin_x, y), role_line, fontsize=9.0, fontname=font_bold, color=C_TEXT)
    page.insert_text((595 - margin_x - 105, y), primary_exp.get("period", "MM/YYYY - Present"), fontsize=8.0, fontname=font_regular, color=C_MUTED)
    y += 12

    for b in application_data.get("tailored_experience", [])[:4]:
        b_clean = "• " + re.sub(r"^(situation|task|action|result|situaci[oó]n|tarea|acci[oó]n|resultado):\s*", "", b.strip(), flags=re.IGNORECASE)
        b_rect = fitz.Rect(margin_x + 5, y, 595 - margin_x, y + 25)
        page.insert_textbox(b_rect, b_clean, fontsize=8.0, fontname=font_regular, color=C_TEXT)
        y += 26

    doc.save(output_path)
    doc.close()
    return output_path

if __name__ == "__main__":
    print("Módulo generador de PDF (LaTeX Timeline + Tectonic) listo.")
