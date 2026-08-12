# 라이브러리 불러오기
from pathlib import Path  # 경로 설정
import json
import joblib  # 학습이 끝난 파이프라인(전처리 + 모델)을 파일로 저장하고 나중에 다시 불러오기 위해 사용
import pandas as pd
from sklearn.compose import ColumnTransformer  # 열마다 다른 전처리를 동시에 적용
from sklearn.ensemble import RandomForestClassifier  # 모델 정의용 랜덤포레스트 분류 모델
from sklearn.impute import SimpleImputer  # 결측치를 대표값으로 채운다.
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score  # 평가지표들
from sklearn.model_selection import train_test_split  # 학습/ 평가 데이터 분할
from sklearn.pipeline import Pipeline  # 전처리 + 모델을 하나로 묶어서 학습/예측 코드 재현성 보장
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # 수치형 표준화, 범주형 원핫인코딩

# 전처리 + 모델을 하나의 파이프라인으로 묶어서 반환
def build_pipeline() -> Pipeline:
    # 특성중 숫자형과 범주형 구분 (숫자형 특성 처리 파이프라인)
    numeric_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),  # 결측치를 채운다 -> 중앙값으로 채운다.
        ('scaler', StandardScaler())  # 표준화로 스케일링
    ])
    
    # 특성중 숫자형과 범주형 구분 (범주형 특성 처리 파이프라인)
    categorical_pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),  # 결측치를 대표값으로 채운다. / 숫자는 중앙값, 범주형은 최빈값으로 설정
        ('encoder', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    # 모델 입력으로 사용할 열 목록을 명시적으로 나열
    numeric_features = ['행사기간', '버스정류장수']
    categorical_features = ['홈페이지주소', '지하철유무']
    
    # 컬럼별로 다른 전처리를 동시에 적용
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_pipe, numeric_features),
            ('cat', categorical_pipe, categorical_features)
        ]
    )
    
    # 모델 정의
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    # 전처리 + 모델을 하나의 파이프라인으로 묶어서 반환
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', model)
    ])
    
    return pipeline


def train():
    # 데이터 경로 설정
    # __file__ : 현재 이 .py 파일 자신의 경로
    # .resolve() : 상대경로를 절대경로 바꿔준다(어디서 실행하든지 안전함)
    # .parent : 파일이 들어있는 폴더
    HERE = Path(__file__).resolve().parent
    
    # 대문자로 작성한것은 상수로 하겠다는 뜻
    # C:\Users\Administrator\bigdata2026\bigdata2026-basic\ml_data\telecom_churn.csv
    # print(HERE /'ml_data'/'telecom_churn.csv')
    DATA_PATH = HERE / 'ml_data' / '전국문화축제정보정리_raw.csv'
    
    # 학습된 모델과 평가지표 저장 경로 설정 (상수 표기 적용)
    MODEL_PATH = HERE / 'festival_pipeline_model.joblib'
    METRICS_PATH = HERE / 'pipeline_metrics.json'
    
    # csv파일을 읽어 데이터 프레임을 저장
    try:
        df = pd.read_csv(DATA_PATH, encoding='cp949')
    except UnicodeDecodeError:
        df = pd.read_csv(DATA_PATH, encoding='utf-8')
        
    df.columns = df.columns.str.strip()
    
    # 예측하려는 정답 열 가공 (전체 평균 방문객 수보다 작으면 기획 이탈(1), 이상이면 비이탈(0) 처리)
    mean_visitors = df['방문객수'].mean()
    df['is_churn'] = (df['방문객수'] < mean_visitors).astype(int)
    
    # 입력(X) / 정답(Y) 분리
    X = df[['행사기간', '버스정류장수', '홈페이지주소', '지하철유무']]
    y = df['is_churn']
    
    # 학습용/평가용 데이터 분활
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 파이프라인 생성 후 학습 데이터로 학습
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    
    # 예측 확률값 계산
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    
    # 확률이 0.5 이상이면 이탈(1), 미만이면 비이탈(0)으로 최종 분류
    y_pred = (y_prob >= 0.5).astype(int)
    
    # 보고용으로 핵심 자료만 정리
    conf_matrix = confusion_matrix(y_test, y_pred)
    
    try:
        roc_auc = roc_auc_score(y_test, y_prob)
    except ValueError:
        roc_auc = 0.0
        
    class_report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    
    if conf_matrix.shape == (2, 2):
        tn, fp, fn, tp = conf_matrix.ravel()
    else:
        tn, fp, fn, tp = int(conf_matrix), 0, 0, 0
    
    # 보고용으로 핵심 자료만 정리
    metrics = {
        "model_summary": "Pipeline (ColumnTransformer + RandomForestClassifier)",
        "accuracy": round(class_report_dict["accuracy"], 4),
        "roc_auc_score": round(roc_auc, 4),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp)
        }
    }
    
    # 학습된 파이프라인(전처리+모델) 파일로 저장
    joblib.dump(pipeline, MODEL_PATH)
    
    # 평가 지표를 사람이 있을 수 있도록 JSON 파일로 저장
    # ensure_ascii=False : 한글이 유니코드의 escape(\uXXXXX)로 깨지지 않고, 그대로 저장
    # indent=2 : 들여쓰기 2칸으로 보기 좋게 저장
    METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8-sig')
    
    return metrics


if __name__ == '__main__':
    # 이 파일을 직접 python train.py 형태로 실행했을때만 동작
    # (다른 파일에서 import해서 train()함수만 가져다 쓸 때는 실행되지 않는다.)
    print(json.dumps(train(), ensure_ascii=False, indent=2))
