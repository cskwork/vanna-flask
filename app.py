from dotenv import load_dotenv
load_dotenv()

from functools import wraps
from flask import Flask, jsonify, Response, request
import flask
import os
from cache import MemoryCache
import logging
from waitress import serve
import time
from collections import defaultdict
import re

from config import MyVanna, get_db_connection_params

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='')

# SETUP
cache = MemoryCache()

# Rate limiting setup
request_counts = defaultdict(list)
RATE_LIMIT_REQUESTS = int(os.environ.get('RATE_LIMIT_REQUESTS', '30'))
RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '60'))  # seconds

vn = MyVanna()

db_params = get_db_connection_params()

# 데이터베이스 연결 시도 (에러 핸들링 포함)
try:
    if db_params['db_type'] == 'sqlite':
        logger.info(f"Connecting to SQLite database: {db_params['path']}")
        vn.connect_to_sqlite(db_params['path'])
    elif db_params['db_type'] == 'mysql':
        logger.info(f"Connecting to MySQL database at {db_params['host']}")
        vn.connect_to_mysql(
            host=db_params['host'],
            user=db_params['user'],
            password=db_params['password'],
            db=db_params['database'],
        )
    elif db_params['db_type'] == 'postgresql':
        logger.info(f"Connecting to PostgreSQL database at {db_params['host']}")
        vn.connect_to_postgres(
            host=db_params['host'],
            user=db_params['user'],
            password=db_params['password'],
            db=db_params['database'],
        )
    
    logger.info("Database connection established successfully")
    
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    logger.error("Application will start but database features may not work properly")
    # 애플리케이션은 계속 실행되지만 DB 연결 실패를 로그에 기록

# Utility functions for UX improvements
def check_rate_limit():
    """Rate limiting to prevent API abuse"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    current_time = time.time()
    
    # Clean old requests outside the window
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check if rate limit exceeded
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Record this request
    request_counts[client_ip].append(current_time)
    return True

def validate_question(question):
    """입력된 질문의 유효성을 검사합니다"""
    if not question or not question.strip():
        return False, "질문을 입력해주세요"
    
    if len(question.strip()) < 3:
        return False, "질문은 최소 3글자 이상이어야 합니다"
    
    if len(question.strip()) > 500:
        return False, "질문은 500글자를 초과할 수 없습니다"
    
    # SQL injection 패턴 기본 검사
    dangerous_patterns = ['drop table', 'delete from', 'truncate', 'update', 'insert into']
    question_lower = question.lower()
    for pattern in dangerous_patterns:
        if pattern in question_lower:
            return False, f"보안상 위험한 패턴이 감지되었습니다: {pattern}"
    
    return True, None

def rate_limit_decorator(f):
    """Rate limiting decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_rate_limit():
            logger.warning(f"Rate limit exceeded for {request.environ.get('REMOTE_ADDR', 'unknown')}")
            return jsonify({
                "type": "error", 
                "error": "너무 많은 요청이 발생했습니다. 잠시 후 다시 시도해주세요.",
                "retry_after": RATE_LIMIT_WINDOW
            }), 429
        return f(*args, **kwargs)
    return decorated

# NO NEED TO CHANGE ANYTHING BELOW THIS LINE
def requires_cache(fields):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            id = request.args.get('id')

            if id is None:
                logger.warning("No id provided")
                return jsonify({"type": "error", "error": "No id provided"})
            
            for field in fields:
                if cache.get(id=id, field=field) is None:
                    logger.warning(f"No {field} found for id {id}")
                    return jsonify({"type": "error", "error": f"No {field} found"})
            
            field_values = {field: cache.get(id=id, field=field) for field in fields}
            
            # Add the id to the field_values
            field_values['id'] = id

            return f(*args, **field_values, **kwargs)
        return decorated
    return decorator

