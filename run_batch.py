import os
import sys

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

def execute_batch(source="multinationals", threshold=75, limit_per_cluster=2):
    print("=" * 75, flush=True)
    print("   EJECUCIÓN AUTÓNOMA EN LOTE (MODO 4 - AUTOPILOTO)", flush=True)
    print("=" * 75, flush=True)
    
    orch = Orchestrator()

    if source == "multinationals":
        print("[*] Rastreador en vivo: Conectando con LinkedIn Jobs (Multinacionales Bogotá/Colombia)...", flush=True)
        jobs = job_scout.scout_multinationals(location="Bogota, Colombia", limit_per_cluster=limit_per_cluster)
    else:
        print("[*] Rastreador en vivo: Conectando con RemoteOK + Arbeitnow...", flush=True)
        jobs = job_scout.find_jobs(max_results=8)

    if not jobs:
        print("[!] No se encontraron vacantes para procesar.", flush=True)
        return

    print(f"\n[*] Analizando {len(jobs)} vacantes encontradas con Gemini (Umbral mínimo: {threshold}/100)...\n", flush=True)
    generated = 0

    for idx, j in enumerate(jobs, 1):
        print(f"[{idx}/{len(jobs)}] {j['company']} — '{j['title']}'", flush=True)
        
        # Obtener detalle completo de LinkedIn si está disponible
        desc_text = j.get("description", "")
        if j.get("job_id"):
            detail = job_scout.fetch_linkedin_job_detail(j["job_id"])
            if detail and len(detail) > 100:
                desc_text = detail

        # 1. Evaluar con Gemini
        eval_res = orch.evaluate_job(j["title"], j["company"], desc_text)
        if "error" in eval_res:
            print(f"    [!] Error en evaluación: {eval_res['error']}", flush=True)
            continue

        score = eval_res.get("fit_score", 0)
        track = eval_res.get("profile_track", "N/A")
        lang = eval_res.get("language_fit", "N/A")

        print(f"    -> Match: {score}/100 | Track: {track} | Idioma: {lang}", flush=True)

        if score < threshold:
            print(f"    [-] Descartada: Match {score} menor al umbral {threshold}.", flush=True)
            continue

        if lang == "RISK_C1_NATIVE_DEMANDED":
            print(f"    [-] Descartada: Exige inglés C1/Nativo excluyente (Protección B2 activa).", flush=True)
            continue

        # 2. Generar postulación adaptada
        print(f"    [+] ¡MATCH ALTO ({score}/100)! Adaptando CV STAR y Cover Letter...", flush=True)
        tailor_res = orch.tailor_application(j["title"], j["company"], desc_text, eval_res)
        if "error" in tailor_res:
            print(f"    [!] Error al redactar: {tailor_res['error']}", flush=True)
            continue

        safe_company = "".join(c for c in j["company"] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        pdf_path = os.path.join(output_dir, f"CV_Santiago_Ochoa_{safe_company}.pdf")
        cl_path = os.path.join(output_dir, f"Cover_Letter_{safe_company}.txt")

        build_pdf(CANDIDATE_HEADER, tailor_res, pdf_path)
        with open(cl_path, "w", encoding="utf-8") as f:
            f.write(tailor_res.get("cover_letter", ""))

        # 3. Guardar en SQLite
        app_id = job_tracker.add_application(
            company=j["company"],
            position=j["title"],
            track=track,
            fit_score=score,
            url=j.get("url", ""),
            notes=f"Auto-batch. Idioma: {lang}. Ángulo: {eval_res.get('suggested_angle', '')}"
        )
        print(f"    [OK] CV PDF generado: {pdf_path}", flush=True)
        print(f"    [OK] Guardado en SQLite (ID #{app_id})", flush=True)
        generated += 1

    print("\n" + "=" * 75, flush=True)
    print(f"🏁 Proceso en lote completado: {generated} postulaciones listas en 'output/'", flush=True)
    print("=" * 75, flush=True)

    # 4. Desplegar SQLite Tracker
    print("\n" + "=" * 95, flush=True)
    print("RESUMEN DE POSTULACIONES EN SQLITE (job_tracker.db):", flush=True)
    print("=" * 95, flush=True)
    apps = job_tracker.list_applications()
    print(f"{'ID':<4} | {'EMPRESA':<22} | {'CARGO':<28} | {'TRACK':<14} | {'FIT':<4} | {'ESTADO':<14} | {'FECHA'}", flush=True)
    print("-" * 95, flush=True)
    for a in apps:
        f_date = a.get('date_added', '')[:10] if a.get('date_added') else ''
        print(f"{a['id']:<4} | {a['company'][:22]:<22} | {a['position'][:28]:<28} | {a['track'][:14]:<14} | {a['fit_score']:<4} | {a['status']:<14} | {f_date}", flush=True)
    print("-" * 95, flush=True)

if __name__ == "__main__":
    execute_batch(source="multinationals", threshold=75, limit_per_cluster=2)
