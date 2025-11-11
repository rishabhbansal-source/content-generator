"""DBML schema parser to extract database structure information."""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class TableColumn:
    """Represents a database column."""
    name: str
    data_type: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_unique: bool = False
    is_not_null: bool = False
    default_value: Optional[str] = None
    references: Optional[str] = None
    note: Optional[str] = None


@dataclass
class Table:
    """Represents a database table."""
    name: str
    columns: List[TableColumn] = field(default_factory=list)
    note: Optional[str] = None
    relationships: List[str] = field(default_factory=list)


class DBMLParser:
    """Parse DBML schema file to extract database structure."""

    def __init__(self, dbml_file_path: str):
        """
        Initialize DBML parser.

        Args:
            dbml_file_path: Path to the DBML file
        """
        self.dbml_file_path = dbml_file_path
        self.tables: Dict[str, Table] = {}
        self._parse()

    def _parse(self):
        """Parse the DBML file."""
        with open(self.dbml_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract all table definitions
        table_pattern = r'Table\s+(\w+)\s*\{([^}]+)\}'
        matches = re.finditer(table_pattern, content, re.MULTILINE | re.DOTALL)

        for match in matches:
            table_name = match.group(1)
            table_body = match.group(2)
            self._parse_table(table_name, table_body)

    def _parse_table(self, table_name: str, table_body: str):
        """
        Parse a single table definition.

        Args:
            table_name: Name of the table
            table_body: Body content of the table definition
        """
        table = Table(name=table_name)

        # Parse columns
        lines = table_body.strip().split('\n')
        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('//'):
                continue

            # Extract table note
            if line.startswith('Note:'):
                table.note = line.replace('Note:', '').strip().strip("'\"")
                continue

            # Parse column definition
            column = self._parse_column(line)
            if column:
                table.columns.append(column)

        self.tables[table_name] = table

    def _parse_column(self, line: str) -> Optional[TableColumn]:
        """
        Parse a column definition line.

        Args:
            line: Column definition line

        Returns:
            TableColumn object or None
        """
        # Basic pattern: column_name data_type [attributes]
        parts = line.split(None, 1)
        if len(parts) < 2:
            return None

        column_name = parts[0]
        remainder = parts[1]

        # Extract data type
        data_type_match = re.match(r'(\w+(?:\(\d+\))?)', remainder)
        if not data_type_match:
            return None

        data_type = data_type_match.group(1)

        # Parse attributes in brackets
        column = TableColumn(name=column_name, data_type=data_type)

        # Check for attributes
        if '[' in remainder:
            attrs_match = re.search(r'\[([^\]]+)\]', remainder)
            if attrs_match:
                attrs = attrs_match.group(1)
                self._parse_column_attributes(column, attrs)

        return column

    def _parse_column_attributes(self, column: TableColumn, attrs: str):
        """
        Parse column attributes.

        Args:
            column: TableColumn object to update
            attrs: Attributes string
        """
        # Split attributes by comma (outside of quotes and parentheses)
        attr_list = [attr.strip() for attr in attrs.split(',')]

        for attr in attr_list:
            # Primary key
            if attr == 'pk' or attr == 'primary key':
                column.is_primary_key = True

            # Unique
            elif attr == 'unique':
                column.is_unique = True

            # Not null
            elif attr == 'not null':
                column.is_not_null = True

            # Foreign key reference
            elif attr.startswith('ref:'):
                column.is_foreign_key = True
                # Extract reference (e.g., "ref: > table.column")
                ref_match = re.search(r'ref:\s*[>-]+\s*([\w.]+)', attr)
                if ref_match:
                    column.references = ref_match.group(1)

            # Default value
            elif attr.startswith('default:'):
                default_match = re.search(r'default:\s*(.+)', attr)
                if default_match:
                    column.default_value = default_match.group(1).strip()

            # Note
            elif attr.startswith('note:'):
                note_match = re.search(r"note:\s*['\"](.+)['\"]", attr)
                if note_match:
                    column.note = note_match.group(1)

    def get_table(self, table_name: str) -> Optional[Table]:
        """
        Get table by name.

        Args:
            table_name: Name of the table

        Returns:
            Table object or None
        """
        return self.tables.get(table_name)

    def get_all_table_names(self) -> List[str]:
        """
        Get list of all table names.

        Returns:
            List of table names
        """
        return list(self.tables.keys())

    def get_related_tables(self, table_name: str) -> Set[str]:
        """
        Get all tables related to the given table through foreign keys.

        Args:
            table_name: Name of the table

        Returns:
            Set of related table names
        """
        related = set()
        table = self.get_table(table_name)

        if not table:
            return related

        # Find tables this table references
        for column in table.columns:
            if column.references:
                ref_table = column.references.split('.')[0]
                related.add(ref_table)

        # Find tables that reference this table
        for other_table_name, other_table in self.tables.items():
            for column in other_table.columns:
                if column.references and column.references.startswith(f"{table_name}."):
                    related.add(other_table_name)

        return related

    def get_schema_summary(self) -> str:
        """
        Get a formatted summary of the database schema.

        Returns:
            Formatted schema summary
        """
        summary = f"Database Schema Summary\n"
        summary += f"=" * 50 + "\n\n"
        summary += f"Total Tables: {len(self.tables)}\n\n"

        for table_name, table in sorted(self.tables.items()):
            summary += f"\nTable: {table_name}\n"
            if table.note:
                summary += f"  Note: {table.note}\n"

            summary += f"  Columns ({len(table.columns)}):\n"
            for col in table.columns:
                flags = []
                if col.is_primary_key:
                    flags.append("PK")
                if col.is_foreign_key:
                    flags.append(f"FK -> {col.references}")
                if col.is_unique:
                    flags.append("UNIQUE")

                flag_str = f" [{', '.join(flags)}]" if flags else ""
                summary += f"    - {col.name}: {col.data_type}{flag_str}\n"

        return summary

    def get_table_info_for_llm(self, table_names: Optional[List[str]] = None) -> str:
        """
        Get table information formatted for LLM context.

        Args:
            table_names: Specific tables to include (all if None)

        Returns:
            Formatted table information
        """
        if table_names is None:
            table_names = self.get_all_table_names()

        info = "Database Schema Information:\n\n"

        for table_name in table_names:
            table = self.get_table(table_name)
            if not table:
                continue

            info += f"Table: {table_name}\n"
            if table.note:
                info += f"Description: {table.note}\n"

            info += "Columns:\n"
            for col in table.columns:
                info += f"  - {col.name} ({col.data_type})"
                if col.note:
                    info += f" - {col.note}"
                if col.is_foreign_key and col.references:
                    info += f" -> References {col.references}"
                info += "\n"

            # Add related tables
            related = self.get_related_tables(table_name)
            if related:
                info += f"Related Tables: {', '.join(sorted(related))}\n"

            info += "\n"

        return info
