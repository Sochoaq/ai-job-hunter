import os
import json
import re
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Cargar variables de entorno si existen (.env)
load_dotenv()

class FitAnalysis(BaseModel):
    fit_score: int = Field(description="Puntuación de compatibilidad de 0 a 100")
    recommendation: str = Field(description="'APPLY_PRIORITY', 'APPLY_STANDARD', o 'SKIP'")
    matching_skills: List[str] = Field(description="Habilidades del candidato que coinciden directamente")
    missing_skills: List[str] = Field(description="Requerimientos que faltan o requieren explicación")
    key_talking_points: List[str] = Field(description="Puntos fuertes de Santiago a destacar en la postulación")
    suggested_angle: str = Field(description="Enfoque estratégico para la postulación")

def get_candidate_profile() -> str:
    profile_path = os.path.join(
        os.path.dirname(__file__),
        ".claude", "skills", "job-application-assistant", "01-candidate-profile.md"
    )
    if os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Santiago Alejandro Ochoa - Ingeniero de Proyectos | AI Engineering & Software"

class Orchestrator:
    """
    Orquestador Multi-Agente Híbrido:
    - Agente 1 (Scout & Matcher - Gemini): Evalúa vacantes masivas con Fit Score estructurado y bajo costo.
    - Agente 2 (CV & Cover Letter Tailor - Claude): Redacta adaptaciones quirúrgicas en Markdown / LaTeX.
    """
    def __init__(self):
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

    def evaluate_job_with_gemini(self, job_title: str, company: str, job_description: str) -> Dict[str, Any]:
        """
        Agente 1: Evaluación estructurada usando Gemini.
        """
        if not self.gemini_api_key:
            return {
                "error": "GEMINI_API_KEY no configurada. Por favor define GEMINI_API_KEY en tu entorno o en .env"
            }
        
        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_api_key)
            candidate_profile = get_candidate_profile()

            prompt = f"""
            Eres el 'Talent Matchmaker Agent' para Santiago Alejandro Ochoa Quesada.
            Tu misión es analizar la siguiente vacante con objetividad y rigor técnico frente a su perfil.

            --- PERFIL DEL CANDIDATO ---
            {candidate_profile}

            --- VACANTE A EVALUAR ---
            Empresa: {company}
            Cargo: {job_title}
            Descripción:
            {job_description}

            Devuelve un análisis estructurado de compatibilidad.
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
            return {"error": f"Error evaluando con Gemini: {str(e)}"}

    def tailor_application_with_claude(self, job_title: str, company: str, job_description: str, fit_analysis: Dict[str, Any]) -> Dict[str, str]:
        """
        Agente 2: Redacción y optimización ATS de alto impacto usando Claude.
        """
        if not self.anthropic_api_key:
            return {
                "error": "ANTHROPIC_API_KEY no configurada. Por favor define ANTHROPIC_API_KEY en tu entorno o en .env"
            }

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            candidate_profile = get_candidate_profile()

            prompt = f"""
            Eres el 'Senior ATS & Career Tailor Agent' para Santiago Alejandro Ochoa Quesada.
            Tu objetivo es redactar:
            1. Un 'Executive Summary' personalizado para el CV.
            2. 3 a 5 viñetas de experiencia laboral reenfocadas con métricas de impacto (STAR).
            3. Una carta de presentación persuasiva, técnica y directa (estilo cover letter moderna).

            --- PERFIL DEL CANDIDATO ---
            {candidate_profile}

            --- ANÁLISIS PREVIO DE MATCH ---
            {json.dumps(fit_analysis, indent=2)}

            --- VACANTE ---
            Empresa: {company}
            Cargo: {job_title}
            Descripción: {job_description}

            Responde en formato JSON con las claves: 'cv_summary', 'experience_bullet_points', 'cover_letter'.
            """

            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.content[0].text
            # Extraer bloque JSON si viene envuelto
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return {"raw_output": raw_text}
        except Exception as e:
            return {"error": f"Error redactando con Claude: {str(e)}"}

if __name__ == "__main__":
    print("Orquestador Híbrido Gemini + Claude inicializado correctamente.")
    print("Módulos listos: Agente Evaluador (Gemini) + Agente Redactor ATS (Claude).")
