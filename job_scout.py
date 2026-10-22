import re
import sys
import requests
from typing import List, Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TRACK_PATTERNS = {
    "AI_ENGINEERING": [
        r"\b(ai|artificial intelligence)\b",
        r"\b(machine learning|deep learning)\b",
        r"\b(computer vision|opencv|yolo)\b",
        r"\b(pytorch|tensorflow|scikit-learn)\b",
        r"\b(mlops|llm|nlp|data science)\b"
    ],
    "CLOUD_DEVOPS": [
        r"\b(cloud engineer|cloud architect)\b",
        r"\b(devops|devsecops|sre)\b",
        r"\b(aws|amazon web services)\b",
        r"\b(docker|kubernetes|k8s)\b",
        r"\b(ci/cd|github actions|gitlab ci)\b",
        r"\b(backend developer|backend engineer)\b",
        r"\b(python developer|python engineer)\b",
        r"\b(linux sysadmin|infrastructure)\b",
        r"\b(ciberseguridad|cybersecurity|security engineer)\b"
    ],
    "HARDWARE_EMBEDDED": [
        r"\b(embedded systems?|embedded software|firmware)\b",
        r"\b(microcontroller|esp32|stm32|arm cortex)\b",
        r"\b(iot|internet of things|telemetry)\b",
        r"\b(hardware engineer|circuit design|pcb)\b",
        r"\b(c\+\+ developer|c/c\+\+)\b",
        r"\b(fpga|verilog|vhdl)\b",
        r"\b(plc|automatizaci[oó]n|scada|control industrial)\b",
        r"\b(instrumentaci[oó]n|field engineer|ingeniero de proyectos)\b"
    ]
}

DISQUALIFYING_PATTERNS = [
    r"\b(german|deutsch|fließend deutsch|deutschkenntnisse)\b",
    r"\b(french|français)\b",
    r"\b(c1|c2|native english only|native english speaker mandatory)\b"
]

def clean_html(raw_html: str) -> str:
    """Elimina etiquetas HTML de la descripción de la vacante."""
    if not raw_html:
        return ""
    clean = re.sub(r"<[^>]+>", " ", raw_html)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

def is_disqualified(text: str) -> bool:
    text_lower = text.lower()
    for pat in DISQUALIFYING_PATTERNS:
        if re.search(pat, text_lower):
            return True
    return False

def detect_track(title: str, tags: List[str], desc: str) -> str:
    """Determina qué track coincide con mayor peso en el título y tags."""
    weighted_text = f"{title} {title} {' '.join(tags)} {' '.join(tags)} {desc[:400]}".lower()
    scores = {track: 0 for track in TRACK_PATTERNS}
    for track, patterns in TRACK_PATTERNS.items():
        for pat in patterns:
            matches = len(re.findall(pat, weighted_text))
            scores[track] += matches
    best_track = max(scores, key=scores.get)
    if scores[best_track] > 0:
        return best_track
    return "HARDWARE_EMBEDDED" if any(w in weighted_text for w in ["proyecto", "automatizacion", "control"]) else "AI_ENGINEERING"

def scout_linkedin_jobs(query: str, location: str = "Bogota, Colombia", limit: int = 10) -> List[Dict[str, Any]]:
    """Consulta la API pública guest de LinkedIn para Colombia/Bogotá."""
    jobs = []
    try:
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={query.replace(' ', '+')}&location={location.replace(' ', '+')}&start=0"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
        }
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            titles = re.findall(r'<h3[^>]*base-search-card__title[^>]*>(.*?)</h3>', res.text, re.DOTALL)
            companies = re.findall(r'<h4[^>]*base-search-card__subtitle[^>]*>(.*?)</h4>', res.text, re.DOTALL)
            links = re.findall(r'<a[^>]*class="base-card__full-link[^"]*"[^>]*href="([^"]+)"', res.text)
            locs = re.findall(r'<span[^>]*class="job-search-card__location"[^>]*>(.*?)</span>', res.text, re.DOTALL)

            for i in range(min(len(titles), len(companies))):
                t = clean_html(titles[i])
                c = clean_html(companies[i])
                l = links[i].split("?")[0] if i < len(links) else ""
                loc = clean_html(locs[i]) if i < len(locs) else location

                # Extraer Job ID de LinkedIn para posible detalle
                job_id_match = re.search(r'-(\d+)$', l)
                job_id = job_id_match.group(1) if job_id_match else ""

                track = detect_track(t, [c], "")
                jobs.append({
                    "source": "LinkedIn (Multinacional)",
                    "title": t,
                    "company": c,
                    "url": l,
                    "job_id": job_id,
                    "location": loc,
                    "track_hint": track,
                    "description": f"Vacante de {t} en la multinacional {c} ({loc}). Enlace de postulación directa: {l}"
                })
                if len(jobs) >= limit:
                    break
    except Exception as e:
        print(f"[!] Error consultando LinkedIn para '{query}': {e}")
    return jobs

