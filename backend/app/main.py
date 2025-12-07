from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "message": "Workflow Manager API",
        "docs": f"{settings.API_V1_PREFIX}/docs"
    }


# Include routers
from app.api.v1 import projects, workflows, documents, rags
app.include_router(projects.router, prefix=f"{settings.API_V1_PREFIX}/projects", tags=["projects"])
app.include_router(workflows.router, prefix=f"{settings.API_V1_PREFIX}/workflows", tags=["workflows"])
app.include_router(documents.router, prefix=f"{settings.API_V1_PREFIX}/documents", tags=["documents"])
app.include_router(rags.router, prefix=f"{settings.API_V1_PREFIX}/rags", tags=["rags"])