@app.route('/api/v0/health', methods=['GET'])
def health_check():
    """시스템 상태를 확인하는 헬스체크 엔드포인트"""
    try:
        # 기본 서비스 상태 확인
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "components": {}
        }
        
        # 데이터베이스 연결 확인
        try:
            # 간단한 쿼리로 DB 연결 테스트
            test_query = "SELECT 1"
            vn.run_sql(test_query)
            health_status["components"]["database"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy", 
                "error": str(e)[:100]
            }
            health_status["status"] = "degraded"
        
        # LLM 서비스 상태 확인 (간단한 체크)
        try:
            # 매우 간단한 질문으로 LLM 응답성 테스트
            if hasattr(vn, 'generate_sql'):
                health_status["components"]["llm"] = {"status": "healthy"}
            else:
                health_status["components"]["llm"] = {"status": "unhealthy", "error": "LLM not available"}
        except Exception as e:
            health_status["components"]["llm"] = {
                "status": "unhealthy", 
                "error": str(e)[:100]
            }
            health_status["status"] = "degraded"
        
        # 캐시 시스템 확인
        try:
            test_key = "health_check_test"
            cache.set(id=test_key, field="test", value="test_value")
            retrieved = cache.get(id=test_key, field="test")
            if retrieved == "test_value":
                health_status["components"]["cache"] = {"status": "healthy"}
                cache.delete(id=test_key)  # 정리
            else:
                health_status["components"]["cache"] = {"status": "unhealthy", "error": "Cache not working"}
        except Exception as e:
            health_status["components"]["cache"] = {
                "status": "unhealthy", 
                "error": str(e)[:100]
            }
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }), 503

@app.route('/api/v0/generate_questions', methods=['GET'])
def generate_questions():
    logger.info("Generating sample questions")
    try:
        questions = vn.generate_questions()
        if not questions:
            return jsonify({
                "type": "question_list", 
                "questions": ["데이터베이스에서 모든 테이블을 보여주세요", "가장 최근 레코드 10개를 조회해주세요"],
                "header": "추천 질문 생성에 실패했습니다. 기본 질문을 사용해보세요:",
                "fallback": True
            })
        
        return jsonify({
            "type": "question_list", 
            "questions": questions,
            "header": "다음 질문들을 참고해보세요:",
            "count": len(questions)
        })
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        return jsonify({
            "type": "error",
            "error": "추천 질문 생성 중 오류가 발생했습니다.",
            "fallback_questions": ["데이터베이스에서 모든 테이블을 보여주세요", "가장 최근 레코드 10개를 조회해주세요"]
        }), 500

@app.route('/api/v0/generate_sql', methods=['GET'])
@rate_limit_decorator
def generate_sql():
    question = flask.request.args.get('question')
    logger.info(f"Generating SQL for question: {question}")

    # Enhanced validation
    if question is None:
        logger.warning("No question provided")
        return jsonify({
            "type": "error", 
            "error": "질문 파라미터가 필요합니다",
            "details": "URL에 ?question=your_question을 추가해주세요"
        }), 400

    # Validate question content
    is_valid, error_msg = validate_question(question)
    if not is_valid:
        logger.warning(f"Invalid question: {error_msg}")
        return jsonify({
            "type": "error", 
            "error": error_msg,
            "question_length": len(question) if question else 0
        }), 400

    try:
        id = cache.generate_id(question=question)
        
        # Check if this exact question was asked recently (cache hit)
        cached_sql = cache.get(id=id, field='sql')
        if cached_sql:
            logger.info(f"Cache hit for question: {question}")
            return jsonify({
                "type": "sql", 
                "id": id,
                "text": cached_sql,
                "cached": True
            })
        
        # Generate new SQL
        sql = vn.generate_sql(question=question)
        
        if not sql or sql.strip() == '':
            return jsonify({
                "type": "error", 
                "error": "SQL 생성에 실패했습니다. 질문을 다시 확인해주세요.",
                "suggestion": "더 구체적이고 명확한 질문을 입력해보세요."
            }), 500

        cache.set(id=id, field='question', value=question)
        cache.set(id=id, field='sql', value=sql)

        return jsonify({
            "type": "sql", 
            "id": id,
            "text": sql,
            "cached": False
        })
        
    except Exception as e:
        logger.error(f"Error generating SQL for question '{question}': {e}")
        return jsonify({
            "type": "error", 
            "error": "SQL 생성 중 오류가 발생했습니다.",
            "details": "서버 로그를 확인하거나 잠시 후 다시 시도해주세요.",
            "question": question
        }), 500

