from dotenv import load_dotenv
load_dotenv()

from config import MyVanna, get_db_connection_params

vn = MyVanna()

db_params = get_db_connection_params()

if db_params['db_type'] == 'sqlite':
    vn.connect_to_sqlite(db_params['path'])
    print("Training Vanna on SQLite...")
    df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
    for ddl in df_ddl['sql'].to_list():
      vn.train(ddl=ddl)
    print("Training complete.")
elif db_params['db_type'] == 'mysql':
    vn.connect_to_mysql(
        host=db_params['host'],
        user=db_params['user'],
        password=db_params['password'],
        db=db_params['database'],
    )
    print("Training Vanna on MySQL...")
    print("Please add your DDL statements to train Vanna on your MySQL database.")
    # Example:
    # vn.train(ddl="CREATE TABLE ...")
    print("Training complete.")
elif db_params['db_type'] == 'postgresql':
    vn.connect_to_postgres(
        host=db_params['host'],
        user=db_params['user'],
        password=db_params['password'],
        db=db_params['database'],
    )
    print("Training Vanna on PostgreSQL...")
    print("Please add your DDL statements to train Vanna on your PostgreSQL database.")
    # Example:
    # vn.train(ddl="CREATE TABLE ...")
    print("Training complete.")
