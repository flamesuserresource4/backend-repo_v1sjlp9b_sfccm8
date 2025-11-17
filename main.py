import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db, create_document, get_documents
from schemas import Property

app = FastAPI(title="Isherwood Developments API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Isherwood Developments API running"}


class PropertyFilter(BaseModel):
    category: Optional[str] = None
    development_type: Optional[str] = None
    commercial_type: Optional[str] = None
    hospitality_type: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None


@app.get("/properties", response_model=List[dict])
def list_properties(
    category: Optional[str] = None,
    development_type: Optional[str] = None,
    commercial_type: Optional[str] = None,
    hospitality_type: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    """List properties with optional filters"""
    query = {}
    if category:
        query["category"] = category
    if development_type:
        query["development_type"] = development_type
    if commercial_type:
        query["commercial_type"] = commercial_type
    if hospitality_type:
        query["hospitality_type"] = hospitality_type
    if city:
        query["city"] = city
    if status:
        query["status"] = status

    props = get_documents("property", query, limit)
    # Convert ObjectId to string
    for p in props:
        p["id"] = str(p.pop("_id", ""))
    return props


@app.get("/properties/{slug}")
def get_property(slug: str):
    """Get a single property by slug"""
    doc = db["property"].find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Property not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.post("/properties", status_code=201)
def create_property(payload: Property):
    """Create a new property"""
    # Unique slug check
    existing = db["property"].find_one({"slug": payload.slug})
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")
    inserted_id = create_document("property", payload)
    return {"id": inserted_id}


class ChatRequest(BaseModel):
    message: str


@app.post("/properties/{slug}/chat")
def chat_about_property(slug: str, body: ChatRequest):
    """Very simple AI-like responder that answers from stored property data."""
    doc = db["property"].find_one({"slug": slug})
    if not doc:
        raise HTTPException(status_code=404, detail="Property not found")

    name = doc.get("name")
    category = doc.get("category")
    city = doc.get("city")
    status = doc.get("status")
    price = doc.get("price")
    size = doc.get("size_sqft")
    acres = doc.get("lot_acres")
    dev = doc.get("development_type")
    comm = doc.get("commercial_type")
    hosp = doc.get("hospitality_type")
    highlights = doc.get("highlights", [])

    # Heuristic responses
    q = (body.message or "").lower()
    lines: List[str] = []
    lines.append(f"You're asking about {name} in {city}. Here's what I can share:")

    if "price" in q or "cost" in q or "listing" in q:
        if price is not None:
            lines.append(f"- Current guidance price is ${price:,.0f}.")
        else:
            lines.append("- Pricing is available upon request.")

    if "size" in q or "square" in q or "sqft" in q:
        if size:
            lines.append(f"- Interior size is approx. {size:,.0f} sq ft.")
        if acres:
            lines.append(f"- Lot size is approx. {acres:.2f} acres.")

    if "zoning" in q or "use" in q or "type" in q:
        parts = []
        if category:
            parts.append(category.title())
        if dev:
            parts.append(dev.title())
        if comm:
            parts.append(comm.title())
        if hosp:
            parts.append(hosp.title())
        if parts:
            lines.append("- Property type: " + ", ".join(parts))

    if "status" in q or "available" in q:
        lines.append(f"- Status: {status.title() if status else 'Available'}")

    if not any(keyword in q for keyword in ["price","cost","listing","size","square","sqft","zoning","use","type","status","available"]):
        # General overview
        if highlights:
            lines.append("Key highlights:")
            for h in highlights[:5]:
                lines.append(f"  • {h}")
        if not highlights:
            lines.append("Let me know if you'd like details on price, size, zoning, or availability.")

    answer = "\n".join(lines)
    return {"reply": answer}


@app.post("/seed")
def seed_demo():
    """Seed sample properties if collection is empty"""
    count = db["property"].count_documents({})
    if count > 0:
        return {"message": "Collection already seeded", "count": count}

    samples: List[Property] = [
        Property(
            name="Isherwood Plaza",
            slug="isherwood-plaza",
            summary="Modern retail plaza with excellent frontage",
            description="A high-visibility retail plaza with ample parking and strong tenant mix.",
            address="123 Main St",
            city="Cambridge",
            province="ON",
            country="Canada",
            images=[],
            category="commercial",
            commercial_type="plaza",
            size_sqft=45000,
            lot_acres=3.5,
            year_built=2010,
            status="available",
            price=12500000,
            highlights=["Prime corner exposure","Ample surface parking","Strong traffic counts"],
        ),
        Property(
            name="Riverside Towers",
            slug="riverside-towers",
            summary="Waterfront high-rise residential development",
            description="Proposed twin-tower high rise with panoramic river views.",
            address="500 Riverside Dr",
            city="Kitchener",
            province="ON",
            country="Canada",
            images=[],
            category="development",
            development_type="high rise",
            size_sqft=None,
            lot_acres=2.2,
            year_built=None,
            status="under development",
            price=None,
            highlights=["Waterfront location","Transit adjacent","Zoning in progress"],
        ),
        Property(
            name="Isherwood Industrial Park",
            slug="isherwood-industrial-park",
            summary="Modern industrial bays with clear heights",
            description="Flex industrial with loading docks and ample marshalling.",
            address="200 Industry Rd",
            city="Guelph",
            province="ON",
            country="Canada",
            images=[],
            category="commercial",
            commercial_type="industrial",
            size_sqft=120000,
            lot_acres=8.0,
            status="available",
            price=28900000,
            highlights=["32' clear height","ESFR sprinklers","Multiple dock doors"],
        ),
        Property(
            name="Grandview Retirement Residence",
            slug="grandview-retirement-residence",
            summary="Thoughtfully designed retirement community",
            description="A full-service retirement home with wellness amenities.",
            address="88 Grandview Ave",
            city="Waterloo",
            province="ON",
            country="Canada",
            images=[],
            category="hospitality",
            hospitality_type="retirement",
            status="available",
            price=None,
            highlights=["On-site healthcare","Chef-led dining","Landscaped courtyards"],
        ),
    ]

    for p in samples:
        create_document("property", p)

    return {"message": "Seeded demo properties", "count": len(samples)}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, 'name', None) or "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