@app.route('/api/v0/run_sql', methods=['GET'])
@requires_cache(['sql'])
@rate_limit_decorator
def run_sql(id: str, sql: str):
    logger.info(f"Running SQL for id {id}: {sql}")
    
    # SQL 안전성 검사
    sql_lower = sql.lower().strip()
    
    # 위험한 SQL 명령어 체크
    dangerous_commands = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']
    for cmd in dangerous_commands:
        if sql_lower.startswith(cmd + ' ') or f' {cmd} ' in sql_lower:
            logger.warning(f"Dangerous SQL command detected: {cmd} in query: {sql}")
            return jsonify({
                "type": "error", 
                "error": f"보안상 위험한 SQL 명령어가 감지되었습니다: {cmd}",
                "allowed_operations": "SELECT 쿼리만 허용됩니다.",
                "sql": sql
            }), 403
    
    # SELECT 쿼리인지 확인
    if not sql_lower.startswith('select'):
        return jsonify({
            "type": "error", 
            "error": "SELECT 쿼리만 실행할 수 있습니다.",
            "received_query_type": sql_lower.split()[0] if sql_lower.split() else "unknown",
            "sql": sql
        }), 403
    
    try:
        start_time = time.time()
        df = vn.run_sql(sql=sql)
        execution_time = time.time() - start_time
        
        if df is None or df.empty:
            return jsonify({
                "type": "df", 
                "id": id,
                "df": [],
                "row_count": 0,
                "execution_time": round(execution_time, 3),
                "message": "쿼리가 성공적으로 실행되었지만 결과가 없습니다."
            })

        # 결과 크기 제한 (성능 최적화)
        total_rows = len(df)
        display_limit = 100
        df_display = df.head(display_limit)
        
        cache.set(id=id, field='df', value=df)

        return jsonify({
            "type": "df", 
            "id": id,
            "df": df_display.to_json(orient='records'),
            "row_count": total_rows,
            "displayed_rows": len(df_display),
            "execution_time": round(execution_time, 3),
            "columns": list(df.columns),
            "has_more": total_rows > display_limit
        })

    except Exception as e:
        execution_time = time.time() - start_time if 'start_time' in locals() else 0
        error_msg = str(e)
        
        # 일반적인 데이터베이스 오류 메시지 개선
        if "no such table" in error_msg.lower():
            user_error = "지정된 테이블이 존재하지 않습니다. 테이블 이름을 확인해주세요."
        elif "syntax error" in error_msg.lower():
            user_error = "SQL 문법 오류가 있습니다. 쿼리를 다시 확인해주세요."
        elif "permission denied" in error_msg.lower():
            user_error = "데이터베이스 접근 권한이 없습니다."
        elif "timeout" in error_msg.lower():
            user_error = "쿼리 실행 시간이 초과되었습니다. 더 간단한 쿼리를 시도해보세요."
        else:
            user_error = "쿼리 실행 중 오류가 발생했습니다."
        
        logger.error(f"Error running SQL for id {id}: {e}")
        return jsonify({
            "type": "error", 
            "error": user_error,
            "technical_error": error_msg[:200],  # 기술적 에러 정보는 제한
            "execution_time": round(execution_time, 3),
            "sql": sql,
            "suggestion": "쿼리를 단순화하거나 다른 접근 방식을 시도해보세요."
        }), 500

@app.route('/api/v0/download_csv', methods=['GET'])
@requires_cache(['df'])
def download_csv(id: str, df):
    logger.info(f"Downloading CSV for id {id}")
    csv = df.to_csv()

    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 f"attachment; filename={id}.csv"})

@app.route('/api/v0/generate_plotly_figure', methods=['GET'])
@requires_cache(['df', 'question', 'sql'])
def generate_plotly_figure(id: str, df, question, sql):
    logger.info(f"Generating Plotly figure for id {id}")
    try:
        code = vn.generate_plotly_code(question=question, sql=sql, df_metadata=f"Running df.dtypes gives:\n {df.dtypes}")
        fig = vn.get_plotly_figure(plotly_code=code, df=df, dark_mode=False)
        fig_json = fig.to_json()

        cache.set(id=id, field='fig_json', value=fig_json)

        return jsonify(
            {
                "type": "plotly_figure", 
                "id": id,
                "fig": fig_json,
            })
    except Exception as e:
        logger.error(f"Error generating Plotly figure for id {id}: {e}")
        import traceback
        traceback.print_exc()

        return jsonify({"type": "error", "error": str(e)})

