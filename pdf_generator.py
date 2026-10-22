import os
import re
import subprocess
import fitz  # PyMuPDF fallback
from typing import Dict, Any, List

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

CORE_AM4_BULLETS = [
    r"    \item Ejecución de pruebas, validación y diagnóstico a motores y equipos industriales en proyectos para clientes como Refoenergy y Brinsa, asegurando parámetros de operación y confiabilidad.",
    r"    \item Realización de medidas técnicas e instrumentación en campo en proyectos para Geopark (DPS), garantizando la precisión, consistencia y calidad de los datos operativos.",
    r"    \item Programación básica de controladores lógicos programables (PLC) mediante lenguajes de descripción de hardware (HDL), apoyando la automatización de procesos industriales.",
    r"    \item Desarrollo de flujos para adquisición, limpieza y transformación de datos operativos provenientes de sistemas de medición, integrando diferentes fuentes de información.",
    r"    \item Implementación de automatizaciones en Python y C/C++ para capturar, organizar y procesar variables de operación industrial, reduciendo tareas manuales y facilitando el monitoreo.",
    r"    \item Ejecución de pruebas, validaciones y análisis de inconsistencias en sistemas y señales de campo, documentando hallazgos y apoyando la resolución estructurada de problemas.",
    r"    \item Coordinación y documentación de actividades técnicas del proyecto, seguimiento de entregables y elaboración de reportes para mantener la trazabilidad de la información operativa."
]

def generate_latex_timeline_source(candidate_info: Dict[str, Any], application_data: Dict[str, Any]) -> str:
    """
    Construye el código fuente en LaTeX para la plantilla Timeline ejecutiva de 2 páginas
    con tipografía Charter, nodos TikZ, badges de habilidades y certificaciones Cisco/UNAL.
    Garantiza una distribución perfectamente balanceada en ambas páginas sin espacios en blanco excesivos.
    """
    summary = escape_latex(application_data.get("cv_summary", ""))
    if not summary or len(summary) < 80:
        summary = r"\textbf{Ingeniero Electrónico} de la Universidad Nacional de Colombia (promedio 4.6/5.0) y actual \textbf{Ingeniero de Proyectos} en AM4. Especializado en el liderazgo de iniciativas de ingeniería, automatización de flujos de datos e infraestructura bajo entornos Linux y redes. Destacado por integrar capacidades de \textbf{Inteligencia Artificial y analítica} para robustecer la seguridad tecnológica, el monitoreo continuo y la mitigación de riesgos operativos. Con sólida formación en redes y ciberseguridad (\textbf{Cisco CCNA y Ethical Hacking}), capacidad probada en gestión de proyectos industriales de alta exigencia y residencia en Bogotá (disponibilidad híbrida)."
    else:
        # Enriquecer términos clave con negrita ATS
        summary = summary.replace("Ingeniero Electrónico", r"\textbf{Ingeniero Electrónico}")
        summary = summary.replace("Ingeniero de Proyectos", r"\textbf{Ingeniero de Proyectos}")
        summary = summary.replace("Universidad Nacional de Colombia", r"\textbf{Universidad Nacional de Colombia}")

    # Experiencia AM4: Asegurar 7 viñetas para equilibrar completamente la Página 1
    raw_exp = application_data.get("tailored_experience", [])
    am4_bullets = []
    for b in raw_exp:
        if "auxiliar" not in b.lower() and "universidad nacional" not in b.lower():
            clean_b = escape_latex(b)
            if clean_b and len(clean_b) > 20:
                am4_bullets.append(f"    \\item {clean_b}")

    # Completar con viñetas core de AM4 hasta tener exactamente 7 viñetas
    for core_b in CORE_AM4_BULLETS:
        if len(am4_bullets) >= 7:
            break
        core_sample = core_b[15:45].lower()
        if not any(core_sample in b.lower() for b in am4_bullets):
            am4_bullets.append(core_b)

    # Proyectos: 2 proyectos con 3 viñetas detalladas cada uno para equilibrar la Página 2
    raw_proj = application_data.get("tailored_projects", [])
    proj_code_blocks = []
    if raw_proj:
        for p in raw_proj[:2]:
            p_name = p.get("name", "Proyecto Técnico") if isinstance(p, dict) else getattr(p, "name", "Proyecto Técnico")
            p_desc = p.get("description", "") if isinstance(p, dict) else getattr(p, "description", "")
            p_name = escape_latex(p_name)
            p_desc = escape_latex(p_desc)
            proj_code_blocks.append(f"""\\cventry{{{p_name}}}{{Ingeniería de Proyectos y Analítica}}{{Bogotá}}{{2026}}
{{
    \\item {p_desc}
    \\item Implementación de flujos de análisis, validación de señales y automatización de reportes operativos mediante Python y SQL.
    \\item Desarrollo de componentes para almacenamiento, consulta, visualización y documentación de los resultados, facilitando la trazabilidad operativa.
}}""")

    if len(proj_code_blocks) < 2:
        proj_code_blocks = [
            r"""\cventry{Procesamiento y análisis de sistemas de medición}{Python y automatización de reportes}{Bogotá}{2026}
{
    \item Desarrollo de un flujo para adquirir, estructurar y procesar datos provenientes de instrumentación y medición, incluyendo validación de registros y análisis de resultados mediante Python.
    \item Implementación de calibración, transformación y visualización de datos industriales, junto con generación automática de informes para facilitar el seguimiento operativo.
    \item Realización de controles de calidad y pruebas de consistencia para identificar señales atípicas, errores de adquisición y oportunidades de mejora en procesos de control.
}""",
            r"""\cventry{Análisis de datos para inspección técnica}{AM4}{Bogotá}{2026}
{
    \item Procesamiento y organización de datos de inspección aérea y modelos de visión artificial para la detección y monitoreo automático de infraestructura eléctrica y postes.
    \item Análisis de métricas, validación de resultados y seguimiento de pruebas de campo para evaluar la calidad de las inspecciones y apoyar decisiones de mantenimiento.
    \item Desarrollo de componentes para almacenamiento, consulta, visualización y documentación de los resultados, facilitando la trazabilidad del estado de la infraestructura.
}"""
        ]

    projects_latex = "\n\n".join(proj_code_blocks)

    latex_source = f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[margin=0.55in, top=0.5in, bottom=0.5in]{{geometry}}
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
\\titlespacing{{\\section}}{{0pt}}{{11pt}}{{7pt}}

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
    before skip=0.8ex,
    after skip=2.6ex
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
  \\vspace{{0.4ex}}%
  \\begin{{timelineentry}}
    \\small\\color{{darktext}}
    \\begin{{itemize}}[label={{\\color{{accentblue}}\\raisebox{{0.2ex}}{{\\tiny\\faCircle}}}}, leftmargin=1.2em, itemsep=0.4ex, parsep=0pt, topsep=0pt, partopsep=0pt]
      #5
    \\end{{itemize}}
  \\end{{timelineentry}}
}}

