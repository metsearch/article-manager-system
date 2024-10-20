from schemas.article_schema import Article
from io import StringIO
import json 

buffer = StringIO()
print(json.dumps(Article.model_json_schema()), file=buffer)
buffer.seek(0)

article_summarizer_prompt = f"""
    you are an expert in summarizing articles. 
    you will generate a text describing the article in terms of field, subject, authors etc...
    the response must be in ENGLISH: and should respect the next JSON SCHEMA: 
    ###
    {buffer.read()}
    ###
    DO NOT ADD EXTRA INFORMATIONS
"""

if __name__ == '__main__':
    print(article_summarizer_prompt)