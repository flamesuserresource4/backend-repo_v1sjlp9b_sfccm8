"""
Database Schemas for Isherwood Developments
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class Property(BaseModel):
    name: str = Field(..., description="Property name")
    slug: str = Field(..., description="URL-friendly identifier")
    summary: str = Field(..., description="Short overview")
    description: str = Field(..., description="Detailed description")
    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    province: str = Field(..., description="Province/State")
    country: str = Field("Canada", description="Country")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    category: Literal['land','residential','commercial','development','hospitality']
    development_type: Optional[Literal['high rise','mid rise','low rise']] = None
    commercial_type: Optional[Literal['plaza','office','medical','industrial']] = None
    hospitality_type: Optional[Literal['hotel','apartment','retirement']] = None
    size_sqft: Optional[float] = Field(None, ge=0)
    lot_acres: Optional[float] = Field(None, ge=0)
    year_built: Optional[int] = None
    status: Literal['available','leased','sold','under development'] = 'available'
    price: Optional[float] = Field(None, ge=0)
    highlights: List[str] = Field(default_factory=list)
    coordinates: Optional[dict] = None  # {lat, lng}

class ChatMessage(BaseModel):
    property_id: str = Field(..., description="Related property id")
    role: Literal['user','assistant']
    content: str
