'''
ml/retrain.py
--------------------
- 사용자가 실제로 수정한 카테고리(final_category)를 새 학습 데이터로 삼아 모델을 재학습한다.
- 이 스크립트도 FastAPI 서버와 분리된 별도 프로세스로 실행한다.
    (수동 실행 -> 이후 필요하면 cron/스케줄러로 자동화)
- 시간이 지날수록 실제로 만든 Todo데이터가 쌓이면서 모델이 점점 더 우리 말투/패턴에 맞게 똑똑해지는 
    과정을 볼 수가 있다.
'''
import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy import select
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from database.db_connection import SessionFactory
from models import Todo
from ml.train_model import build_pipeline, get_next_version, ARTIFACTS_DIR, DATA_PATH

def load_original_data() -> pd.DataFrame:
    """최초 학습에 사용한 샘플 데이터. 재학습때도 계속 기반 데이터로 포함시킨다."""
    df = pd.read_csv(DATA_PATH)
    return df[['title', 'category']]

def load_user_corrected_data() -> pd.DataFrame:
    """
    사용자가 final_category를 직접 지정한(=확인/수정한) Todo만 새 학습 데이터로 사용한다.

    FastAPI 요청 흐름 밖에서 실행되므로 SessionFactory()를 직접 호출해서 세션을 만들고,
    끝나면 직접 close()한다.    
    """
    session = SessionFactory()
    try:
        # final_category가 NULL이 아닌(=사용자가 한 번이라도 확인한) 행만 조회
        stmt = select(Todo.title, Todo.final_category).where(
            Todo.final_category.is_not(None)
        )
        rows = session.execute(stmt).all()
    finally:
        session.close()

    if not rows: # 아직 아무도 카테고리를 확인/수정하지 않은 경우 빈 DataFrame 반환
        return pd.DataFrame(columns=['title', 'category'])

    df = pd.DataFrame(rows, columns=['title', 'category'])
    return df

def main():
    original_df = load_original_data()
    corrected_df = load_user_corrected_data()

    print(f'[INFO] 기존 라벨 데이터 {len(original_df)}건')
    print(f'[INFO] 사용자가 직접 수정한 데이터 {len(corrected_df)}건')

    if len(corrected_df) == 0:
        print(f'[WARN] 재학습에 사용할 새 데이터가 없습니다. 재학습을 건너뜁니다!')
        return

    # 원본 데이터 + 사용자 수정 데이터
    combined_df = pd.concat([original_df, corrected_df], ignore_index=True)
    # 같은 제목의 Todo가 여러번 등장할 경우 가장 최근 값을 우선시한다.
    combined_df = combined_df.drop_duplicates(subset=['title'], keep='last')
    print(f'[INFO] 합쳐진 총 학습 데이터: {len(combined_df)}건')

    X_train, X_test, y_train, y_test = train_test_split(
        combined_df['title'], combined_df['category'],
        test_size=0.2, random_state=42,
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)  # 학습

    y_pred = pipeline.predict(X_test)   # 예측
    accuracy = accuracy_score(y_test, y_pred) # 정답과 예측값을 비교해서 정확도 구한다.
    print(f'[INFO] 재학습 후 테스트 정확도: {accuracy:.3f}')
    print(classification_report(y_test, y_pred))

    # 버전 번호는 train_model.py가 만들어둔 다음부터 자동으로 이어진다.
    version = get_next_version(ARTIFACTS_DIR)
    model_path = ARTIFACTS_DIR / f'model_v{version}.pkl'
    joblib.dump(pipeline, model_path)

    metadata = {
        "version": version,
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "n_samples": len(combined_df),
        "n_user_corrected": len(corrected_df),  # 재학습 메타데이터에만 있는 필드
        "accuracy": round(accuracy, 4),
        "categories": sorted(combined_df["category"].unique().tolist()),
        "source": "original + user_corrected",
    }
    metadata_path = ARTIFACTS_DIR / f'model_v{version}_metadata.json'
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    latest_path = ARTIFACTS_DIR / 'latest.pkl'
    joblib.dump(pipeline, latest_path)

    print(f'[INFO] 재학습 모델 저장 완료: {model_path.name} (버전 {version})')
    print(f'[INFO] FastAPI 서버를 재시작해야 새 모델이 반영됩니다.')

if __name__ == '__main__':
    main()