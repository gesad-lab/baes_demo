from fastapi import APIRouter

router = APIRouter()

@router.get('/dummy')
def dummy():
    return {'hello': 'world'}
