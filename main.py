from fastapi import FastAPI
from apis.routers.router_get import get_router
from apis.routers.router_delete import delete_router
from apis.routers.patch_router import patch_router
from apis.routers.post_router import post_router
from auth.auth import register_router

app = FastAPI(title='JetBrains', version='1.0.0')

app.include_router(register_router, prefix='/accounts')
app.include_router(get_router, prefix='/main')
app.include_router(delete_router, prefix='/main')
app.include_router(patch_router, prefix='/main')
app.include_router(post_router, prefix='/main')
