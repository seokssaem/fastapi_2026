'''
========================================================================================
routers/ml.py

카테고리 예측 모델의 "정확도"를 확인할 수 있는 모니터링 전용 엔드포인트

MLOps 핵심 개념--> 모델을 배포하고 끝! 이 아니라, 배포 후에도 계속 지켜본다(모니터링)는 것이
        이 파일의 존재 이유.
        실무에서는 정확도가 서서히 떨어지는 현상 (model drift)을 감지하기 위해 
        이런 모니터링 지표를 반드시 별도로 관리한다.
========================================================================================
'''
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from starlette import status

from database.db_connection import get_session
from models import Todo
from schema.response import ModelAccuracyResponse

# 이 라우터의 모든 엔드포인트 앞에 자동으로 /admin이 붙는다. (접두어)
# 지금은 실습용이라 누구나 접근 가능 -> 실무라면 관리자 권한 체크가 필요하다. 
router = APIRouter(prefix='/admin', tags=['ML Monitoring'])

@router.get('/model-accuracy', response_model=ModelAccuracyResponse, status_code=status.HTTP_200_OK)
def get_model_accuracy_handler(session=Depends(get_session)):
    """
    final_category가 채워진(=사용자가 확인/수정을 완료한) Todo만 "정답이 있는" 데이터로 취급해서
    정확도 계산 대상으로 삼는다.
    predicted_category만 있고 final_category가 없는(=아직 아무도 확인 안 한) Todo는
    정확도 계산에서 제외된다.    
    """
    total_stmt = select(func.count()).select_from(Todo).where(Todo.final_category.is_not(None))
    total_labeled = session.execute(total_stmt).scalar_one()

    # predicted_category와 final_category가 "정확히 일치하는" 개수
    # models.py에서 두 개의 컬럼을 나누었다.
    correct_stmt = select(func.count()).select_from(Todo).where(
        Todo.final_category.is_not(None), # SQL문으로--> WHERE final_category IS NOT NULL 
        Todo.predicted_category == Todo.final_category,
    )
    correct = session.execute(correct_stmt).scalar_one()

    # total_labeled가 0이면 0으로 나누는 에러가 발생하니까 미리 방어 처리
    accuracy = round(correct / total_labeled, 4) if total_labeled > 0 else None

    return ModelAccuracyResponse(
        total_labeled=total_labeled,
        correct=correct,
        accuracy=accuracy,
    )