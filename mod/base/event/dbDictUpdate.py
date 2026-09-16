import importlib
import importlib.util
from pathlib import Path

import alembic
from alembic.autogenerate import produce_migrations
from alembic.migration import MigrationContext
from alembic.operations import Operations
from config import *
import dbpool
from event import event
from kernel import *
from logger import *
from packaging.version import parse as parse_version
from pymysql.err import OperationalError as PyMySQLOperationalError
from sqlalchemy import MetaData
from sqlalchemy.exc import OperationalError

###########################################################################
# Patch for old Alembic-Version (< 1.4.0)  (Default value problem on mysql)
if parse_version(alembic.__version__) < parse_version("1.4.0"):
  import alembic.ddl.mysql
  from sqlalchemy.schema import DefaultClause

  if hasattr(alembic.ddl.mysql, "_render_value"):
    _orig_mysql_render_value = alembic.ddl.mysql._render_value

    def _patched_mysql_render_value(compiler, expr):
      if isinstance(expr, DefaultClause):
        expr = expr.arg
      elif hasattr(expr, "arg"):
        expr = expr.arg
      return _orig_mysql_render_value(compiler, expr)

    alembic.ddl.mysql._render_value = _patched_mysql_render_value
###########################################################################


class Event(event):

  def __init__(self):
    super().__init__()

  def run(self):
    logger.info("Starting automatic database schema discovery and update")

    # 1. Discover all base paths from MOD_PATH config
    modpath_str = config.get("GLOBAL", {}).get("MOD_PATH", "")
    base_dir = config["GLOBAL"]["BASE_DIR"]

    raw_paths = [p.strip() for p in modpath_str.split(":") if p.strip()]
    mod_dirs = []
    for p in raw_paths:
      mod_dirs.append(Path(p) if p.startswith("/") else Path(base_dir) / p)

    section_metadata_map = {}

    for mod_dir in mod_dirs:
      for dbdict_dir in mod_dir.glob("mod/*/dbDict"):
        if not dbdict_dir.is_dir():
          continue

        for section_dir in dbdict_dir.iterdir():
          if not section_dir.is_dir():
            continue
          section_name = section_dir.name

          if section_name not in section_metadata_map:
            section_metadata_map[section_name] = MetaData()

          target_metadata = section_metadata_map[section_name]
          for schema_file in section_dir.glob("*.py"):
            if schema_file.name.startswith("__"):
              continue
            self._load_schema_file(schema_file, section_name, target_metadata)

    logger.info(
        f"Discovered schema sections: {list(section_metadata_map.keys())}"
    )

    for section_name, metadata in section_metadata_map.items():
      if not metadata.tables:
        logger.warning(
            f"No tables registered for section '{section_name}', skipping."
        )
        continue

      logger.info(
          f"--- Processing database update for section: '{section_name}' ---"
      )

      try:
        engine = dbpool.get_engine(section_name)
        self._alembic_sync_schema(engine, metadata)
        logger.info(
            f"Completed schema sync for section '{section_name}'"
            f" ({len(metadata.tables)} tables registered)"
        )

      except Exception as e:
        logger.error(
            f"Failed to process database update for section"
            f" '{section_name}': {e}",
            exc_info=True,
        )

    return {"status": "success", "exitcode": 0}

  def _load_schema_file(
      self, schema_file: Path, section_name: str, metadata: MetaData
  ):
    mod_name = f"dyn_dbdict_{section_name}_{schema_file.stem}"
    try:
      spec = importlib.util.spec_from_file_location(mod_name, schema_file)
      if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if hasattr(mod, "get_table_schema"):
          mod.get_table_schema(metadata)
          logger.debug(
              f"[{section_name}] Registered schema from {schema_file.name}"
          )
        else:
          logger.warning(
              f"Schema file {schema_file} has no get_table_schema() function"
          )
    except Exception as e:
      print(
          f"Error loading schema file {schema_file} for section"
          f" '{section_name}': {e}"
      )

  def _alembic_sync_schema(self, engine, metadata: MetaData):
    """Uses Alembic to inspect and apply database schema modifications."""

    # Callback to filter out objects not present in our metadata definition
    def include_object(object, name, type_, reflected, compare_to):
      if type_ == "table":
        # Only consider tables that are explicitly defined in our dbDict metadata
        return name in metadata.tables
      elif type_ in (
          "index",
          "column",
          "foreign_key_constraint",
          "unique_constraint",
      ):
        # Only consider columns/indexes if their parent table is in our metadata
        if hasattr(object, "table") and object.table is not None:
          return object.table.name in metadata.tables
        return True
      return True

    with engine.begin() as conn:
      context = MigrationContext.configure(
          connection=conn,
          opts={
              "compare_type": True,
              "compare_server_default": True,
              "include_object": include_object,
          },
      )

      migration_script = produce_migrations(context, metadata)
      upgrade_ops = migration_script.upgrade_ops

      if upgrade_ops.is_empty():
        logger.info("Database schema is already up-to-date.")
        return

      logger.info("Applying schema modifications via Alembic...")
      op = Operations(context)

      # 1. Sammle alle Tabellen, die in dieser Iteration NEU erstellt werden
      created_table_names = set()

      def collect_new_tables(script_op):
        if hasattr(script_op, "ops"):
          for sub_op in script_op.ops:
            collect_new_tables(sub_op)
        elif type(script_op).__name__.endswith("CreateTableOp"):
          created_table_names.add(script_op.table_name)

      for script_op in upgrade_ops.ops:
        collect_new_tables(script_op)


      # 2. Rekursive Ausführung mit Index-Filterung & Exception-Handling
      def apply_op(script_op):
        if hasattr(script_op, "ops"):
          for sub_op in script_op.ops:
            apply_op(sub_op)
          return

        op_type = type(script_op).__name__

        # Neu: Spalten-Objekt entkoppeln, damit es nicht "already assigned to Table" wirft
        if op_type.endswith("AddColumnOp") and hasattr(script_op, "column"):
          script_op.column = script_op.column.copy()

        # Falls es ein CreateIndexOp für eine gerade eben erstellte Tabelle ist -> überspringen,
        # da MySQL den Index bereits beim CREATE TABLE angelegt hat.
        if op_type.endswith("CreateIndexOp") and getattr(
            script_op, "table_name", None
        ) in created_table_names:
          logger.debug(
              f"Skipping redundant CreateIndexOp '{getattr(script_op, 'index_name', '')}'"
              f" on newly created table '{script_op.table_name}'"
          )
          return

        try:
          op.invoke(script_op)
        except OperationalError as e:
          # MySQL Error 1061: Duplicate key name
          if (
              isinstance(e.orig, PyMySQLOperationalError)
              and e.orig.args[0] == 1061
          ):
            logger.warning(
                f"Index existiert bereits, wird übersprungen: {e.orig}"
            )
          else:
            raise

      for script_op in upgrade_ops.ops:
        apply_op(script_op)

