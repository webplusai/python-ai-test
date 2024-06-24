from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, UUID4
from uuid import uuid4, UUID
from fastapi.responses import JSONResponse
from io import BytesIO
import requests
import PyPDF2
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(root_path="/api")

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Location(BaseModel):
    id: UUID = uuid4()
    name: str
    description: Optional[str] = None
    country_code: Optional[str] = None
    address: Optional[str] = None


class Product(BaseModel):
    id: UUID = uuid4()
    name: str
    description: Optional[str] = None
    hs_code: Optional[str] = None
    image_url: Optional[str] = None
    location: Optional[Location] = None
    weight_kg: Optional[float] = None
    recycled_pct: Optional[float] = None
    waste_pct: Optional[float] = None
    lifetime_amount: Optional[float] = None
    materials: List["Product"] = []

products = [
    Product(
        id='0a9f9b42-6b65-47b7-833b-cd3f8c6d64a0',
        name='Organic Cotton Fine Knit Beanie',
        description='Made from 100% organic cotton with fine knit texture for added comfort. Perfect for sustainable fashion choices.',
        hs_code='650500',
        image_url='https://beechfieldbrands.com/images/b51n.jpg',
        location=Location(
            id='7a6cf93c-ccfb-464f-8970-3c9f8b03b758',
            name='Beechfield Brands Warehouse',
            description='Main storage and distribution center',
            country_code='UK',
            address='1234 Beanie Lane, Manchester, M1 2AB'
        ),
        weight_kg=0.1,
        recycled_pct=30,
        waste_pct=5,
        lifetime_amount=2,
        materials=[
            Product(
                id='166e8b08-0c9e-44bc-95e2-d33b501b19d5',
                name='Organic Cotton Yarn',
                hs_code='520100',
                image_url='https://example.com/images/yarn.jpg',
                location=Location(
                    id='c272ed68-84f7-405c-aab6-d7f3b2904b2b',
                    name='Organic Cotton Supplier',
                    description='Yarn supplier',
                    country_code='IN',
                    address='5678 Yarn Street, Coimbatore, TN'
                ),
                weight_kg=0.05,
                recycled_pct=50,
                waste_pct=2,
                lifetime_amount=5
            )
        ]
    )
]

class ExtractProduct(BaseModel):
    pdf_file: Optional[UploadFile] = File(None)  # For uploading PDF file
    large_text: Optional[str] = None  # Large text input
    url: Optional[str] = None  # URL input

class ExtractProductURL(BaseModel):
    url: str

class ExtractProductText(BaseModel):
    large_text: str

class ExtractProductPDF(BaseModel):
    pdf_file: UploadFile = File(...)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/products")
async def get_products():
    products_dict = [product.dict() for product in products]
    for product in products_dict:
        product['id'] = str(product['id'])
        if product.get('location'):
            product['location']['id'] = str(product['location']['id'])
        for material in product['materials']:
            material['id'] = str(material['id'])
            if material.get('location'):
                material['location']['id'] = str(material['location']['id'])
    return JSONResponse(content={"data": products_dict, "total": len(products)})


@app.post("/products/extract/url", response_model=Product)
async def extract_product_from_url(item: ExtractProductURL):
    product_data = await extract_from_url(item.url)
    if not product_data:
        raise HTTPException(status_code=400, detail="Failed to extract product data from URL")

    product = Product(**product_data)
    products.append(product)
    return product

@app.post("/products/extract/text", response_model=Product)
async def extract_product_from_text(item: ExtractProductText):
    product_data = await extract_from_text(item.large_text)
    if not product_data:
        raise HTTPException(status_code=400, detail="Failed to extract product data from text")

    product = Product(**product_data)
    products.append(product)
    return product

@app.post("/products/extract/pdf", response_model=Product)
async def extract_product_from_pdf(pdf_file: UploadFile = File(...)):
    product_data = await extract_from_pdf(pdf_file)
    print(product_data)
    if not product_data:
        raise HTTPException(status_code=400, detail="Failed to extract product data from PDF")

    product = Product(**product_data)
    products.append(product)
    return product


async def extract_from_url(url: str):
    try:
        return await parse_product_data_from_url(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def extract_from_pdf(pdf_file: UploadFile):
    # Read PDF contents
    pdf_data = await pdf_file.read()
    
    # Parse PDF using PdfReader from PyPDF2
    pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_data))
    
    # Extract text from PDF (assuming single page PDF for simplicity)
    page_text = ""
    for page_num in range(len(pdf_reader.pages)):
        page_text += pdf_reader.pages[page_num].extract_text()
    try:
        return await parse_product_data_from_text(page_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def extract_from_text(large_text: str):
    try:
        return await parse_product_data_from_text(large_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def parse_product_data_from_url(url: str):
    prompt = f"""
    Read the following url and extract the product details in JSON format from the following url:
    \n\n{url}\n\n
    Expected JSON structure: 
    {{'name': str, 'description': str, 'hs_code': str, 'image_url': str, 'location': 
    {{'name': str, 'description': str, 'country_code': str, 'address': str}}, 
    'weight_kg': float, 'recycled_pct': float, 'waste_pct': float, 'lifetime_amount': float, 'materials': list of product}}
    \n\nIf any information of product, location, materials is missing, please guess suitable values.
    \n\n object of materials must be product object"""

    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(prompt)
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": "gpt-3.5-turbo-0125",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": 0.7,
            },
        )
        product_data = response.json()["choices"][0]["message"]["content"].strip()
        return eval(product_data)
    except Exception as e:
        print("An error occurred:", e)
        return ""

async def parse_product_data_from_text(text: str):
    prompt = f"""
    Extract the product details in JSON format from the following text:
    \n\n{text}\n\n
    Expected JSON structure: 
    {{'name': str, 'description': str, 'hs_code': str, 'image_url': str, 'location': 
    {{'name': str, 'description': str, 'country_code': str, 'address': str}}, 
    'weight_kg': float, 'recycled_pct': float, 'waste_pct': float, 'lifetime_amount': float, 'materials': list}}
    \n\nIf any information of product, location, materials is missing, please guess suitable values.
    \n\nIf there is url inside provided text, please read that url and extract based on that read data
    \n\n object of materials must be product object"""

    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(prompt)
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": "gpt-3.5-turbo-0125",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": 0.7,
            },
        )
        product_data = response.json()["choices"][0]["message"]["content"].strip()
        return eval(product_data)
    except Exception as e:
        print("An error occurred:", e)
        return ""
