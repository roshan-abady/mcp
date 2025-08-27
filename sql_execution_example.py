"""
Example SQL execution tool that could be added to the MCP server.
This shows how to extend the server to support direct SQL queries.
"""

import logging
from typing import Annotated, Any, Dict, List, Optional

from fastmcp.tools import Tool
from pydantic import Field

logger = logging.getLogger(__name__)


async def execute_sql_query(
    snowflake_service,
    query: Annotated[str, Field(description="SQL query to execute on Snowflake")],
    limit: Annotated[int, Field(description="Maximum number of rows to return", default=100)] = 100,
) -> str:
    """
    Execute a SQL query on Snowflake and return the results.
    
    This tool allows you to run SQL queries directly against your Snowflake database.
    Use this for data analysis, reporting, and ad-hoc queries.
    
    Parameters
    ----------
    query : str
        The SQL query to execute
    limit : int, default=100
        Maximum number of rows to return to prevent overwhelming responses
        
    Returns
    -------
    str
        JSON formatted results of the query execution
    """
    try:
        # Validate that the query is a SELECT statement for safety
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            return {
                "error": "Only SELECT queries are allowed for security reasons",
                "query": query
            }
        
        # Add LIMIT if not present to prevent huge result sets
        if 'LIMIT' not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"
        
        # Execute the query using the service's connection
        with snowflake_service.get_connection(use_dict_cursor=True) as (conn, cursor):
            logger.info(f"Executing SQL query: {query}")
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Get column names
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []
            
            return {
                "success": True,
                "query": query,
                "columns": column_names,
                "row_count": len(results),
                "results": results[:limit]  # Ensure we don't exceed limit
            }
            
    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


def add_sql_execution_tool(snowflake_service, server):
    """
    Add SQL execution capability to the MCP server.
    
    This function would be called from initialize_tools() to add
    SQL query execution as an available tool.
    """
    
    def sql_wrapper(query: str, limit: int = 100) -> str:
        """Wrapper function for SQL execution tool."""
        import asyncio
        import json
        
        # Since this is called from a non-async context, we need to handle it
        try:
            # For now, we'll call the sync version directly
            result = execute_sql_query_sync(snowflake_service, query, limit)
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"SQL execution failed: {str(e)}",
                "query": query
            }, indent=2)
    
    # Add the tool to the server
    server.add_tool(
        Tool.from_function(
            fn=sql_wrapper,
            name="execute_sql",
            description="Execute SQL SELECT queries on Snowflake database. Use this for data analysis, reporting, and exploring your data."
        )
    )


def execute_sql_query_sync(snowflake_service, query: str, limit: int = 100) -> Dict[str, Any]:
    """
    Synchronous version of SQL execution for use with the MCP tools framework.
    """
    try:
        # Validate that the query is a SELECT statement for safety
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            return {
                "success": False,
                "error": "Only SELECT queries are allowed for security reasons",
                "query": query
            }
        
        # Add LIMIT if not present
        if 'LIMIT' not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"
        
        # Execute the query
        with snowflake_service.get_connection(use_dict_cursor=True) as (conn, cursor):
            logger.info(f"Executing SQL query: {query}")
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Get column names
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []
            
            return {
                "success": True,
                "query": query,
                "columns": column_names,
                "row_count": len(results),
                "results": results[:limit]
            }
            
    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        return {
            "success": False,
            "error": str(e),
            "query": query
        }
