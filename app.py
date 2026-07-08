from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tariffs import TARIFFS_WB, TARIFFS_OZON, DEFAULT_TAX, AVERAGE_STORAGE_DAYS

app = FastAPI(title="SellerPilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CalculationRequest(BaseModel):
    marketplace: str = "WB"
    sku: str
    purchase_price: float
    selling_price: float
    category: str
    discount: float = 0.0
    buyout_percent: float = 100.0
    tax_rate: float = DEFAULT_TAX

class CalculationResponse(BaseModel):
    sku: str
    revenue_after_discount: float
    commission_amount: float
    logistics_amount: float
    storage_amount: float
    tax_amount: float
    total_costs: float
    net_profit: float
    roi: float
    verdict: str

@app.post("/calculate", response_model=CalculationResponse)
async def calculate(request: CalculationRequest):
    tariffs = TARIFFS_WB if request.marketplace.upper() == "WB" else TARIFFS_OZON
    cat = tariffs.get(request.category, {"logistics": 70, "storage_per_day": 0.10, "commission": 18})

    revenue_after_discount = request.selling_price * (1 - request.discount / 100) * (request.buyout_percent / 100)
    commission_amount = revenue_after_discount * (cat["commission"] / 100)
    logistics_amount = cat["logistics"]
    storage_amount = cat["storage_per_day"] * AVERAGE_STORAGE_DAYS
    tax_amount = revenue_after_discount * (request.tax_rate / 100)
    total_costs = request.purchase_price + commission_amount + logistics_amount + storage_amount + tax_amount
    net_profit = revenue_after_discount - total_costs
    roi = (net_profit / total_costs * 100) if total_costs > 0 else 0

    if roi > 20:
        verdict = "🚀 Отлично"
    elif roi > 0:
        verdict = "👍 Нормально"
    else:
        verdict = "❌ Убыток"

    return CalculationResponse(
        sku=request.sku,
        revenue_after_discount=round(revenue_after_discount, 2),
        commission_amount=round(commission_amount, 2),
        logistics_amount=round(logistics_amount, 2),
        storage_amount=round(storage_amount, 2),
        tax_amount=round(tax_amount, 2),
        total_costs=round(total_costs, 2),
        net_profit=round(net_profit, 2),
        roi=round(roi, 2),
        verdict=verdict
    )

app.mount("/", StaticFiles(directory="static", html=True), name="static")