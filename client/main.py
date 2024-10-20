import os
import streamlit as st
import arxiv
import httpx
import asyncio
from io import BytesIO

API_URL = 'http://localhost:8100/v1/article'

async def send_pdf_to_api(pdf_bytes: BytesIO, filename: str = "article.pdf"):
    async with httpx.AsyncClient() as client:
        files = {'file': (filename, pdf_bytes, 'application/pdf')}
        headers = {'accept': 'application/json'}
        response = await client.post(os.path.join(API_URL, 'add'), headers=headers, files=files)
        return response.json()

# Upload PDF to API manually
async def handle_manual_upload(uploaded_file: BytesIO):
    st.write("Processing uploaded article...")
    file_bytes = uploaded_file.read()
    response = await send_pdf_to_api(file_bytes)
    st.write(response)
    
# Upload PDF to API from arXiv
async def fetch_arxiv_articles(subject: str):
    client = arxiv.Client(
        page_size=10,
        delay_seconds=3,
        num_retries=3
    )

    search = arxiv.Search(
        query=subject,
        max_results=5,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    results_generator = client.results(search)
    
    tasks = []
    
    async with httpx.AsyncClient() as http_client:
        for result in results_generator:
            pdf_url = result.pdf_url
            st.write(f"Title: {result.title}")
            
            try:
                response = await http_client.get(pdf_url)
                pdf_bytes = BytesIO(response.content)

                task = send_pdf_to_api(pdf_bytes.getvalue(), result.get_short_id() + ".pdf")
                tasks.append(task)

            except Exception as e:
                st.error(f"Error fetching PDF for {result.title}: {str(e)}")

    if tasks:
        api_responses = await asyncio.gather(*tasks, return_exceptions=True)

        for api_response in api_responses:
            if isinstance(api_response, Exception):
                st.error(f"API error: {api_response}")
            else:
                st.write(api_response)
    else:
        st.warning("No articles were fetched.")
        
async def search_articles(query: str, nb_neighbors: int = 3):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "nb_neighbors": nb_neighbors,
        "query": query
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(os.path.join(API_URL, 'search'), headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            st.error(f"Error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            return None


st.title("Article Management System")

st.header("Add Article Manually")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
if uploaded_file is not None:
    asyncio.run(handle_manual_upload(uploaded_file))

st.header("Add 5 Random Articles from arXiv by Subject")
subject = st.text_input("Enter a subject for article search:")
if st.button("Fetch Random Articles"):
    asyncio.run(fetch_arxiv_articles(subject))

st.header("Search Articles")
search_query = st.text_input("Enter search query")
nb_neighbors = st.number_input("Number of articles:", min_value=1, max_value=10, value=3)

if st.button("Search"):
    if search_query:
        results = asyncio.run(search_articles(search_query, nb_neighbors))
        if results:
            st.write("Search Results:")
            st.json(results)
    else:
        st.warning("Please enter a query before searching.")
