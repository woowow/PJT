from __future__ import annotations

from datetime import datetime
import pendulum

from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator

KST = pendulum.timezone("Asia/Seoul")

with DAG(
    dag_id="reset_weekly_count",
    description="Reset paper.weekly_count every week (guestcategorycount is NOT reset).",
    schedule="0 0 * * 0",  # 일요일 00:00 (KST)
    start_date=datetime(2025, 1, 1, tzinfo=KST),
    catchup=False,
    max_active_runs=1,
    tags=["paper", "weekly", "postgres"],
) as dag:

    reset_paper_weekly_count = PostgresOperator(
        task_id="reset_paper_weekly_count",
        postgres_conn_id="paper_postgres", 
        sql="""
        UPDATE paper
        SET weekly_count = 0;
        """,
    )

    reset_paper_weekly_count
