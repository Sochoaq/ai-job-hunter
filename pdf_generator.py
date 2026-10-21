import os
import fitz  # PyMuPDF
from typing import Dict, Any, List

def build_pdf(candidate_info: Dict[str, Any], application_data: Dict[str, Any], output_path: str):
    """
    Genera un CV profesional en PDF de 1 página con diseño tipográfico limpio
    aprobado para sistemas ATS (Applicant Tracking Systems).
    """
    doc = fitz.open()
    # A4 standard (595.27 x 841.89 points)
    page = doc.new_page(width=595.27, height=841.89)

    # Registrar fuentes del sistema si existen
    font_regular = "helv"
    font_bold = "hebo"

    if os.path.exists("C:/Windows/Fonts/arial.ttf"):
        font_regular = "arial"
        page.insert_font(fontname="arial", fontfile="C:/Windows/Fonts/arial.ttf")

    if os.path.exists("C:/Windows/Fonts/arialbd.ttf"):
        font_bold = "arialbd"
        page.insert_font(fontname="arialbd", fontfile="C:/Windows/Fonts/arialbd.ttf")
    
    # Paleta sobria profesional
    C_PRIMARY = (0.05, 0.2, 0.45)   # Navy Blue
    C_TEXT = (0.15, 0.15, 0.15)      # Charcoal Dark
    C_MUTED = (0.4, 0.4, 0.4)        # Muted Gray

    margin_x = 42
    y = 42

    # 1. HEADER (Nombre y Contacto)
    name = candidate_info.get("name", "SANTIAGO ALEJANDRO OCHOA QUESADA").upper()
    page.insert_text((margin_x, y), name, fontsize=16, fontname=font_bold, color=C_PRIMARY)
    y += 18
    
    title = candidate_info.get("title", "Ingeniero de Proyectos | AI, Cloud & Hardware Systems")
    page.insert_text((margin_x, y), title, fontsize=10.5, fontname=font_bold, color=C_TEXT)
    y += 15

    contact_line = f"{candidate_info.get('email', 'santy.alejo4@gmail.com')}  |  {candidate_info.get('phone', '+57 320 351 7153')}  |  Bogotá, Colombia  |  {candidate_info.get('linkedin', 'linkedin.com/in/santiago-alejandro-ochoa-quesada-a07a18288')}"
    page.insert_text((margin_x, y), contact_line, fontsize=8.2, fontname=font_regular, color=C_MUTED)
    y += 12

    # Línea divisoria superior
    page.draw_line((margin_x, y), (595 - margin_x, y), color=C_PRIMARY, width=1.5)
    y += 15

    # 2. RESUMEN PROFESIONAL ADAPTADO
    page.insert_text((margin_x, y), "RESUMEN PROFESIONAL", fontsize=10, fontname=font_bold, color=C_PRIMARY)
    y += 13
    summary = application_data.get("cv_summary", "")
    summary_rect = fitz.Rect(margin_x, y, 595 - margin_x, y + 42)
    page.insert_textbox(summary_rect, summary, fontsize=8.5, fontname=font_regular, color=C_TEXT)
    y += 46

    # 3. EXPERIENCIA LABORAL
    page.insert_text((margin_x, y), "EXPERIENCIA PROFESIONAL", fontsize=10, fontname=font_bold, color=C_PRIMARY)
    y += 13

    # Cargo actual en AM4
    page.insert_text((margin_x, y), "Ingeniero de Proyectos — Desarrollo de Software y Datos | AM4", fontsize=9.2, fontname=font_bold, color=C_TEXT)
    page.insert_text((595 - margin_x - 105, y), "04/2026 — Actualidad", fontsize=8.2, fontname=font_regular, color=C_MUTED)
    y += 13

    # Viñetas STAR adaptadas
    experience_bullets = application_data.get("tailored_experience", [])
    for b in experience_bullets[:4]:
        bullet_text = "• " + b.replace("Situation:", "").replace("Task:", "").replace("Action:", "").replace("Result:", "").strip()
        b_rect = fitz.Rect(margin_x + 5, y, 595 - margin_x, y + 26)
        page.insert_textbox(b_rect, bullet_text, fontsize=8.0, fontname=font_regular, color=C_TEXT)
        y += 27

    # Experiencia UNAL
    y += 2
    page.insert_text((margin_x, y), "Auxiliar Estudiantil | Universidad Nacional de Colombia", fontsize=9.2, fontname=font_bold, color=C_TEXT)
    page.insert_text((595 - margin_x - 105, y), "07/2024 — 11/2025", fontsize=8.2, fontname=font_regular, color=C_MUTED)
    y += 13
    unal_rect = fitz.Rect(margin_x + 5, y, 595 - margin_x, y + 20)
    page.insert_textbox(unal_rect, "• Programación, simulación y depuración de sistemas digitales; validación experimental de modelos y soporte técnico.", fontsize=8.0, fontname=font_regular, color=C_TEXT)
    y += 25

    # 4. PROYECTOS RELEVANTES ADAPTADOS
    page.insert_text((margin_x, y), "PROYECTOS TÉCNICOS DESTACADOS", fontsize=10, fontname=font_bold, color=C_PRIMARY)
    y += 13

    projects = application_data.get("tailored_projects", [])
    for p in projects[:2]:
        p_name = p.get("name", "Proyecto") if isinstance(p, dict) else getattr(p, "name", "Proyecto")
        p_desc = p.get("description", "") if isinstance(p, dict) else getattr(p, "description", "")
        page.insert_text((margin_x, y), f"• {p_name}:", fontsize=8.8, fontname=font_bold, color=C_TEXT)
        y += 11
        p_rect = fitz.Rect(margin_x + 8, y, 595 - margin_x, y + 24)
        page.insert_textbox(p_rect, p_desc, fontsize=8.0, fontname=font_regular, color=C_TEXT)
        y += 25

    # 5. EDUCACIÓN Y CERTIFICACIONES
    page.insert_text((margin_x, y), "EDUCACIÓN Y HABILIDADES TÉCNICAS", fontsize=10, fontname=font_bold, color=C_PRIMARY)
    y += 13

    edu_text = "Ingeniería Electrónica — Universidad Nacional de Colombia (UNAL) | Promedio: 4.6 / 5.0  (2021 — 2025)"
    page.insert_text((margin_x, y), edu_text, fontsize=8.5, fontname=font_bold, color=C_TEXT)
    y += 13

    skills_text = "Stack: Python, C/C++, SQL, PyTorch, Scikit-Learn, SciPy, Docker, AWS (EC2/S3/IAM), GitHub Actions CI/CD, Pytest, Linux."
    page.insert_text((margin_x, y), skills_text, fontsize=8.0, fontname=font_regular, color=C_MUTED)

    # Guardar documento
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    doc.close()
    return output_path

if __name__ == "__main__":
    print("Módulo generador de PDF (PyMuPDF) cargado.")
