from sqlalchemy import (
   BigInteger,
   Boolean,
   Column,
   Date,
   DateTime,
   ForeignKeyConstraint,
   Integer,
   LargeBinary,
   String,
   Table,
   Text,
   UniqueConstraint,
   text,
)


def defaultSourceTableColumns():
    return([
      #######################################################################
      # General included fields
      Column(
         "srcsys",
         String(100),
         nullable=True,
         server_default=text("'w5base'"),
      ),
      Column("srcid", 
         String(100), 
         nullable=True
      ),
      Column("srcload", 
         DateTime, 
         nullable=True
      ),
      Column("createuser", 
         BigInteger, 
         nullable=False, 
         server_default=text("'0'")
      ),
      Column("modifyuser", 
         BigInteger, 
         nullable=False, 
         server_default=text("'0'")
      ),
      Column("editor", 
         String(255), 
         nullable=False, 
         server_default=text("''")
      ),
      Column("realeditor", 
         String(255), 
         nullable=False, 
         server_default=text("''")
      ),
      Column("lastqcheck", 
         DateTime, 
         nullable=True, 
         index=True
      ),
      UniqueConstraint("srcsys","srcid", 
         name="srcsys"
      )
   ])