def fetch_linkedin_job_detail(job_id: str) -> str:
    """Obtiene la descripción completa de una vacante de LinkedIn."""
    if not job_id:
        return ""
    try:
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return clean_html(res.text)
    except Exception:
        pass
    return ""

def scout_multinationals(location: str = "Bogota, Colombia", limit_per_cluster: int = 5) -> List[Dict[str, Any]]:
    """
    Busca vacantes en multinacionales líderes en Colombia y Latinoamérica
    alineadas con los 3 perfiles técnicos de Santiago.
    """
    print(f"[*] Rastreador de Multinacionales activo para: {location}...")
    clusters = [
        "Siemens OR Schneider OR ABB OR GEA OR Tetra Pak",
        "Mastercard OR Unisys OR Inetum OR IBM OR Cisco Ciberseguridad",
        "Mercado Libre OR Globant OR Oracle Cloud",
        "Ingeniero de Proyectos Industriales CAPEX Automatizacion",
        "Quala OR Bavaria OR CasaLuker Proyectos"
    ]

    all_jobs = []
    seen_urls = set()

    for q in clusters:
        cluster_jobs = scout_linkedin_jobs(q, location=location, limit=limit_per_cluster)
        for j in cluster_jobs:
            if j["url"] and j["url"] not in seen_urls:
                seen_urls.add(j["url"])
                all_jobs.append(j)

    print(f"[OK] Se encontraron {len(all_jobs)} ofertas vigentes de multinacionales.")
    return all_jobs

def scout_remoteok(limit: int = 30) -> List[Dict[str, Any]]:
    """Obtiene vacantes tecnológicas remotas desde RemoteOK."""
    jobs = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get("https://remoteok.com/api", headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for item in data:
                if not isinstance(item, dict) or "position" not in item:
                    continue
                title = item.get("position", "")
                company = item.get("company", "")
                tags = item.get("tags", [])
                desc = clean_html(item.get("description", ""))
                url = item.get("url") or item.get("apply_url") or f"https://remoteok.com/l/{item.get('id', '')}"
                location = item.get("location", "Remote")

                combined = f"{title} {' '.join(tags)} {desc}"
                if is_disqualified(combined):
                    continue

                track = detect_track(title, tags, desc)
                if track:
                    jobs.append({
                        "source": "RemoteOK",
                        "title": title,
                        "company": company,
                        "url": url,
                        "location": location,
                        "tags": tags,
                        "track_hint": track,
                        "description": desc
                    })
                if len(jobs) >= limit:
                    break
    except Exception as e:
        print(f"[!] Error explorando RemoteOK: {e}")
    return jobs

def scout_arbeitnow(limit: int = 30) -> List[Dict[str, Any]]:
    """Obtiene vacantes tecnológicas remotas desde Arbeitnow."""
    jobs = []
    try:
        res = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=10)
        if res.status_code == 200:
            items = res.json().get("data", [])
            for item in items:
                title = item.get("title", "")
                company = item.get("company_name", "")
                tags = item.get("tags", [])
                desc = clean_html(item.get("description", ""))
                url = item.get("url", "")
                location = item.get("location", "Remote")
                is_remote = item.get("remote", False)

                if not is_remote:
                    continue

                combined = f"{title} {' '.join(tags)} {desc}"
                if is_disqualified(combined):
                    continue

                track = detect_track(title, tags, desc)
                if track:
                    jobs.append({
                        "source": "Arbeitnow",
                        "title": title,
                        "company": company,
                        "url": url,
                        "location": location,
                        "tags": tags,
                        "track_hint": track,
                        "description": desc
                    })
                if len(jobs) >= limit:
                    break
    except Exception as e:
        print(f"[!] Error explorando Arbeitnow: {e}")
    return jobs

def find_jobs(max_results: int = 20) -> List[Dict[str, Any]]:
    """Explora bolsas de empleo remotas y consolida vacantes filtradas."""
    print("[*] Explorando ofertas remotas en RemoteOK y Arbeitnow...")
    all_jobs = []
    all_jobs.extend(scout_remoteok(limit=max_results // 2))
    all_jobs.extend(scout_arbeitnow(limit=max_results // 2))
    print(f"[OK] Se encontraron {len(all_jobs)} ofertas potenciales alineadas a tus tracks.")
    return all_jobs

if __name__ == "__main__":
    results = scout_multinationals(limit_per_cluster=2)
    for i, j in enumerate(results, 1):
        print(f"{i}. [{j['track_hint']}] {j['title']} @ {j['company']} ({j['location']})")
