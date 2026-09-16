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
      "system",
      metadata,
      # --- Primary Key ---
      Column(
         "id",
         BigInteger,
         primary_key=True,
         autoincrement=False,
         server_default=text("'0'"),
      ),
      # --- Columns ---
      Column("name", String(30), nullable=False, server_default=text("''")),
      Column("sys_id", String(255), nullable=False, server_default=text("''")),
      Column(
         "createdate",
         DateTime,
         nullable=False,
         server_default=text("'0000-00-00 00:00:00'"),
      ),
      Column(
         "modifydate",
         DateTime,
         nullable=False,
         server_default=text("'0000-00-00 00:00:00'"),
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

