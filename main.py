import nltk
nltk.download("punkt", quiet=True)

from newspaper import Article

#Newspaper3k

#180graus erro - não funciona com esse protótipo, 403 forbidden: site bloqueia o request padrão
#Conecta Piauí sucesso - prototipo simples funciona
#Meio Norte sucesso - prototipo simples funciona
#Hora Piauí sucesso mas necessita atenção a mais
#G1 Piauí sucesso - protótipo simples funciona
#G1 sucesso - protótipo simples funciona
#Cidade Verde erro - nao funciona com esse protótipo, 403 forbidden: site bloqueia o request padrão
#OitoMeia sucesso - protótipo simples funciona
#Portal AZ sucesso - protótipo simples funciona
#Boletim Brio sucesso - protótipo simples funciona
#GP1 sucesso - protótipo simples funciona

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

url = "https://180graus.com/na-politica/novo-salario-minimo-deve-gerar-impacto-superior-a-r-109-milhoes-nas-prefeituras-do-piaui-em-2026/"
data = extract_with_newspaper(url)

print("TITLE:", data["title"])
print("DATE :", data["publish_date"])
print("AUTH :", data["authors"])
print("\nTEXT (preview):\n", data["text"][:800])
