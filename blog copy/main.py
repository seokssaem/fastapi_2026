from schema.request import ArticleRequest, ArticleUpdateRequest
from schema.response import ArticleResponse
from fastapi import FastAPI, HTTPException, status

app = FastAPI(
    title='블로그 API',
    description='FastAPI 입문 실습 과제 - 블로그',
    version='1.0.0'
)

# 0. 임시 데이터 저장소 (메모리)
articles = []

# 1. 루트 (홈)
@app.get('/')
def root_handler(): 
    return {'message':'Hello, Blog!!!'}

# 2. 전체 게시글 조회
@app.get('/articles', 
         response_model=list[ArticleResponse],
         status_code=status.HTTP_200_OK)
def get_articles():
    """전체 블로그 게시글 조회 - 없으면 빈 리스트를 반환"""
    return articles

# 3. 단일 게시글 조회 - 경로 매개변수
@app.get(
    '/articles/{article_id}',
    response_model=ArticleResponse,
    status_code=status.HTTP_200_OK
)
def get_article(article_id: int):
    for a in articles:
        if a['id'] == article_id:
            return a 
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f'{article_id}번 게시글을 찾을 수 없습니다.'
    )
    
# 4. POST - 게시글 생성    
@app.post(
    '/articles',
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED
)
def create_article(body: ArticleRequest):
    new_article = {
        'id': len(articles) + 1, 
        'title': body.title,
        'content': body.content,
    }
    articles.append(new_article)
    return new_article

# 5. PATCH - 게시글 수정
@app.patch(
    '/articles/{article_id}',
    response_model=ArticleResponse,
    status_code=status.HTTP_200_OK
)
def update_article(article_id: int, body: ArticleUpdateRequest):
    for a in articles:
        if a['id'] == article_id:
            if body.title is not None: # 수정될 제목이 있다면
                a['title'] = body.title # 제목 수정
            if body.content is not None: # 수정될 내용이 있다면
                a['content'] = body.content
            return a # 수정된 게시판글(a) 반환
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail=f'{article_id}번 수정될 부분을 찾지 못했습니다.')

# 6. DELETE - 게시글 삭제
@app.delete(
    '/articles/{article_id}',
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_article(article_id: int):
    for a in articles:
        if a['id'] == article_id:
            articles.remove(a) # 해당 게시글 삭제
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail=f'{article_id}번 게시글을 찾지 못해서 삭제를 할 수가 없습니다.')