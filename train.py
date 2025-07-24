from dotenv import load_dotenv
load_dotenv()

from config import MyVanna, get_db_connection

vn = MyVanna()

db_connection = get_db_connection()

if db_connection['db_type'] == 'sqlite':
    vn.connect_to_sqlite(db_connection['path'])
    print("Training Vanna on SQLite...")
    df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
    for ddl in df_ddl['sql'].to_list():
      vn.train(ddl=ddl)
    print("Training complete.")
elif db_connection['db_type'] == 'mysql':
    vn.connect_to_mysql(
        host=db_connection['host'],
        user=db_connection['user'],
        password=db_connection['password'],
        db=db_connection['database'],
    )
    print("Training Vanna on MySQL...")
    print("Please add your DDL statements to train Vanna on your MySQL database.")
    # Example:
    # vn.train(ddl="CREATE TABLE ...")
    print("Training complete.")
elif db_connection['db_type'] == 'postgresql':
    vn.connect_to_postgres(
        host=db_connection['host'],
        user=db_connection['user'],
        password=db_connection['password'],
        db=db_connection['database'],
    )
    print("Training Vanna on PostgreSQL...")
    print("Please add your DDL statements to train Vanna on your PostgreSQL database.")
    # Example:
    # vn.train(ddl="CREATE TABLE ...")
    print("Training complete.")
