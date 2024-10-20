import json
from uuid import uuid4
from PyPDF2 import PdfReader

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from log_handler.log import logger 

from typing import List

from mapper.mapper import Mapper 
from schemas.article_schema import Article
from settings.system_settings import article_summarizer_prompt

from qdrant_client import models

from schemas.search_schemas import SemanticSearchReq

class Article:
    def __init__(self, mapper:Mapper) -> None:
        self.router = APIRouter(
            prefix="/v1/article",
            tags=["Article"],
            responses={200: {"description": "Article router is used to add, get and delete articles in qdrant"}},
        )
        
        self.collection_name = 'articles_'
        self.mapper = mapper
        
        self.router.add_api_route("/add", endpoint=self.add_article, methods=["POST"])
        self.router.add_api_route("/get", endpoint=self.get_article, methods=["GET"])
        self.router.add_api_route("/search", endpoint=self.semantic_search, methods=["POST"])
    
    async def __create_collection(self):
        await self.mapper.shared_qdrant_client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE)
        )
        logger.debug(f'Collection `{self.collection_name}` successfully created')
                
    async def __extact_txt_from_pdf(self, file_path: str):
        reader = PdfReader(file_path)
        pages = [page.extract_text() for page in reader.pages]
        return '\n'.join(pages)
    
    async def __parse_article(self, text: str) -> dict:
        print('start..llm')
        completion_res = await self.mapper.shared_openai_client.chat.completions.create(
            messages=[
                {'role': 'system', 'content': article_summarizer_prompt},
                {'role': 'user', 'content': f'article: ###\n{text}\n###'}
            ],
            stream=False,
            model='gpt-4o-mini',
            response_format={'type': 'json_object'}   
        )
        print('end llm')
        json_doc = completion_res.choices[0].message.content.strip()
        mark0 = json_doc.index('{')
        mark1 = json_doc[-1::-1].index('}')
        json_doc = json_doc[mark0:len(json_doc) - mark1]
        return json.loads(json_doc)
                
    async def __add_vector(self, vector_id: str, metadata: dict) -> None:
        logger.debug(f'Checking for collection `{self.collection_name}`...')
        collection_found = await self.mapper.shared_qdrant_client.collection_exists(collection_name=self.collection_name)
        if not collection_found:    
            await self.__create_collection()
        else:
            logger.debug(f'Collection `{self.collection_name}` found!')
        
        summary = metadata['summary']
        summary_embeddings = await self.mapper.get_embedding(text=summary)
        await self.mapper.shared_qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=vector_id,
                    payload=metadata,
                    vector=summary_embeddings[:1024],
                ),
            ],
        )
    
    async def add_article(self, file: UploadFile = File()):
        article_id = str(uuid4())
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pdf files are accepted!"
            )
            
        try:
            article_text = await self.__extact_txt_from_pdf(file.file)
            article_metadata = await self.__parse_article(article_text)
            await self.__add_vector(article_id, article_metadata)
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "message": f"Article ({article_id}) of '{self.collection_name}' successfully created",
                }
            )
        except Exception as e:
            logger.error(f"Error while creating a record: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
        )
        
    async def get_article(self, article_id: str):
        try:
            result = await self.mapper.shared_qdrant_client.retrieve(
                collection_name=self.collection_name,
                ids=[article_id],
                with_payload=True,
                with_vectors=False
            )
            document = result[0]
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "article": document.payload
                }
            )
            
        except Exception as e:
            logger.error(f"Error while getting the article: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
            
    async def semantic_search(self, incoming_req:SemanticSearchReq):
        collection_found = await self.mapper.shared_qdrant_client.collection_exists(collection_name=self.collection_name)
        if not collection_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.collection_name} was not found, can not apply semantic search in this collection"
            )
            
        print("start..llm")
        completion_res = await self.mapper.shared_openai_client.chat.completions.create(
            messages=[
                {'role': 'system', 'content': "You are a query enricher, your role will be to analyze the query and generate a more complete query for an article search. DO NOT ADD ANY NEW INFORMATION, ONLY ENRICH THE QUERY."},
                {'role': 'user', 'content': f'{incoming_req.query}'}
            ],
            stream=False,
            model="gpt-4o-mini", 
        )
        print("end llm")
        enhanced_query = completion_res.choices[0].message.content
        logger.debug(enhanced_query)
        query_embedding = await self.mapper.get_embedding(
            text=enhanced_query
        )
        
        points = await self.mapper.shared_qdrant_client.query_points(
            collection_name=self.collection_name,
            query=query_embedding[:1024],
            limit=incoming_req.nb_neighbors
        )
        
        # return JSONResponse(
        #     status_code=status.HTTP_200_OK,
        #     content={
        #         "search_result": points
        #     }
        # )