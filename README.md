# SQL Query Generator with AI Analysis

A Django-based web application that uses OpenAI's GPT to generate SQL queries from natural language and provides AI-powered analysis of query results. The application processes large transaction datasets stored in Parquet format and provides an intuitive interface for querying and analyzing transaction data.

## Features

- 🤖 **AI-Powered SQL Generation**: Convert natural language queries into SQL using OpenAI GPT-3.5-turbo
- 📊 **Interactive Web Interface**: Simple, clean web form for submitting queries and viewing results
- 🔍 **Automatic Data Analysis**: AI-generated insights and analysis of query results
- 💾 **Large Dataset Support**: Efficiently load and process large Parquet files (600MB+) using Polars and PyArrow
- 🔒 **SQL Safety Validation**: Automatic validation to prevent dangerous SQL operations
- 🌐 **Case-Insensitive Search**: Smart text matching that handles case variations automatically
- 📈 **PostgreSQL Integration**: Full support for PostgreSQL database with Django ORM

## Technology Stack

- **Backend**: Django 5.2.8
- **Database**: PostgreSQL (via psycopg2)
- **AI/ML**: OpenAI API (GPT-3.5-turbo)
- **Data Processing**: Polars, PyArrow
- **Environment Management**: python-dotenv

## Prerequisites

- Python 3.9+
- PostgreSQL database
- OpenAI API key
- Virtual environment (recommended)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SYNAPSEPARQUET
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate.bat  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install django psycopg2-binary python-dotenv polars openai
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # Django Secret Key (generate a new one for production)
   SECRET_KEY=your-secret-key-here

   # PostgreSQL Database Configuration
   DB_NAME=the_project_db
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5432

   # OpenAI API Key
   OPENAI_API_KEY=your-openai-api-key-here
   ```

5. **Set up PostgreSQL database**
   
   Create a PostgreSQL database:
   ```sql
   CREATE DATABASE the_project_db;
   ```

6. **Run Django migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Usage

### Web Interface

1. **Start the Django development server**
   ```bash
   python manage.py runserver
   ```

2. **Open your browser**
   Navigate to `http://127.0.0.1:8000/`

3. **Enter a query**
   Type a natural language query in the form, for example:
   - "Show me the top 10 transactions by amount"
   - "List all transactions with Apple Pay wallet type"
   - "Count transactions by merchant city"
   - "Show me transactions over 1000 KZT in Almaty"

4. **View results**
   - Generated SQL query
   - AI-powered analysis of the results
   - Formatted data table with query results

### Command Line Interface

You can also use the command-line script:

```bash
python main.py "Show me transactions with wallet type of Apple Pay"
```

Or run interactively:
```bash
python main.py
# Then enter your query when prompted
```

### Loading Data from Parquet Files

To load transaction data from a Parquet file into the database:

```bash
python manage.py load_parquet
```

This command:
- Processes large Parquet files efficiently (handles 600MB+ files)
- Loads data in batches to avoid memory issues
- Shows progress updates during loading
- Uses streaming mode for optimal performance

**Note**: Place your Parquet file as `example_dataset.parquet` in the project root, or modify the command to point to your file.

## Project Structure

```
SYNAPSEPARQUET/
├── .env                      # Environment variables (not in git)
├── .gitignore                # Git ignore rules
├── main.py                   # Command-line interface script
├── manage.py                 # Django management script
├── example_dataset.parquet   # Sample data file (not in git)
│
├── my_app/                   # Main Django application
│   ├── models.py            # Transaction model definition
│   ├── views.py             # Web views and business logic
│   ├── utils.py             # Shared utilities (SYSTEM_PROMPT, validation)
│   ├── admin.py             # Django admin configuration
│   │
│   └── management/
│       └── commands/
│           └── load_parquet.py  # Management command for loading Parquet files
│
├── the_project/              # Django project settings
│   ├── settings.py          # Django configuration
│   ├── urls.py              # URL routing
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
│
└── templates/
    └── my_app/
        └── index.html       # Main web interface template
```

## Database Schema

The `Transaction` model includes the following fields:

- `transaction_id` - Unique transaction identifier
- `transaction_timestamp` - Date and time of transaction
- `card_id` - Card identifier
- `expiry_date` - Card expiry date
- `issuer_bank_name` - Name of issuing bank
- `merchant_id` - Merchant identifier
- `merchant_mcc` - Merchant category code
- `mcc_category` - MCC category description
- `merchant_city` - City where transaction occurred
- `transaction_type` - Type of transaction
- `transaction_amount_kzt` - Transaction amount in KZT
- `original_amount` - Original transaction amount
- `transaction_currency` - Currency code
- `acquirer_country_iso` - Acquirer country ISO code
- `pos_entry_mode` - Point of sale entry mode
- `wallet_type` - Type of wallet (e.g., Apple Pay, Google Pay)
- `__index_level_0__` - Internal index field

## Features in Detail

### SQL Safety

The application includes built-in SQL safety validation:
- Only read-only queries are allowed (SELECT, WITH, EXPLAIN)
- Dangerous operations are blocked (DROP, DELETE, UPDATE, INSERT, etc.)
- Automatic validation before query execution

### Case-Insensitive Matching

Text searches automatically use case-insensitive matching:
- Uses PostgreSQL's `ILIKE` operator for pattern matching
- Uses `LOWER()` function for exact matches
- Handles variations like "apple pay", "Apple Pay", "APPLE PAY"

### Large File Processing

The `load_parquet` command is optimized for large files:
- Processes data in batches (1,000 rows at a time)
- Uses PyArrow's batch iterator for memory efficiency
- Handles files with single large row groups
- Shows progress updates during loading

### AI Analysis

After executing a query, the application:
- Sends results to OpenAI for analysis
- Generates insights, patterns, and trends
- Provides actionable recommendations
- Limits analysis to first 100 rows to manage token usage

## Configuration

### Database Settings

Edit `the_project/settings.py` or update `.env` file to change database configuration:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', ''),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

### OpenAI Model

The default model is `gpt-3.5-turbo`. To change it, modify:
- `my_app/views.py` (line 135 and 154)
- `main.py` (line 282 and 316)

## Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL is running
- Verify database credentials in `.env`
- Check that the database exists

### OpenAI API Errors

- Verify your API key in `.env`
- Check your OpenAI account has available credits
- Ensure you have internet connectivity

### Memory Issues with Large Files

- The `load_parquet` command is optimized for large files
- If issues persist, reduce `batch_size` in `load_parquet.py`
- Ensure sufficient system RAM

## Security Notes

- Never commit `.env` file to version control
- Use strong `SECRET_KEY` in production
- Restrict database access appropriately
- Keep OpenAI API key secure
- Review generated SQL queries before execution in production

## Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Django Admin

Access the admin interface at `http://127.0.0.1:8000/admin/` (requires superuser account):

```bash
python manage.py createsuperuser
```

## License

[Specify your license here]

## Contributing

[Add contribution guidelines if applicable]

## Support

[Add support information if applicable]

