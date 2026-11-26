from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

DOCS = {
    "mexico": "Mexico (Spanish): CV of 1-2 pages. Headings: Datos personales, Experiencia laboral, Formacion academica, Habilidades, Idiomas. Dates as month/year. Formal tone. A photo and personal details are common but optional.",
    "spain": "Spain (Spanish): CV of 1-2 pages. Headings: Experiencia profesional, Formacion, Idiomas, Informatica. Dates as mm/aaaa. Formal tone. A photo is common but optional.",
    "france": "France (French): CV of 1 page preferred. Headings: Experience professionnelle, Formation, Competences, Langues, Centres d'interet. Dates as mm/aaaa. Formal tone. Photo optional.",
    "germany": "Germany (German): Lebenslauf, tabular, reverse chronological, 1-2 pages. Headings: Berufserfahrung, Ausbildung, Kenntnisse, Sprachen. Dates as MM/JJJJ. Photo common but optional.",
    "brazil": "Brazil (Portuguese): CV of 1-2 pages. Headings: Experiencia Profissional, Formacao Academica, Habilidades, Idiomas. Dates as mm/aaaa. Photo optional.",
    "usa": "USA (English): resume of 1 page typical. Headings: Summary, Experience, Skills, Education. Dates as Mon YYYY. No photo, date of birth or marital status. Achievement-focused bullets with metrics.",
    "uk": "UK (English, British spelling): CV of 2 pages. Headings: Personal Statement, Work Experience, Education, Skills. Dates as Mon YYYY. No photo or date of birth.",
    "india": "India (English): resume of 1-2 pages. Headings: Summary, Experience, Skills, Education, Certifications. Photo and personal details usually not required.",
}

COLLECTION = "hiring_conventions"
_embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
_client = QdrantClient(":memory:")


def _embed(texts):
    return [v.tolist() for v in _embedder.embed(texts)]


_keys = list(DOCS)
_vecs = _embed([DOCS[k] for k in _keys])
_client.create_collection(
    COLLECTION,
    vectors_config=VectorParams(size=len(_vecs[0]), distance=Distance.COSINE),
)
_client.upsert(
    COLLECTION,
    points=[
        PointStruct(id=i, vector=_vecs[i], payload={"market": k, "text": DOCS[k]})
        for i, k in enumerate(_keys)
    ],
)


def search_conventions(query: str, n: int = 2) -> str:
    q = _embed([query])[0]
    res = _client.query_points(COLLECTION, query=q, limit=n).points
    return "\n".join(p.payload["text"] for p in res)