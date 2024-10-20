import json
from uuid import uuid4
from PyPDF2 import PdfReader

from elasticsearch import NotFoundError

from fastapi import APIRouter, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from log_handler.log import logger 

from typing import List

from mapper.mapper import Mapper 
from schemas.article_schema import Article
from settings.system_settings import article_summarizer_prompt

from schemas.search_schemas import SemanticSearchReq

class Article:
    def __init__(self, mapper:Mapper) -> None:
        self.router = APIRouter(
            prefix="/v1/article",
            tags=["Article"],
            responses={200: {"description": "Article router is used to add, get and delete articles in elasticsearch"}},
        )
        
        self.index_name = 'articles_'
        self.mapper = mapper
        
        self.router.add_api_route("/add", endpoint=self.add_article, methods=["POST"])
        self.router.add_api_route("/get", endpoint=self.get_article, methods=["GET"])
        self.router.add_api_route("/search", endpoint=self.semantic_search, methods=["POST"])
        
    async def __create_index(self):
        logger.debug(f'Checking for index `{self.index_name}`...')
        index_schema = {
            'properties': {
                'id': {'type': 'keyword'}, 
                'summary_embeddings': {
                    'type': 'dense_vector',
                    'dims': 1024,
                    'index': True,
                    'similarity': 'cosine'
                },
                'summary': {'type': 'text'},
                'title': {'type': 'text'},
                'field': {'type': 'text'},
                "authors": {
                    "type": "nested",
                    "properties": {
                        "name": { "type": "text" },
                    }
                },
                'publication_date': {'type': 'text'}
            }
        }
        index_settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
        index_found = await self.mapper.shared_es_client.indices.exists(index=self.index_name)
        if index_found:
            logger.info('Index found!')
        else:
            try:
                await self.mapper.shared_es_client.indices.create(
                    index=self.index_name,
                    mappings=index_schema,
                    settings=index_settings,
                )
                logger.info('Index successfully created!')
            except Exception as e:
                logger.error(f'Error while creating an index: {str(e)}')
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )
                
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
                
    async def __create_record(self, doc_id: str, metadata: dict) -> None:
        await self.__create_index()
        summary = metadata['summary']
        summary_embeddings = await self.mapper.get_embedding(text=summary)
        metadata['summary_embeddings'] = summary_embeddings
        index_res = await self.mapper.shared_es_client.index(
            index=self.index_name,
            id=doc_id,
            document=metadata
        )
        return dict(index_res)
    
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
            await self.__create_record(article_id, article_metadata)
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Error while creating a record: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
        )
        
    async def get_article(self, article_id:str):
        try:
            res = await self.mapper.shared_es_client.get(
                index=self.index_name,
                id=article_id
            )
            del res['_source']['article_summary_embedding']
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "article": res['_source']  
                }
            )
            
        except Exception as e:
            logger.error(f"Error while getting the article: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    # async def get_all_articles(self):
    #     try:
    #         res = await self.mapper.shared_es_client.search(
    #             index=self.index_name,
    #             body={
    #                 "query": {
    #                     "match_all": {}
    #                 }
    #             }
    #         )
    #         return JSONResponse(
    #             status_code=status.HTTP_200_OK,
    #             content={
    #                 "result": res['hits']['hits']
    #             }
    #         )
    #     except Exception as e:
    #         logger.error(f"Error while getting all articles: {str(e)}")
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail=str(e)
    #         )
    
    # async def delete_article(self, article_id:str):
    #     try:
    #         await self.mapper.shared_es_client.delete(
    #             index=self.index_name,
    #             id=article_id
    #         )
    #         return JSONResponse(
    #             status_code=status.HTTP_200_OK,
    #             content={
    #                 "message": f"Article ({article_id}) of '{self.index_name}' successfully deleted",
    #             }
    #         )
    #     except NotFoundError as e:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail=str(e)
    #         )
    #     except Exception as e:
    #         logger.error(f"Error while deleting article: {str(e)}")
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail=str(e)
    #         )
            
            
    def semantic_search(self):
        async def _inner_search(incoming_req:SemanticSearchReq):
            index_found = await self.mapper.shared_es_client.indices.exists(index=incoming_req.index)
            if not index_found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{incoming_req.index} was not found, can not apply semantic search the index"
                ) 
            
            print("start..llm")
            completion_res = await self.mapper.shared_openai_client.chat.completions.create(
                messages=[
                    {'role': 'system', 'content': "Tu es un enrichisseur de requête, ton role sera d'analyser la requete et de générer le profile ideal. exemple: je recherche un ingénieir en deep learning, tu dois créer un paragraph ou le candidat ideal decrit ses competence technique"},
                    {'role': 'user', 'content': f'{incoming_req.query}'}
                ],
                stream=False,
                model="gpt-3.5-turbo-0125" 
            )
            print("end llm")
            enhanced_query = completion_res.choices[0].message.content
            print(enhanced_query)
            query_embedding = await self.mapper.get_embedding(
                text=enhanced_query
            )
            dsl_query_hmap = {
                "index": incoming_req.index,
                "query":{
                    "script_score": {
                        "query" : {
                           "match_all": {}
                        },
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'text_summary_embedding') + 1.0",
                            "params": {
                                "query_vector": query_embedding 
                            }
                        }
                    }
                },
                "sort": [
                    {
                        "_score":{
                            "order": "desc"
                        }
                    }
                ]
            }
            search_res = await self.mapper.shared_es_client.search(**dsl_query_hmap)
            print("nb responses", len(search_res['hits']['hits']))
            accumulator:List[Candidate] = []
            for hit in search_res['hits']['hits'][:incoming_req.nb_neighbors]:
                del hit['_source']['text_summary_embedding']
                item = Candidate(**hit['_source'])
                accumulator.append(item)
                print(json.dumps(hit, indent=3))

            return accumulator
        return _inner_search