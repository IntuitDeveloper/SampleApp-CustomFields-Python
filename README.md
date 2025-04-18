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
   git clone https://github.com/Soumiya-mohan/Custom-Fields-Python.git
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

4. **Setup Config file**
   Replace `your_client_id` and `your_client_secret` with your actual QuickBooks Developer credentials.

## Running the Application

1. **Start the Flask Server**
   ```bash
   python app.py
   ```

2. **Access the Application**
   Open your web browser and navigate to:
   ```
   http://localhost:port
   ```

## Usage Guide

### Authentication
1. Click the "Connect to QuickBooks" button
2. Log in to your QuickBooks account
3. Authorize the application to access your QuickBooks data

### Creating Custom Fields
1. Enter a name for your custom field in the "Create Tag" section
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
├── static/            # Static assets (CSS, images)
│   ├── styles.css
│   └── images/
└── templates/         # HTML templates
    └── index.html
```

## Troubleshooting
   - Ensure your OAuth credentials are correct
   - Check that the redirect URI matches your QuickBooks app settings
   - Verify admin is connecting to Quickbooks account


## Contributing

Feel free to submit issues and enhancement requests. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 