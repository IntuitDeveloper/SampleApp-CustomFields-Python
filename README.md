# QuickBooks Custom Fields Integration

A simple Flask application that demonstrates integration with QuickBooks Online API to create custom fields and attach those custom fields to invoices.

## App features

- OAuth 2.0 authentication with QuickBooks Online
- Create and read custom field from QuickBooks
- Attach invoice to custom fields

## Prerequisites

- Python 3.8 or higher
- QuickBooks Developer account with OAuth 2.0 credentials


## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone 
   cd Custom-Fields-Python
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4.**Set environment variables**
Create a `.env` file with your QuickBooks credentials:
```
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
REDIRECT_URI=your_redirect_uri
```
## Configuration

1. Update `config.py` with your QuickBooks API credentials
2. Set up your QuickBooks Developer account and configure the OAuth2 redirect URI
3. For local development, use ngrok to create a public URL:
```bash
ngrok http 5000
```

## Running the Application

1. **Start the Flask Server**
   ```bash
   python app.py
   ```
2. **Access the Application**
   Access the application at `http://localhost:5000`

## Usage Guide

### Authentication
1. Click the "Connect to QuickBooks" button
2. Log in to your QuickBooks account
3. Authorize the application to access your QuickBooks data

### Creating Custom Fields
1. Enter a name for your custom field in the "Create Custom Field" section
2. Click "Create Custom Field" to create a new custom field in QuickBooks

### Creating Invoices
1. Select a customer from the dropdown
2. Select an item from the dropdown
3. Enter the amount
4. Select a custom field and enter its value
5. Click "Create Invoice" 

### Managing Custom Fields
- View all active custom fields in the dashboard
- Deactivate custom fields using the provided interface
- Reactivate deactivated custom fields as needed

## Project Structure

```
Custom-Fields-Python/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── .env.template      # Template for environment variables
├── static/            # Static assets (CSS, images)
│   ├── styles.css
│   └── images/
└── templates/         # HTML templates
    └── index.html
```

## Security Notes

- Never commit your `.env` file to version control
- Keep your QuickBooks credentials secure
- Use environment variables for all sensitive information
- The `.env` file is automatically ignored by Git

## Troubleshooting

1. **Authentication Issues**
   - Ensure your OAuth credentials are correct in the `.env` file
   - Check that the redirect URI matches your QuickBooks app settings
   - Verify admin is connecting to Quickbooks account

2. **Environment Setup Issues**
   - Make sure the `.env` file exists and contains all required variables
   - Verify that environment variables are being loaded correctly
   - Check that the virtual environment is activated

3. **API Errors**
   - Check the application logs for detailed error messages
   - Verify your QuickBooks subscription includes API access
   - Ensure you're using the correct API endpoints for your QuickBooks environment

## Contributing

Feel free to submit issues and enhancement requests. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
