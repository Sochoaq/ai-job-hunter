import os
import sys
import json
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from orchestrator import Orchestrator
from pdf_generator import build_pdf
import job_tracker
import job_scout

CANDIDATE_HEADER = {
    "name": "Santiago Alejandro Ochoa Quesada",
    "title": "Ingeniero de Proyectos | AI, Cloud & Hardware Systems",
    "email": "santy.alejo4@gmail.com",
    "phone": "+57 320 351 7153",
    "location": "Bogotá, Colombia",
    "linkedin": "linkedin.com/in/santiago-alejandro-ochoa-quesada-a07a18288",
    "github": "github.com/Sochoaq"
}

def print_banner():
    banner = r"""
======================================================================
     AI JOB HUNTER & CV ADAPTER - SANTIAGO OCHOA QUESADA
     Tracks: AI Engineering | Cloud & DevOps | Hardware & Embedded
======================================================================
    """
    print(banner)

def process_and_save_application(orch: Orchestrator, company: str, position: str, desc: str, url: str = ""):
    print(f"\n[*] Evaluando compatibilidad con Gemini para {company}...")
    eval_result = orch.evaluate_job(position, company, desc)
    
    if "error" in eval_result:
        print(f"[!] Error: {eval_result['error']}")
        return

    fit_score = eval_result.get("fit_score", 0)
    rec = eval_result.get("recommendation", "N/A")
    track = eval_result.get("profile_track", "N/A")
    lang_fit = eval_result.get("language_fit", "N/A")

    print(f"\n---------------- RESULTADO DE EVALUACIÓN ----------------")
    print(f" Compatibilidad:  {fit_score}/100")
    print(f" Recomendación:   {rec}")
    print(f" Track Detectado: {track}")
    print(f" Idioma (B2 Fit): {lang_fit}")
    print(f" Fortalezas:      {', '.join(eval_result.get('matching_skills', []))}")
    print(f" Puntos Débiles:  {', '.join(eval_result.get('missing_skills', []))}")
    print(f" Estrategia:      {eval_result.get('suggested_angle', '')}")
    print("---------------------------------------------------------")

    choice = input("\n¿Deseas adaptar tu CV en PDF y carta para esta vacante? (s/n): ").strip().lower()
    if choice != "s":
        print("[*] Postulación no generada.")
        return

    print("\n[*] Generando CV a la medida y carta de presentación con Gemini...")
    tailor_result = orch.tailor_application(position, company, desc, eval_result)
    
    if "error" in tailor_result:
        print(f"[!] Error al redactar: {tailor_result['error']}")
        return

    # Generar PDF de 1 página ATS
    safe_company = "".join(c for c in company if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"CV_Santiago_Ochoa_{safe_company}.pdf")
    cl_path = os.path.join(output_dir, f"Cover_Letter_{safe_company}.txt")

    build_pdf(CANDIDATE_HEADER, tailor_result, pdf_path)
    
    with open(cl_path, "w", encoding="utf-8") as f:
        f.write(tailor_result.get("cover_letter", ""))

    # Registrar en base de datos SQLite
    app_id = job_tracker.add_application(
        company=company,
        position=position,
        track=track,
        fit_score=fit_score,
        url=url,
        notes=f"Idioma: {lang_fit}. Ángulo: {eval_result.get('suggested_angle', '')}"
    )

    print(f"\n[OK] ¡Postulación completada con éxito!")
    print(f"📄 CV PDF (1 página ATS): {pdf_path}")
    print(f"✉️  Cover Letter:           {cl_path}")
    print(f"📊 Registrado en Tracker DB con ID #{app_id}")

def menu_scout(orch: Orchestrator):
    print("\n[1] Explorando vacantes remotas abiertas en la web...")
    jobs = job_scout.find_jobs(max_results=15)
    if not jobs:
        print("[!] No se pudieron cargar vacantes en este momento.")
        return

    print("\nVacantes encontradas:")
    for idx, j in enumerate(jobs, 1):
        print(f" {idx:2d}. [{j['track_hint']}] {j['title']} @ {j['company']} ({j['location']})")

    sel = input("\nIngresa el número de la vacante que deseas evaluar (o presiona Enter para volver): ").strip()
    if not sel.isdigit() or int(sel) < 1 or int(sel) > len(jobs):
        return

    job = jobs[int(sel) - 1]
    process_and_save_application(
        orch,
        company=job["company"],
        position=job["title"],
        desc=job["description"],
        url=job["url"]
    )

def menu_custom(orch: Orchestrator):
    print("\n[2] Postular a vacante personalizada")
    company = input("Nombre de la Empresa: ").strip()
    if not company:
        print("[!] La empresa no puede estar vacía.")
        return
    position = input("Título del Cargo: ").strip()
    url = input("URL de la oferta (opcional): ").strip()
    print("\nPega o escribe la descripción de la vacante (escribe 'FIN' en una línea separada al terminar):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "FIN":
            break
        lines.append(line)
    desc = "\n".join(lines).strip()

    if not desc:
        print("[!] Descripción vacía.")
        return

    process_and_save_application(orch, company, position, desc, url)

def menu_tracker():
    print("\n[3] SEGUIMIENTO DE POSTULACIONES (job_tracker.db)")
    apps = job_tracker.list_applications()
    if not apps:
        print("Aún no tienes aplicaciones registradas en la base de datos.")
        return

    print("-" * 80)
    print(f"{'ID':<4} | {'EMPRESA':<20} | {'CARGO':<25} | {'TRACK':<15} | {'FIT':<4} | {'ESTADO'}")
    print("-" * 80)
    for a in apps:
        print(f"{a['id']:<4} | {a['company'][:20]:<20} | {a['position'][:25]:<25} | {a['track'][:15]:<15} | {a['fit_score']:<4} | {a['status']}")
    print("-" * 80)

    sub = input("\n¿Deseas actualizar el estado de alguna postulación? (ID para editar / Enter para salir): ").strip()
    if sub.isdigit():
        app_id = int(sub)
        print("Estados: 1. PENDING_REVIEW | 2. APPLIED | 3. INTERVIEW | 4. REJECTED | 5. OFFER")
        st_choice = input("Selecciona nuevo estado (1-5): ").strip()
        st_map = {
            "1": "PENDING_REVIEW",
            "2": "APPLIED",
            "3": "INTERVIEW",
            "4": "REJECTED",
            "5": "OFFER"
        }
        if st_choice in st_map:
            job_tracker.update_status(app_id, st_map[st_choice])
            print(f"[OK] Estado de aplicación #{app_id} actualizado a {st_map[st_choice]}.")

def main():
    orch = Orchestrator()
    while True:
        print_banner()
        print("1. Buscar y evaluar vacantes remotas (RemoteOK + Arbeitnow)")
        print("2. Pegar y postular a vacante personalizada (LinkedIn, Torre, etc.)")
        print("3. Ver y gestionar seguimiento de postulaciones (job_tracker.db)")
        print("4. Salir")
        
        choice = input("\nSelecciona una opción (1-4): ").strip()
        if choice == "1":
            menu_scout(orch)
        elif choice == "2":
            menu_custom(orch)
        elif choice == "3":
            menu_tracker()
        elif choice == "4":
            print("\n¡Éxitos en tu búsqueda de empleo! Hasta pronto.")
            break
        else:
            print("[!] Opción inválida.")

if __name__ == "__main__":
    main()
