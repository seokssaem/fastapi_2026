'''
=================================================================================
services/category_service.py

학습된 ML 모델(파이프라인 객체)을 감싸서 "제목 문자열 -> 카테고리 문자열"
예측만 담당하는 아주 얇은 계층

=================================================================================
'''
class CategoryPredictionService:
    def __init__(self, model):
        """
        main.py에서 lifespan에서 joblib.load()로 딱 한 번 로드해준 sklearn Pipeline 객체를 
        그대로 주입받는다.
        매 요청마다 이 클래스를 새로 만들어도 model자체는 재사용되므로 무거운 로딩이 반복되지 않는다.
        """

        self.model = model

    def predict(self, title: str) -> str:
        """
        사이킷런 모델은 "여러 건을 한 번에" 예측하는 것을 기본으로 설계되어 있다.
        입력도, 출력도 항상 리스트 형태다.
        한 건만 예측하고 싶어도 [] 리스트로 감싸서 묶어야 하고, 결과도 리스트로 나오므로
        [0]으로 첫 번째(유일한) 값만 꺼낸다.
        """
        prediction = self.model.predict([title])
        return prediction[0]