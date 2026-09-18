import localSQLalchemy
from sqlalchemy import (
   BigInteger,
   Column,
   DateTime,
   Index,
   Integer,
   LargeBinary,
   String,
   Table,
   Text,
   UniqueConstraint,
   text,
)


def get_table_schema(metadata):
   return Table(
      "cmdb_ci_server",
      metadata,
      # --- Primary Key ---
      Column(
         "id",
         BigInteger,
         primary_key=True,
         server_default=text("'0'"),
      ),
      # --- Columns ---
      Column("name", String(128), nullable=False, server_default=text("''")),
      Column("cost_center", String(128), nullable=True, server_default=text("''")),
      Column("discovery_source", String(128), nullable=True, server_default=text("''")),
      Column("life_cycle_stage", String(128), nullable=True, server_default=text("''")),
      Column("life_cycle_stage_status", String(128), nullable=False, server_default=text("''")),
      Column("location", String(128), nullable=True, server_default=text("''")),
      Column("object_id", String(128), nullable=True, server_default=text("''")),
      Column("used_for", String(128), nullable=True, server_default=text("''")),
      Column("sys_class_name", String(128), nullable=True, server_default=text("''")),
      Column("sys_id", String(255), nullable=False, server_default=text("''")),
      Column(
         "createdate",
         DateTime
      ),
      Column(
         "modifydate",
         DateTime
      ),
      Column("createuser", BigInteger, nullable=False, server_default=text("'0'")),
      Column("modifyuser", BigInteger, nullable=False, server_default=text("'0'")),
      Column("editor", String(100), nullable=False, server_default=text("''")),
      Column("realeditor", String(100), nullable=False, server_default=text("''")),
      Column("lastqcheck", DateTime, nullable=True),
      Column("description", String(128), nullable=True),
      UniqueConstraint("sys_id", name="sysid"),
      Index("system_lastqcheck", "lastqcheck"),
      extend_existing=True
   )

