import os
import re
import fitz  # PyMuPDF
from typing import Dict, Any, List

def clean_bullet_prefix(text: str) -> str:
    """Remueve prefijos de metodología STAR tanto en inglés como en español."""
    cleaned = re.sub(r"^(situation|task|action|result|situaci[oó]n|tarea|acci[oó]n|resultado):\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"^(bullet\s*\d*|\d+[\.\)])\s*", "", cleaned).strip()
    return cleaned

def insert_dynamic_text(page, x1, y, x2, text, fontsize, fontname, color, line_spacing=3.0) -> float:
    """
    Inserta texto con cálculo exacto de altura ocupada,
    evitando truncamiento o desbordamiento silencioso de PyMuPDF.
    """
    max_h = 140.0
    rect = fitz.Rect(x1, y, x2, y + max_h)
    rc = page.insert_textbox(rect, text, fontsize=fontsize, fontname=fontname, color=color)
    if rc >= 0:
        used_h = max_h - rc
        return y + used_h + line_spacing
    else:
        # Si excedió por alguna razón, forzar con altura estimada
        return y + 30.0

def build_pdf(candidate_info: Dict[str, Any], application_data: Dict[str, Any], output_path: str):
    """
    Genera un CV profesional en PDF de 1 página con diseño tipográfico limpio
    aprobado para sistemas ATS (Applicant Tracking Systems).
    """
    doc = fitz.open()
    # A4 standard (595.27 x 841.89 points)
    page = doc.new_page(width=595.27, height=841.89)

    font_regular = "helv"
    font_bold = "hebo"

    if os.path.exists("C:/Windows/Fonts/arial.ttf"):
        font_regular = "arial"
        page.insert_font(fontname="arial", fontfile="C:/Windows/Fonts/arial.ttf")

    if os.path.exists("C:/Windows/Fonts/arialbd.ttf"):
        font_bold = "arialbd"
        page.insert_font(fontname="arialbd", fontfile="C:/Windows/Fonts/arialbd.ttf")
    
    C_PRIMARY = (0.05, 0.2, 0.45)   # Deep Navy
    C_TEXT = (0.15, 0.15, 0.15)      # Charcoal
    C_MUTED = (0.38, 0.38, 0.38)     # Muted Slate
    C_LINE = (0.75, 0.8, 0.88)

    margin_x = 40
    max_x = 595 - margin_x
    y = 38

    # 1. HEADER (Nombre y Contacto)
    name = candidate_info.get("name", "SANTIAGO ALEJANDRO OCHOA QUESADA").upper()
    page.insert_text((margin_x, y), name, fontsize=15.5, fontname=font_bold, color=C_PRIMARY)
    y += 17
    
    title = candidate_info.get("title", "Ingeniero de Proyectos | AI, Cloud & Hardware Systems")
    page.insert_text((margin_x, y), title, fontsize=10.0, fontname=font_bold, color=C_TEXT)
    y += 14

    contact_line = f"{candidate_info.get('email', 'santy.alejo4@gmail.com')}  |  {candidate_info.get('phone', '+57 320 351 7153')}  |  Bogotá, Colombia  |  {candidate_info.get('linkedin', 'linkedin.com/in/santiago-alejandro-ochoa-quesada-a07a18288')}"
    page.insert_text((margin_x, y), contact_line, fontsize=8.0, fontname=font_regular, color=C_MUTED)
    y += 10

    # Línea divisoria
    page.draw_line((margin_x, y), (max_x, y), color=C_PRIMARY, width=1.4)
    y += 12

    # 2. RESUMEN PROFESIONAL ADAPTADO
    page.insert_text((margin_x, y), "RESUMEN PROFESIONAL", fontsize=9.5, fontname=font_bold, color=C_PRIMARY)
    y += 12
    summary = application_data.get("cv_summary", "")
    y = insert_dynamic_text(page, margin_x, y, max_x, summary, 8.2, font_regular, C_TEXT, line_spacing=6.0)

    # 3. EXPERIENCIA LABORAL
    page.insert_text((margin_x, y), "EXPERIENCIA PROFESIONAL", fontsize=9.5, fontname=font_bold, color=C_PRIMARY)
    y += 12

    # Cargo actual en AM4
    page.insert_text((margin_x, y), "Ingeniero de Proyectos — Desarrollo de Software y Datos | AM4", fontsize=9.0, fontname=font_bold, color=C_TEXT)
    page.insert_text((max_x - 105, y), "04/2026 — Actualidad", fontsize=8.0, fontname=font_regular, color=C_MUTED)
    y += 11

    # Viñetas STAR adaptadas para AM4 (primeras 3 viñetas para AM4)
    experience_bullets = application_data.get("tailored_experience", [])
    am4_bullets = [clean_bullet_prefix(b) for b in experience_bullets if "auxiliar" not in b.lower() and "universidad nacional" not in b.lower()]
    if not am4_bullets:
        am4_bullets = [clean_bullet_prefix(b) for b in experience_bullets[:3]]

    for b in am4_bullets[:3]:
        bullet_text = f"•  {b}"
        y = insert_dynamic_text(page, margin_x + 5, y, max_x, bullet_text, 7.8, font_regular, C_TEXT, line_spacing=2.5)

    # Cargo UNAL
    y += 3
    page.insert_text((margin_x, y), "Auxiliar Estudiantil | Universidad Nacional de Colombia", fontsize=9.0, fontname=font_bold, color=C_TEXT)
    page.insert_text((max_x - 105, y), "07/2024 — 11/2025", fontsize=8.0, fontname=font_regular, color=C_MUTED)
    y += 11

    unal_bullet = "•  Programación, simulación y depuración de sistemas digitales; validación experimental de modelos de ingeniería y soporte técnico de laboratorio."
    # Buscar si Gemini incluyó una viñeta para UNAL
    for b in experience_bullets:
        if "auxiliar" in b.lower() or "universidad nacional" in b.lower():
            unal_bullet = f"•  {clean_bullet_prefix(b)}"
            break
    y = insert_dynamic_text(page, margin_x + 5, y, max_x, unal_bullet, 7.8, font_regular, C_TEXT, line_spacing=6.0)

    # 4. PROYECTOS RELEVANTES ADAPTADOS
    page.insert_text((margin_x, y), "PROYECTOS TÉCNICOS DESTACADOS", fontsize=9.5, fontname=font_bold, color=C_PRIMARY)
    y += 12

    projects = application_data.get("tailored_projects", [])
    for p in projects[:2]:
        p_name = p.get("name", "Proyecto") if isinstance(p, dict) else getattr(p, "name", "Proyecto")
        p_desc = p.get("description", "") if isinstance(p, dict) else getattr(p, "description", "")
        page.insert_text((margin_x, y), f"•  {p_name}", fontsize=8.6, fontname=font_bold, color=C_TEXT)
        y += 10
        y = insert_dynamic_text(page, margin_x + 8, y, max_x, p_desc, 7.8, font_regular, C_TEXT, line_spacing=4.0)

    # 5. EDUCACIÓN Y HABILIDADES
    y += 2
    page.insert_text((margin_x, y), "EDUCACIÓN Y HABILIDADES TÉCNICAS", fontsize=9.5, fontname=font_bold, color=C_PRIMARY)
    y += 12

    edu_text = "Ingeniería Electrónica — Universidad Nacional de Colombia (UNAL)  |  Promedio: 4.6 / 5.0   (2021 — 2025)"
    page.insert_text((margin_x, y), edu_text, fontsize=8.2, fontname=font_bold, color=C_TEXT)
    y += 11

    skills_text = "Stack: Python, C/C++, SQL, PyTorch, Scikit-Learn, SciPy, Docker, AWS (EC2/S3/IAM), GitHub Actions CI/CD, Pytest, Linux."
    page.insert_text((margin_x, y), skills_text, fontsize=7.8, fontname=font_regular, color=C_MUTED)

    # Guardar
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    doc.close()
    return output_path

if __name__ == "__main__":
    print("Módulo generador de PDF (PyMuPDF) cargado.")
