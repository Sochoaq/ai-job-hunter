import os
import sys
import json
import re
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

def get_api_key(name: str) -> str:
    # 1. Variable de entorno actual
    key = os.environ.get(name)
    if key:
        return key
    # 2. Registro de Windows (User Environment)
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
                val, _ = winreg.QueryValueEx(k, name)
                if val:
                    return val
        except Exception:
            pass
    return ""

class FitAnalysis(BaseModel):
    fit_score: int = Field(description="Puntuación de compatibilidad de 0 a 100")
    recommendation: str = Field(description="'APPLY_PRIORITY', 'APPLY_STANDARD', o 'SKIP'")
    profile_track: str = Field(description="Track detectado: 'AI_ENGINEERING', 'CLOUD_DEVOPS', o 'HARDWARE_EMBEDDED'")
    matching_skills: List[str] = Field(description="Habilidades del candidato que coinciden directamente")
    missing_skills: List[str] = Field(description="Requerimientos que faltan o requieren explicación")
    key_talking_points: List[str] = Field(description="Puntos fuertes de Santiago a destacar en la postulación")
    suggested_angle: str = Field(description="Enfoque estratégico para la postulación")

class TailoredApplication(BaseModel):
    cv_summary: str = Field(description="Resumen profesional adaptado a la vacante (3-4 líneas)")
    tailored_experience: List[str] = Field(description="Viñetas STAR con métricas enfocadas en el rol")
    tailored_projects: List[Dict[str, str]] = Field(description="Proyectos más relevantes con stack ajustado")
    cover_letter: str = Field(description="Carta de presentación persuasiva y técnica en el idioma de la vacante")

def get_candidate_profile() -> str:
    profile_path = os.path.join(
        os.path.dirname(__file__),
        ".claude", "skills", "job-application-assistant", "01-candidate-profile.md"
    )
    if os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Santiago Alejandro Ochoa - Ingeniero de Proyectos | AI, Cloud & Hardware Systems"

class Orchestrator:
    def __init__(self):
        self.gemini_api_key = get_api_key("GEMINI_API_KEY")
        self.anthropic_api_key = get_api_key("ANTHROPIC_API_KEY")

    def evaluate_job(self, job_title: str, company: str, job_description: str) -> Dict[str, Any]:
        """Agente Evaluador con Gemini: clasifica y calcula match multi-perfil (AI, Cloud, Hardware)."""
        if not self.gemini_api_key:
            return {"error": "GEMINI_API_KEY no encontrada."}
        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_api_key)
            profile = get_candidate_profile()

            prompt = f"""
            Eres el 'Talent Matchmaker Agent' para Santiago Alejandro Ochoa Quesada.
            Santiago está abierto y calificado para tres verticales principales:
            1. AI Engineering (Machine Learning, Computer Vision, Signal DSP, MLOps, PyTorch).
            2. Cloud & Systems Engineering (AWS, Linux, Docker, CI/CD, Data Pipelines, QA).
            3. Hardware & Embedded Engineering (ESP32, C/C++, Sensores, Telemetría, Circuitos).

            --- PERFIL DEL CANDIDATO ---
            {profile}

            --- VACANTE A EVALUAR ---
            Empresa: {company}
            Cargo: {job_title}
            Descripción:
            {job_description}

            Evalúa la vacante, identifica el track dominante y calcula el fit score.
            """
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=dict(
                    response_mime_type="application/json",
                    response_schema=FitAnalysis,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            return {"error": f"Error evaluando vacante: {str(e)}"}

    def tailor_application(self, job_title: str, company: str, job_description: str, fit_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Agente Redactor: adapta CV y Cover Letter destacando el track exacto de la vacante."""
        if not self.gemini_api_key:
            return {"error": "GEMINI_API_KEY no encontrada."}
        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_api_key)
            profile = get_candidate_profile()

            prompt = f"""
            Eres un 'ATS Resume & Cover Letter Tailor' de clase mundial para Santiago Alejandro Ochoa Quesada.
            Tu misión es generar una postulación adaptada, persuasiva y técnica orientada a superar filtros ATS y convencer al Hiring Manager.

            --- PERFIL DEL CANDIDATO ---
            {profile}

            --- EVALUACIÓN Y TRACK DETECTADO ---
            {json.dumps(fit_analysis, indent=2, ensure_ascii=False)}

            --- VACANTE ---
            Empresa: {company}
            Cargo: {job_title}
            Descripción:
            {job_description}

            Genera:
            1. cv_summary: Resumen profesional de 3-4 líneas alineado al rol.
            2. tailored_experience: 4 viñetas STAR con contexto industrial, acciones técnicas y métricas.
            3. tailored_projects: 2 proyectos clave con el stack exacto.
            4. cover_letter: Carta de presentación impecable (en inglés si la oferta es en inglés, o en español).
            """
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=dict(
                    response_mime_type="application/json",
                    response_schema=TailoredApplication,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            return {"error": f"Error redactando postulación: {str(e)}"}

if __name__ == "__main__":
    print("Orquestador Multi-Perfil (AI, Cloud & Hardware) listo.")
