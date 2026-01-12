import nltk
nltk.download("punkt", quiet=True)

# instalar dependências e ambiente conda

#Newspaper3k

#180graus erro - 403 forbidden: o site impede os requests do protótipo incial 
#Conecta Piauí sucesso
#Meio Norte sucesso
#Hora Piauí sucesso mas requer atenção - não extrai todos os dados necessários
#G1 Piauí sucesso
#G1 sucesso
#Cidade Verde erro - 403 forbidden: o site impede os requests do protótipo incial 
#OitoMeia sucesso
#Portal AZ sucesso
#Boletim Brio sucesso
#GP1 sucesso

from newspaper import Article

def extract_with_newspaper(url: str, language: str = "pt"):
    a = Article(url, language=language)
    a.download()
    a.parse()
    # tenta pegar algumas infos extras quando disponíveis
    a.nlp()
    return {
        "url": url,
        "title": a.title,
        "authors": a.authors,
        "publish_date": a.publish_date.isoformat() if a.publish_date else None,
        "text": a.text,
        "top_image": a.top_image,
        "keywords": getattr(a, "keywords", None),
        "summary": getattr(a, "summary", None),
    }

url = "<URL DA MATERIA>"
data = extract_with_newspaper(url)

print("TITLE:", data["title"])
print("DATE :", data["publish_date"])
print("AUTH :", data["authors"])
print("\nTEXT (preview):\n", data["text"][:800])