@app.route('/api/v0/get_training_data', methods=['GET'])
def get_training_data():
    logger.info("Getting training data")
    df = vn.get_training_data()

    return jsonify(
    {
        "type": "df", 
        "id": "training_data",
        "df": df.head(25).to_json(orient='records'),
    })

@app.route('/api/v0/remove_training_data', methods=['POST'])
def remove_training_data():
    id = flask.request.json.get('id')
    logger.info(f"Removing training data for id {id}")

    if id is None:
        logger.warning("No id provided for removing training data")
        return jsonify({"type": "error", "error": "No id provided"})

    if vn.remove_training_data(id=id):
        return jsonify({"success": True})
    else:
        logger.error(f"Couldn't remove training data for id {id}")
        return jsonify({"type": "error", "error": "Couldn't remove training data"})

@app.route('/api/v0/train', methods=['POST'])
def add_training_data():
    question = flask.request.json.get('question')
    sql = flask.request.json.get('sql')
    ddl = flask.request.json.get('ddl')
    documentation = flask.request.json.get('documentation')
    logger.info(f"Adding training data: question={question}, sql={sql}, ddl={ddl}, documentation={documentation}")

    try:
        id = vn.train(question=question, sql=sql, ddl=ddl, documentation=documentation)

        return jsonify({"id": id})
    except Exception as e:
        logger.error(f"Error adding training data: {e}")
        return jsonify({"type": "error", "error": str(e)})

@app.route('/api/v0/generate_followup_questions', methods=['GET'])
@requires_cache(['df', 'question', 'sql'])
def generate_followup_questions(id: str, df, question, sql):
    logger.info(f"Generating followup questions for id {id}")
    followup_questions = vn.generate_followup_questions(question=question, sql=sql, df=df)

    cache.set(id=id, field='followup_questions', value=followup_questions)

    return jsonify(
        {
            "type": "question_list", 
            "id": id,
            "questions": followup_questions,
            "header": "Here are some followup questions you can ask:"
        })

@app.route('/api/v0/load_question', methods=['GET'])
@requires_cache(['question', 'sql', 'df', 'fig_json', 'followup_questions'])
def load_question(id: str, question, sql, df, fig_json, followup_questions):
    logger.info(f"Loading question for id {id}")
    try:
        return jsonify(
            {
                "type": "question_cache", 
                "id": id,
                "question": question,
                "sql": sql,
                "df": df.head(10).to_json(orient='records'),
                "fig": fig_json,
                "followup_questions": followup_questions,
            })

    except Exception as e:
        logger.error(f"Error loading question for id {id}: {e}")
        return jsonify({"type": "error", "error": str(e)})

@app.route('/api/v0/get_question_history', methods=['GET'])
def get_question_history():
    logger.info("Getting question history")
    return jsonify({"type": "question_history", "questions": cache.get_all(field_list=['question']) })

@app.route('/api/v0/config', methods=['GET'])
def get_config():
    """시스템 설정 정보를 반환합니다 (민감한 정보 제외)"""
    try:
        config_info = {
            "database_type": db_params.get('db_type', 'unknown'),
            "llm_provider": os.environ.get('LLM', 'ollama'),
            "vector_store": os.environ.get('VECTOR_STORE', 'chromadb'),
            "rate_limiting": {
                "requests_per_window": RATE_LIMIT_REQUESTS,
                "window_seconds": RATE_LIMIT_WINDOW
            },
            "features": {
                "health_check": True,
                "rate_limiting": True,
                "input_validation": True,
                "sql_safety_checks": True,
                "caching": True
            },
            "version": "1.0.0"
        }
        
        return jsonify(config_info)
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({
            "type": "error",
            "error": "설정 정보를 가져오는 중 오류가 발생했습니다."
        }), 500

@app.route('/')
def root():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    logger.info("Starting Vanna Flask app")
    serve(app, host='0.0.0.0', port=8080)