\\begin{{document}}
\\thispagestyle{{empty}}
\\color{{darktext}}

% Encabezado
\\begin{{center}}
    {{\\Huge \\bfseries\\color{{accent}} SANTIAGO ALEJANDRO OCHOA QUESADA}} \\\\[6pt]
    {{\\small\\color{{darktext}}
    \\faEnvelope\\ \\href{{mailto:santy.alejo4@gmail.com}}{{santy.alejo4@gmail.com}}
    \\quad\\textcolor{{bulletline}}{{\\textbar}}\\quad
    \\faPhone\\ +57 320 351 7153
    \\quad\\textcolor{{bulletline}}{{\\textbar}}\\quad
    \\faMapMarker*\\ Bogotá, Colombia \\\\[4pt]
    \\faLinkedin\\ \\href{{https://linkedin.com/in/santiago-alejandro-ochoa-quesada-a07a18288/}}{{LinkedIn}}
    \\quad\\textcolor{{bulletline}}{{\\textbar}}\\quad
    \\faGithub\\ \\href{{https://github.com/Sochoaq}}{{GitHub}}
    }}
\\end{{center}}
\\vspace{{4pt}}

\\section{{Perfil Profesional}}
{summary}

\\section{{Experiencia Profesional}}

\\cventry{{Ingeniero de Proyectos (Control y Automatización)}}{{AM4}}{{Bogotá}}{{04/2026 - Actualidad}}
{{
{chr(10).join(am4_bullets)}
}}

\\cventry{{Auxiliar Estudiantil}}{{Universidad Nacional de Colombia}}{{Bogotá}}{{07/2024 - 11/2025}}
{{
    \\item Apoyo en laboratorios mediante organización, validación y análisis de resultados experimentales, programación, simulación y depuración de sistemas digitales y señales.
    \\item Preparación y verificación de prácticas, registros, equipos de instrumentación y material técnico, asegurando consistencia en la toma de datos durante las sesiones.
    \\item Acompañamiento a estudiantes en análisis de resultados, identificación de errores y resolución de problemas de electrónica y control durante prácticas de laboratorio.
    \\item Elaboración de guías, reportes y presentaciones técnicas para documentar procedimientos, fallas, hallazgos y aprendizajes de manera estructurada.
}}

\\section{{Educación}}

\\cventry{{Ingeniería Electrónica}}{{Universidad Nacional de Colombia}}{{Bogotá}}{{02/2021 - 11/2025}}
{{
    \\item \\textbf{{Promedio académico: 4.6 / 5.0}}.
    \\item Formación en control continuo y discreto, automatización, sistemas digitales, procesamiento de señales, instrumentación, comunicaciones y análisis numérico.
    \\item Desarrollo de proyectos enfocados en simulación de procesos, programación de hardware, validación experimental y elaboración de reportes técnicos de ingeniería.
}}

\\newpage

\\section{{Proyectos Relevantes}}

{projects_latex}

\\section{{Habilidades}}
\\begin{{tcolorbox}}[colback=lightgray, colframe=lightgray, boxrule=0pt, arc=6pt, left=10pt, right=10pt, top=10pt, bottom=10pt]
\\noindent
\\linespread{{1.8}}\\selectfont
\\skillbadge{{Automatización de Procesos}}
\\skillbadge{{Control Industrial}}
\\skillbadge{{Ciberseguridad y Redes}}
\\skillbadge{{Cisco CCNA}}
\\skillbadge{{Ethical Hacking}}
\\skillbadge{{Linux \\& Infraestructura}}
\\skillbadge{{Python}}
\\skillbadge{{C/C++}}
\\skillbadge{{SQL}}
\\skillbadge{{Adquisición de Datos}}
\\skillbadge{{Validación de Señales}}
\\skillbadge{{Gestión de Proyectos}}
\\skillbadge{{Documentación Técnica}}
\\skillbadge{{Resolución de Problemas}}
\\skillbadge{{Trabajo en Equipo}}
\\end{{tcolorbox}}

\\section{{Idiomas}}
\\begin{{itemize}}[label={{}}, leftmargin=0.3cm, itemsep=6pt]
    \\item \\textbf{{Español}} \\hfill Nativo \\quad \\textcolor{{accent}}{{\\faCircle \\faCircle \\faCircle \\faCircle \\faCircle}}
    \\item \\textbf{{Inglés}} \\hfill B2 (Profesional de Trabajo) \\quad \\textcolor{{accent}}{{\\faCircle \\faCircle \\faCircle \\faCircle}} \\textcolor{{bulletline}}{{\\faCircle}}
    \\item \\textbf{{Francés}} \\hfill A2 \\quad \\textcolor{{accent}}{{\\faCircle \\faCircle}} \\textcolor{{bulletline}}{{\\faCircle \\faCircle \\faCircle}}
\\end{{itemize}}

\\section{{Certificaciones}}
\\begin{{itemize}}[label={{\\color{{accentblue}}\\faAward}}, leftmargin=0.6cm, itemsep=6pt]
    \\item \\textbf{{Ethical Hacking \\& Cybersecurity}} --- Cisco Networking Academy \\hfill \\textit{{04/2026}}
    \\item \\textbf{{CCNA: Introduction to Networks}} --- Cisco Networking Academy \\hfill \\textit{{07/2025}}
    \\item \\textbf{{Análisis Computacional de Datos Ambientales}} --- Universidad Nacional de Colombia \\hfill \\textit{{09/2025}}
    \\item \\textbf{{Introducción a la Fotónica Integrada y las Comunicaciones Cuánticas}} --- UNAL \\hfill \\textit{{07/2024}}
    \\item \\textbf{{Python Intermedio}} --- SoloLearn \\hfill \\textit{{03/2021}}
\\end{{itemize}}

\\vfill
\\begin{{center}}
    {{\\footnotesize\\color{{subtletext}}
    \\faGithub\\ Código fuente, proyectos técnicos y repositorios disponibles en \\href{{https://github.com/Sochoaq}}{{github.com/Sochoaq}}}}
\\end{{center}}

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

    margin_x = 40
    y = 40
    name = candidate_info.get("name", "SANTIAGO ALEJANDRO OCHOA QUESADA").upper()
    page.insert_text((margin_x, y), name, fontsize=15.5, fontname=font_bold, color=C_PRIMARY)
    y += 18
    title = candidate_info.get("title", "Ingeniero de Proyectos | AI, Cloud & Hardware Systems")
    page.insert_text((margin_x, y), title, fontsize=10.0, fontname=font_bold, color=C_TEXT)
    y += 14
    contact_line = f"{candidate_info.get('email', 'santy.alejo4@gmail.com')} | {candidate_info.get('phone', '+57 320 351 7153')} | Bogotá, Colombia | {candidate_info.get('linkedin', 'linkedin.com/in/santiago-alejandro-ochoa-quesada-a07a18288')}"
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
    page.insert_text((margin_x, y), "Ingeniero de Proyectos (Control y Automatización) | AM4", fontsize=9.0, fontname=font_bold, color=C_TEXT)
    page.insert_text((595 - margin_x - 105, y), "04/2026 - Actualidad", fontsize=8.0, fontname=font_regular, color=C_MUTED)
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
