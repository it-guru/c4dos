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
      "smnow_system",
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
      Column("conumber", String(128), nullable=True),
      Column("sys_id", String(255), nullable=False, server_default=text("''")),
      Column(
         "lastupdate",
         DateTime,
         nullable=True
      ),
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
      Index("smnowsys_lastqcheck", "lastqcheck"),
      extend_existing=True
   )

