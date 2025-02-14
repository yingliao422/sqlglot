from tests.dialects.test_dialect import Validator


class TestDatabricks(Validator):
    dialect = "databricks"

    def test_databricks(self):
        self.validate_identity("CREATE TABLE t (c STRUCT<interval: DOUBLE COMMENT 'aaa'>)")
        self.validate_identity("CREATE TABLE my_table () TBLPROPERTIES (a.b=15)")
        self.validate_identity("CREATE TABLE my_table () TBLPROPERTIES ('a.b'=15)")
        self.validate_identity("SELECT CAST('11 23:4:0' AS INTERVAL DAY TO HOUR)")
        self.validate_identity("SELECT CAST('11 23:4:0' AS INTERVAL DAY TO MINUTE)")
        self.validate_identity("SELECT CAST('11 23:4:0' AS INTERVAL DAY TO SECOND)")
        self.validate_identity("SELECT CAST('23:00:00' AS INTERVAL HOUR TO MINUTE)")
        self.validate_identity("SELECT CAST('23:00:00' AS INTERVAL HOUR TO SECOND)")
        self.validate_identity("SELECT CAST('23:00:00' AS INTERVAL MINUTE TO SECOND)")
        self.validate_identity("CREATE TABLE target SHALLOW CLONE source")
        self.validate_identity("INSERT INTO a REPLACE WHERE cond VALUES (1), (2)")
        self.validate_identity("SELECT c1 : price")
        self.validate_identity("CREATE FUNCTION a.b(x INT) RETURNS INT RETURN x + 1")
        self.validate_identity("CREATE FUNCTION a AS b")
        self.validate_identity("SELECT ${x} FROM ${y} WHERE ${z} > 1")
        self.validate_identity("CREATE TABLE foo (x DATE GENERATED ALWAYS AS (CAST(y AS DATE)))")
        self.validate_identity(
            "SELECT * FROM sales UNPIVOT INCLUDE NULLS (sales FOR quarter IN (q1 AS `Jan-Mar`))"
        )
        self.validate_identity(
            "SELECT * FROM sales UNPIVOT EXCLUDE NULLS (sales FOR quarter IN (q1 AS `Jan-Mar`))"
        )

        self.validate_all(
            "CREATE TABLE foo (x INT GENERATED ALWAYS AS (YEAR(y)))",
            write={
                "databricks": "CREATE TABLE foo (x INT GENERATED ALWAYS AS (YEAR(TO_DATE(y))))",
                "tsql": "CREATE TABLE foo (x AS YEAR(CAST(y AS DATE)))",
            },
        )
        self.validate_all(
            "CREATE TABLE t1 AS (SELECT c FROM t2)",
            read={
                "teradata": "CREATE TABLE t1 AS (SELECT c FROM t2) WITH DATA",
            },
        )

    # https://docs.databricks.com/sql/language-manual/functions/colonsign.html
    def test_json(self):
        self.validate_identity("""SELECT c1 : price FROM VALUES ('{ "price": 5 }') AS T(c1)""")

        self.validate_all(
            """SELECT c1:['price'] FROM VALUES('{ "price": 5 }') AS T(c1)""",
            write={
                "databricks": """SELECT c1 : ARRAY('price') FROM VALUES ('{ "price": 5 }') AS T(c1)""",
            },
        )
        self.validate_all(
            """SELECT c1:item[1].price FROM VALUES('{ "item": [ { "model" : "basic", "price" : 6.12 }, { "model" : "medium", "price" : 9.24 } ] }') AS T(c1)""",
            write={
                "databricks": """SELECT c1 : item[1].price FROM VALUES ('{ "item": [ { "model" : "basic", "price" : 6.12 }, { "model" : "medium", "price" : 9.24 } ] }') AS T(c1)""",
            },
        )
        self.validate_all(
            """SELECT c1:item[*].price FROM VALUES('{ "item": [ { "model" : "basic", "price" : 6.12 }, { "model" : "medium", "price" : 9.24 } ] }') AS T(c1)""",
            write={
                "databricks": """SELECT c1 : item[*].price FROM VALUES ('{ "item": [ { "model" : "basic", "price" : 6.12 }, { "model" : "medium", "price" : 9.24 } ] }') AS T(c1)""",
            },
        )
        self.validate_all(
            """SELECT from_json(c1:item[*].price, 'ARRAY<DOUBLE>')[0] FROM VALUES('{ "item": [ { "model" : "basic", "price" : 6.12 }, { "model" : "medium", "price" : 9.24 } ] }') AS T(c1)""",
            write={
                "databricks": """SELECT FROM_JSON(c1 : item[*].price, 'ARRAY<DOUBLE>')[0] FROM VALUES ('{ "item": [ { "model" : "basic", "price" : 6.12 }, { "model" : "medium", "price" : 9.24 } ] }') AS T(c1)""",
            },
        )
        self.validate_all(
            """SELECT inline(from_json(c1:item[*], 'ARRAY<STRUCT<model STRING, price DOUBLE>>')) FROM VALUES('{ "item": [ { "model" : "basic", "price" : 6.12 }, { "model" : "medium", "price" : 9.24 } ] }') AS T(c1)""",
            write={
                "databricks": """SELECT INLINE(FROM_JSON(c1 : item[*], 'ARRAY<STRUCT<model STRING, price DOUBLE>>')) FROM VALUES ('{ "item": [ { "model" : "basic", "price" : 6.12 }, { "model" : "medium", "price" : 9.24 } ] }') AS T(c1)""",
            },
        )

    def test_datediff(self):
        self.validate_all(
            "SELECT DATEDIFF(year, 'start', 'end')",
            write={
                "tsql": "SELECT DATEDIFF(year, 'start', 'end')",
                "databricks": "SELECT DATEDIFF(year, 'start', 'end')",
            },
        )
        self.validate_all(
            "SELECT DATEDIFF(microsecond, 'start', 'end')",
            write={
                "databricks": "SELECT DATEDIFF(microsecond, 'start', 'end')",
                "postgres": "SELECT CAST(EXTRACT(epoch FROM CAST('end' AS TIMESTAMP) - CAST('start' AS TIMESTAMP)) * 1000000 AS BIGINT)",
            },
        )
        self.validate_all(
            "SELECT DATEDIFF(millisecond, 'start', 'end')",
            write={
                "databricks": "SELECT DATEDIFF(millisecond, 'start', 'end')",
                "postgres": "SELECT CAST(EXTRACT(epoch FROM CAST('end' AS TIMESTAMP) - CAST('start' AS TIMESTAMP)) * 1000 AS BIGINT)",
            },
        )
        self.validate_all(
            "SELECT DATEDIFF(second, 'start', 'end')",
            write={
                "databricks": "SELECT DATEDIFF(second, 'start', 'end')",
                "postgres": "SELECT CAST(EXTRACT(epoch FROM CAST('end' AS TIMESTAMP) - CAST('start' AS TIMESTAMP)) AS BIGINT)",
            },
        )
        self.validate_all(
            "SELECT DATEDIFF(minute, 'start', 'end')",
            write={
                "databricks": "SELECT DATEDIFF(minute, 'start', 'end')",
                "postgres": "SELECT CAST(EXTRACT(epoch FROM CAST('end' AS TIMESTAMP) - CAST('start' AS TIMESTAMP)) / 60 AS BIGINT)",
            },
        )
        self.validate_all(
            "SELECT DATEDIFF(hour, 'start', 'end')",
            write={
                "databricks": "SELECT DATEDIFF(hour, 'start', 'end')",
                "postgres": "SELECT CAST(EXTRACT(epoch FROM CAST('end' AS TIMESTAMP) - CAST('start' AS TIMESTAMP)) / 3600 AS BIGINT)",
            },
        )
        self.validate_all(
            "SELECT DATEDIFF(day, 'start', 'end')",
            write={
                "databricks": "SELECT DATEDIFF(day, 'start', 'end')",
                "postgres": "SELECT CAST(EXTRACT(epoch FROM CAST('end' AS TIMESTAMP) - CAST('start' AS TIMESTAMP)) / 86400 AS BIGINT)",
            },
        )
        self.validate_all(
            "SELECT DATEDIFF(week, 'start', 'end')",
            write={
                "databricks": "SELECT DATEDIFF(week, 'start', 'end')",
                "postgres": "SELECT CAST(EXTRACT(year FROM AGE(CAST('end' AS TIMESTAMP), CAST('start' AS TIMESTAMP))) * 48 + EXTRACT(month FROM AGE(CAST('end' AS TIMESTAMP), CAST('start' AS TIMESTAMP))) * 4 + EXTRACT(day FROM AGE(CAST('end' AS TIMESTAMP), CAST('start' AS TIMESTAMP))) / 7 AS BIGINT)",
            },
        )
        self.validate_all(
            "SELECT DATEDIFF(month, 'start', 'end')",
            write={
                "databricks": "SELECT DATEDIFF(month, 'start', 'end')",
                "postgres": "SELECT CAST(EXTRACT(year FROM AGE(CAST('end' AS TIMESTAMP), CAST('start' AS TIMESTAMP))) * 12 + EXTRACT(month FROM AGE(CAST('end' AS TIMESTAMP), CAST('start' AS TIMESTAMP))) AS BIGINT)",
            },
        )
        self.validate_all(
            "SELECT DATEDIFF(quarter, 'start', 'end')",
            write={
                "databricks": "SELECT DATEDIFF(quarter, 'start', 'end')",
                "postgres": "SELECT CAST(EXTRACT(year FROM AGE(CAST('end' AS TIMESTAMP), CAST('start' AS TIMESTAMP))) * 4 + EXTRACT(month FROM AGE(CAST('end' AS TIMESTAMP), CAST('start' AS TIMESTAMP))) / 3 AS BIGINT)",
            },
        )
        self.validate_all(
            "SELECT DATEDIFF(year, 'start', 'end')",
            write={
                "databricks": "SELECT DATEDIFF(year, 'start', 'end')",
                "postgres": "SELECT CAST(EXTRACT(year FROM AGE(CAST('end' AS TIMESTAMP), CAST('start' AS TIMESTAMP))) AS BIGINT)",
            },
        )

    def test_add_date(self):
        self.validate_all(
            "SELECT DATEADD(year, 1, '2020-01-01')",
            write={
                "tsql": "SELECT DATEADD(year, 1, '2020-01-01')",
                "databricks": "SELECT DATEADD(year, 1, '2020-01-01')",
            },
        )
        self.validate_all(
            "SELECT DATEDIFF('end', 'start')",
            write={"databricks": "SELECT DATEDIFF(DAY, 'start', 'end')"},
        )
        self.validate_all(
            "SELECT DATE_ADD('2020-01-01', 1)",
            write={
                "tsql": "SELECT DATEADD(DAY, 1, '2020-01-01')",
                "databricks": "SELECT DATEADD(DAY, 1, '2020-01-01')",
            },
        )

    def test_without_as(self):
        self.validate_all(
            "CREATE TABLE x (SELECT 1)",
            write={
                "databricks": "CREATE TABLE x AS (SELECT 1)",
            },
        )

        self.validate_all(
            "WITH x (select 1) SELECT * FROM x",
            write={
                "databricks": "WITH x AS (SELECT 1) SELECT * FROM x",
            },
        )

    def test_merge_into(self):
        self.validate_all(
            """MERGE common..t_reporting_user WITH (HOLDLOCK) AS T
            USING common..t_reporting_user_merge AS S
            ON (T.user_id = S.user_id)
            WHEN NOT MATCHED BY TARGET
            THEN INSERT(user_id, username)
            VALUES(s.user_id, s.username)
            WHEN MATCHED
            THEN UPDATE SET
            T.username = S.username""",
            write={
                "databricks": "MERGE INTO common.t_reporting_user AS T USING common.t_reporting_user_merge AS S ON (T.user_id = S.user_id) WHEN MATCHED THEN UPDATE SET T.username = S.username WHEN NOT MATCHED THEN INSERT (user_id, username) VALUES (s.user_id, s.username)"
            },
        )
        self.validate_all(
            """MERGE common..t_reporting_user WITH (HOLDLOCK) AS T
            USING common..t_reporting_user_merge AS S
            ON (T.user_id = S.user_id)
            WHEN MATCHED
            THEN UPDATE SET
            T.username = S.username
            WHEN NOT MATCHED BY TARGET
            THEN INSERT(user_id, username)
            VALUES(s.user_id, s.username)
            """,
            write={
                "databricks": "MERGE INTO common.t_reporting_user AS T USING common.t_reporting_user_merge AS S ON (T.user_id = S.user_id) WHEN MATCHED THEN UPDATE SET T.username = S.username WHEN NOT MATCHED THEN INSERT (user_id, username) VALUES (s.user_id, s.username)"
            },
        )
        self.validate_all(
            """MERGE common..t_reporting_user WITH (HOLDLOCK) AS T
            USING common..t_reporting_user_merge AS S
            ON (T.user_id = S.user_id)
            WHEN NOT MATCHED BY TARGET
            THEN INSERT(user_id, username)
            VALUES(s.user_id, s.username)
            """,
            write={
                "databricks": "MERGE INTO common.t_reporting_user AS T USING common.t_reporting_user_merge AS S ON (T.user_id = S.user_id) WHEN NOT MATCHED THEN INSERT (user_id, username) VALUES (s.user_id, s.username)"
            },
        )
        self.validate_all(
            """MERGE common..t_reporting_user WITH (HOLDLOCK) AS T
            USING common..t_reporting_user_merge AS S
            ON (T.user_id = S.user_id)
            WHEN MATCHED AND T.username IS NULL
            THEN UPDATE SET
            T.username = S.username
            WHEN NOT MATCHED BY TARGET
            THEN INSERT(user_id, username)
            VALUES(s.user_id, s.username)
            """,
            write={
                "databricks": "MERGE INTO common.t_reporting_user AS T USING common.t_reporting_user_merge AS S ON (T.user_id = S.user_id) WHEN MATCHED AND T.username IS NULL THEN UPDATE SET T.username = S.username WHEN NOT MATCHED THEN INSERT (user_id, username) VALUES (s.user_id, s.username)"
            },
        )
        # more test cases on multiple matched clauses
        self.validate_all(
            """MERGE common..t_reporting_user WITH (HOLDLOCK) AS T
            USING common..t_reporting_user_merge AS S
            ON (T.user_id = S.user_id)
            WHEN MATCHED
            THEN UPDATE SET
            T.username = S.username
            WHEN MATCHED AND S.username = 'xyx'
            THEN UPDATE SET
            T.username = 'yxy'
            WHEN NOT MATCHED BY TARGET
            THEN INSERT(user_id, username)
            VALUES(s.user_id, s.username)
            """,
            write={
                "databricks": "MERGE INTO common.t_reporting_user AS T USING common.t_reporting_user_merge AS S ON (T.user_id = S.user_id) WHEN MATCHED AND S.username = 'xyx' THEN UPDATE SET T.username = 'yxy' WHEN MATCHED THEN UPDATE SET T.username = S.username WHEN NOT MATCHED THEN INSERT (user_id, username) VALUES (s.user_id, s.username)"
            },
        )
        self.validate_all(
            """MERGE common..t_reporting_user WITH (HOLDLOCK) AS T
            USING common..t_reporting_user_merge AS S
            ON (T.user_id = S.user_id)
            WHEN MATCHED AND S.username = 'xyx'
            THEN UPDATE SET
            T.username = 'yxy'
            WHEN MATCHED
            THEN UPDATE SET
            T.username = S.username
            WHEN NOT MATCHED BY TARGET
            THEN INSERT(user_id, username)
            VALUES(s.user_id, s.username)
            """,
            write={
                "databricks": "MERGE INTO common.t_reporting_user AS T USING common.t_reporting_user_merge AS S ON (T.user_id = S.user_id) WHEN MATCHED AND S.username = 'xyx' THEN UPDATE SET T.username = 'yxy' WHEN MATCHED THEN UPDATE SET T.username = S.username WHEN NOT MATCHED THEN INSERT (user_id, username) VALUES (s.user_id, s.username)"
            },
        )
        self.validate_all(
            """MERGE common..t_reporting_user WITH (HOLDLOCK) AS T
            USING common..t_reporting_user_merge AS S
            ON (T.user_id = S.user_id)
            WHEN MATCHED
            THEN UPDATE SET
            T.username = S.username
            WHEN NOT MATCHED BY TARGET
            THEN INSERT(user_id, username)
            VALUES(s.user_id, s.username)
            WHEN MATCHED AND S.username = 'xyx'
            THEN UPDATE SET
            T.username = 'yxy'
            """,
            write={
                "databricks": "MERGE INTO common.t_reporting_user AS T USING common.t_reporting_user_merge AS S ON (T.user_id = S.user_id) WHEN MATCHED AND S.username = 'xyx' THEN UPDATE SET T.username = 'yxy' WHEN MATCHED THEN UPDATE SET T.username = S.username WHEN NOT MATCHED THEN INSERT (user_id, username) VALUES (s.user_id, s.username)"
            },
        )
        self.validate_all(
            """MERGE common..t_reporting_user WITH (HOLDLOCK) AS T
            USING common..t_reporting_user_merge AS S
            ON (T.user_id = S.user_id)
            WHEN MATCHED
            THEN UPDATE SET
            T.username = S.username
            WHEN MATCHED AND S.username = 'xyx'
            THEN UPDATE SET
            T.username = 'yxy'
            WHEN NOT MATCHED BY TARGET
            THEN INSERT(user_id, username)
            VALUES(s.user_id, s.username)
            """,
            write={
                "databricks": "MERGE INTO common.t_reporting_user AS T USING common.t_reporting_user_merge AS S ON (T.user_id = S.user_id) WHEN MATCHED AND S.username = 'xyx' THEN UPDATE SET T.username = 'yxy' WHEN MATCHED THEN UPDATE SET T.username = S.username WHEN NOT MATCHED THEN INSERT (user_id, username) VALUES (s.user_id, s.username)"
            },
        )
        self.validate_all(
            """MERGE common..t_reporting_user WITH (HOLDLOCK) AS T
            USING common..t_reporting_user_merge AS S
            ON (T.user_id = S.user_id)

            WHEN NOT MATCHED BY SOURCE
            THEN DELETE

            WHEN NOT MATCHED BY SOURCE AND S.username = 'xyx'
            THEN DELETE

            WHEN MATCHED
            THEN UPDATE SET
            T.username = S.username

            WHEN MATCHED AND S.username = 'xyx'
            THEN UPDATE SET
            T.username = 'MATCHED'

            WHEN NOT MATCHED AND T.username = 'xyx'
            THEN INSERT(user_id, username)
            VALUES(s.user_id, 'NOT MATCHED')

            WHEN NOT MATCHED
            THEN INSERT(user_id, username)
            VALUES(s.user_id, s.username)
            """,
            write={
                "databricks": "MERGE INTO common.t_reporting_user AS T USING common.t_reporting_user_merge AS S ON (T.user_id = S.user_id) WHEN MATCHED AND S.username = 'xyx' THEN UPDATE SET T.username = 'MATCHED' WHEN MATCHED THEN UPDATE SET T.username = S.username WHEN NOT MATCHED AND T.username = 'xyx' THEN INSERT (user_id, username) VALUES (s.user_id, 'NOT MATCHED') WHEN NOT MATCHED THEN INSERT (user_id, username) VALUES (s.user_id, s.username) WHEN NOT MATCHED BY SOURCE AND S.username = 'xyx' THEN DELETE WHEN NOT MATCHED BY SOURCE THEN DELETE"
            },
        )
