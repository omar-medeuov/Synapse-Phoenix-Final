from django.shortcuts import render
from django.http import JsonResponse
import json
import re
from openai import OpenAI
from openai import APIError, APIConnectionError, AuthenticationError
from django.db import connection
from django.conf import settings
from my_app.utils import SYSTEM_PROMPT, validate_sql_query


def extract_sql_query(response_text):
    """
    Extract SQL query from OpenAI response.
    Handles JSON responses, markdown code blocks, and plain SQL.
    """
    # Remove markdown code blocks if present
    text = response_text.strip()
    
    # Remove ```sql or ``` markers
    if text.startswith('```'):
        lines = text.split('\n')
        # Remove first line (```sql or ```)
        if lines[0].startswith('```'):
            lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        text = '\n'.join(lines)
    
    # Clean up whitespace
    text = text.strip()
    
    # Try to parse as JSON (in case OpenAI returns JSON format)
    try:
        json_data = json.loads(text)
        # If it's a dict with a 'query' key, extract it
        if isinstance(json_data, dict) and 'query' in json_data:
            text = json_data['query']
        # If it's a dict with 'sql' key
        elif isinstance(json_data, dict) and 'sql' in json_data:
            text = json_data['sql']
    except (json.JSONDecodeError, ValueError):
        # Not JSON, use text as-is
        pass
    
    return text.strip()


def validate_sql_safety(sql_query):
    """
    Validate that the SQL query is safe to execute (read-only operations only).
    Blocks destructive operations like DROP, DELETE, UPDATE, INSERT, etc.
    Returns (is_safe, error_message)
    """
    sql_upper = sql_query.upper().strip()
    
    # Block dangerous/destructive operations
    dangerous_keywords = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 
        'TRUNCATE', 'EXEC', 'EXECUTE', 'GRANT', 'REVOKE', 'COMMIT', 
        'ROLLBACK', 'LOCK', 'UNLOCK'
    ]
    
    # Check for dangerous keywords (as standalone words, not part of other words)
    for keyword in dangerous_keywords:
        # Match keyword as a whole word (not part of another word)
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_upper):
            return False, f"Dangerous SQL operation detected: {keyword}"
    
    return True, None


def execute_sql_query(sql_query):
    """
    Execute SQL query against the database and return results.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            
            # Get column names
            columns = [col[0] for col in cursor.description] if cursor.description else []
            
            # Fetch all results
            rows = cursor.fetchall()
            
            return columns, rows
    except Exception as e:
        raise Exception(f"Database error: {str(e)}")


def index(request):
    """
    Main index page with form for SQL query generation.
    """
    context = {
        'error': None,
        'sql_query': None,
        'columns': None,
        'rows': None,
        'prompt': None,
    }
    
    if request.method == 'POST':
        prompt = request.POST.get('prompt', '').strip()
        context['prompt'] = prompt
        
        if not prompt:
            context['error'] = "Please enter a prompt."
            return render(request, 'my_app/index.html', context)
        
        # Validate that the query is SQL-related
        if not validate_sql_query(prompt):
            context['error'] = "This service only accepts SQL query requests for the transaction table. Please provide a SQL-related question."
            return render(request, 'my_app/index.html', context)
        
        # Load OpenAI API key
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            context['error'] = "OpenAI API key not found in .env file."
            return render(request, 'my_app/index.html', context)
        
        try:
            # Initialize OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Send request to OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            
            # Get the SQL query from response
            response_text = response.choices[0].message.content
            
            if response_text.startswith("ERROR:"):
                context['error'] = response_text
                return render(request, 'my_app/index.html', context)
            
            # Extract SQL query from response
            sql_query = extract_sql_query(response_text)
            context['sql_query'] = sql_query
            
            # Validate SQL safety
            is_safe, error_msg = validate_sql_safety(sql_query)
            if not is_safe:
                context['error'] = f"SQL Safety Error: {error_msg}"
                return render(request, 'my_app/index.html', context)
            
            # Execute SQL query against database
            try:
                columns, rows = execute_sql_query(sql_query)
                context['columns'] = columns
                context['rows'] = rows
            except Exception as db_error:
                context['error'] = f"Database Error: {str(db_error)}"
                return render(request, 'my_app/index.html', context)
            
        except AuthenticationError:
            context['error'] = "Invalid API key. Please check your API key in .env file."
            return render(request, 'my_app/index.html', context)
        except APIConnectionError as e:
            context['error'] = f"Network connection failed: {str(e)}"
            return render(request, 'my_app/index.html', context)
        except APIError as e:
            context['error'] = f"OpenAI API error: {str(e)}"
            return render(request, 'my_app/index.html', context)
        except Exception as e:
            context['error'] = f"Unexpected error: {str(e)}"
            return render(request, 'my_app/index.html', context)
    
    return render(request, 'my_app/index.html', context)
