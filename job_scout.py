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
        r"\b(linux sysadmin|infrastructure)\b"
    ],
    "HARDWARE_EMBEDDED": [
        r"\b(embedded systems?|embedded software|firmware)\b",
        r"\b(microcontroller|esp32|stm32|arm cortex)\b",
        r"\b(iot|internet of things|telemetry)\b",
        r"\b(hardware engineer|circuit design|pcb)\b",
        r"\b(c\+\+ developer|c/c\+\+)\b",
        r"\b(fpga|verilog|vhdl)\b"
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
    # El título y tags tienen mucho mayor peso que la descripción larga
    weighted_text = f"{title} {title} {' '.join(tags)} {' '.join(tags)} {desc[:400]}".lower()
    scores = {track: 0 for track in TRACK_PATTERNS}
    for track, patterns in TRACK_PATTERNS.items():
        for pat in patterns:
            matches = len(re.findall(pat, weighted_text))
            scores[track] += matches
    best_track = max(scores, key=scores.get)
    if scores[best_track] > 0:
        return best_track
    return ""

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
    results = find_jobs(max_results=6)
    for i, j in enumerate(results, 1):
        print(f"{i}. [{j['track_hint']}] {j['title']} @ {j['company']} ({j['location']})")
