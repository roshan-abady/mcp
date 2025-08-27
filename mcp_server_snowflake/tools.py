# Copyright 2025 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Annotated, Optional

import requests
from pydantic import Field

import mcp_server_snowflake.prompts as prompts
from mcp_server_snowflake.environment import construct_snowflake_post
from mcp_server_snowflake.utils import SnowflakeException, SnowflakeResponse

sfse = SnowflakeResponse()


@sfse.snowflake_response(api="search")
async def query_cortex_search(
    snowflake_service,
    service_name: str,
    database_name: str,
    schema_name: str,
    query: str,
    columns: Optional[list[str]] = None,
    filter_query: Optional[dict] = {},
    limit: Optional[int] = 10,
) -> dict:
    """
    Query a Cortex Search Service using the REST API.

    Performs semantic search against a configured Cortex Search service using
    Snowflake's REST API. Supports filtering and column selection for refined
    search results.

    Parameters
    ----------
    snowflake_service
    service_name : str
        Name of the Cortex Search Service
    database_name : str
        Target database containing the search service
    schema_name : str
        Target schema containing the search service
    query : str
        The search query string to submit to Cortex Search
    columns : list[str], optional
        List of columns to return for each relevant result, by default None
    filter_query : dict, optional
        Filter query to apply to search results, by default {}
    limit : int, optional
        Limit on the number of results to return, by default 10

    Returns
    -------
    dict
        JSON response from the Cortex Search API containing search results

    Raises
    ------
    SnowflakeException
        If the API request fails or returns an error status code

    References
    ----------
    Snowflake Cortex Search REST API:
    https://docs.snowflake.com/developer-guide/snowflake-rest-api/reference/cortex-search-service
    """
    host, headers = construct_snowflake_post(
        service=snowflake_service,
        api_path=f"/api/v2/databases/{database_name}/schemas/{schema_name}/cortex-search-services/{service_name}:query",
    )

    if filter_query is None:
        filter_query = {}

    payload = {
        "query": query,
        "filter": filter_query,
        "limit": limit,
    }

    if isinstance(columns, list) and len(columns) > 0:
        payload["columns"] = columns

    response = requests.post(host, headers=headers, json=payload)

    if response.status_code == 200:
        return response

    else:
        raise SnowflakeException(
            tool="Cortex Search",
            status_code=response.status_code,
            message=response.text,
        )


def create_search_wrapper(**kwargs):
    # Extract default values from service configuration
    service_details = kwargs.get("service_details", {})
    default_columns = service_details.get("columns", [])
    default_limit = service_details.get("limit", 10)

    async def search_wrapper(
        query: Annotated[
            str, Field(description="User query to search in search service")
        ],
        columns: Annotated[
            list[str],
            Field(
                description="Optional list of columns to return for each relevant result in the response"
            ),
        ] = default_columns,
        filter_query: Annotated[
            dict, Field(description=prompts.cortex_search_filter_description)
        ] = {},
    ):
        """
        Search using Cortex Search Service.

        Parameters
        ----------
        query : str
            The search query string to submit to Cortex Search
        columns : list[str], optional
            List of columns to return for each relevant result, by default []
        filter_query : dict, optional
            Filter query to apply to search results, by default {}

        Returns
        -------
        dict
            JSON response from the Cortex Search API containing search results

        Raises
        ------
        SnowflakeException
            If the API request fails or returns an error status code
        """

        if kwargs.get("snowflake_service") and kwargs.get("service_details"):
            snowflake_service = kwargs.get("snowflake_service")
            service_details = kwargs.get("service_details")

            return await query_cortex_search(
                snowflake_service=snowflake_service,
                query=query,
                columns=columns,
                filter_query=filter_query,
                service_name=service_details.get("service_name"),
                database_name=service_details.get("database_name"),
                schema_name=service_details.get("schema_name"),
                limit=default_limit,
            )

    return search_wrapper


@sfse.snowflake_response(api="analyst")
async def query_cortex_analyst(
    snowflake_service,
    semantic_model: str,
    query: str,
) -> dict:
    """
    Query Snowflake Cortex Analyst service for natural language to SQL conversion.

    Sends a natural language query to the Cortex Analyst service, which
    interprets the query against a semantic model and generates appropriate
    SQL responses with explanations.

    Parameters
    ----------
    snowflake_service
    semantic_model : str
        Fully qualified path to YAML semantic file or Snowflake Semantic View.
        Examples:
        - "@my_db.my_schema.my_stage/my_semantic_model.yaml"
        - "MY_DB.MY_SCH.MY_SEMANTIC_VIEW"
    query : str
        Natural language query string to submit to Cortex Analyst

    Returns
    -------
    dict
        JSON response from the Cortex Analyst API containing generated SQL,
        explanations, and query results

    Raises
    ------
    SnowflakeException
        If the API request fails or returns an error status code

    Notes
    -----
    The function automatically detects whether the semantic_model parameter
    refers to a YAML file (starts with @ and ends with .yaml) or a semantic view.
    Currently configured for non-streaming responses.
    """
    host, headers = construct_snowflake_post(
        service=snowflake_service,
        api_path="/api/v2/cortex/analyst/message",
    )

    if semantic_model.startswith("@") and semantic_model.endswith(".yaml"):
        semantic_type = "semantic_model_file"
    else:
        semantic_type = "semantic_view"

    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": query,
                    }
                ],
            }
        ],
        semantic_type: semantic_model,
        "stream": False,
    }

    response = requests.post(host, headers=headers, json=payload)

    if response.status_code == 200:
        return response

    else:
        raise SnowflakeException(
            tool="Cortex Analyst",
            status_code=response.status_code,
            message=response.text,
        )


def create_cortex_analyst_wrapper(**kwargs):
    async def cortex_analyst_wrapper(
        query: Annotated[
            str,
            Field(
                description="Rephrased natural language query to submit to Cortex Analyst"
            ),
        ],
    ):
        """
        Query Snowflake Cortex Analyst service for natural language to SQL conversion.

        Parameters
        ----------
        query : str
            The natural language query string to submit to Cortex Analyst

        Returns
        -------
        dict
            JSON response from the Cortex Analyst API containing the generated SQL and related information

        Raises
        ------
        SnowflakeException
            If the API request fails or returns an error status code
        """

        if kwargs.get("snowflake_service") and kwargs.get("service_details"):
            snowflake_service = kwargs.get("snowflake_service")
            service_details = kwargs.get("service_details")

            return await query_cortex_analyst(
                snowflake_service=snowflake_service,
                semantic_model=service_details.get("semantic_model"),
                query=query,
            )

    return cortex_analyst_wrapper


def execute_sql_query(
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
        
    Raises
    ------
    SnowflakeException
        If query execution fails or contains unauthorized operations
    """
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Validate that the query is safe to execute
        query_upper = query.strip().upper()
        
        # Allow SELECT, SHOW, DESCRIBE, EXPLAIN statements
        allowed_prefixes = ['SELECT', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN']
        
        if not any(query_upper.startswith(prefix) for prefix in allowed_prefixes):
            raise SnowflakeException(
                tool="SQL Execution",
                message=f"Only {', '.join(allowed_prefixes)} queries are allowed for security reasons. Got: {query_upper.split()[0] if query_upper.split() else 'empty query'}"
            )
        
        # Add LIMIT if not present and it's a SELECT statement
        if query_upper.startswith('SELECT') and 'LIMIT' not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"
        
        # Execute the query using the service's connection
        with snowflake_service.get_connection(use_dict_cursor=True) as (conn, cursor):
            logger.info(f"Executing SQL query: {query}")
            cursor.execute(query)
            
            # Handle different types of queries
            if query_upper.startswith('SELECT'):
                results = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                
                return json.dumps({
                    "success": True,
                    "query": query,
                    "columns": column_names,
                    "row_count": len(results),
                    "results": results[:limit]  # Ensure we don't exceed limit
                }, indent=2, default=str)
            else:
                # For SHOW, DESCRIBE, etc. - fetch all results
                results = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                
                return json.dumps({
                    "success": True,
                    "query": query,
                    "columns": column_names,
                    "row_count": len(results),
                    "results": results
                }, indent=2, default=str)
            
    except SnowflakeException:
        # Re-raise SnowflakeException as-is
        raise
    except Exception as e:
        logger.error(f"Error executing SQL query: {e}")
        raise SnowflakeException(
            tool="SQL Execution",
            message=f"Query execution failed: {str(e)}"
        )


def create_sql_execution_wrapper(snowflake_service):
    """
    Create a wrapper function for SQL execution.
    
    Parameters
    ----------
    snowflake_service : SnowflakeService
        The Snowflake service instance to use for query execution
        
    Returns
    -------
    callable
        A wrapper function that can be used as an MCP tool
    """
    def sql_execution_wrapper(
        query: Annotated[str, Field(description="SQL query to execute on Snowflake")],
        limit: Annotated[int, Field(description="Maximum number of rows to return", default=100)] = 100,
    ) -> str:
        """Execute SQL queries on Snowflake database."""
        return execute_sql_query(
            snowflake_service=snowflake_service,
            query=query,
            limit=limit
        )
    
    return sql_execution_wrapper
