# config.py
# Configuration for QuickBooks API URLs and scopes

import os
from urllib.parse import urlencode
from intuitlib.enums import Scopes

# QuickBooks OAuth2 Configuration
QB_CLIENT_ID = os.getenv('QB_CLIENT_ID', '')
QB_CLIENT_SECRET = os.getenv('QB_CLIENT_SECRET', '')
QB_REDIRECT_URI = os.getenv('QB_REDIRECT_URI', '')
QB_ENVIRONMENT = os.getenv('QB_ENVIRONMENT', 'production')
    
# API Endpoints
QB_BASE_URL = f"https://{'sandbox-quickbooks.api.intuit.com' if QB_ENVIRONMENT == 'sandbox' else 'quickbooks.api.intuit.com'}/v3/company"
QB_OAUTH_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
QB_GRAPHQL_URL = "https://qb.api.intuit.com/graphql"
QB_AUTH_URL = f"https://appcenter.intuit.com/connect/oauth2"
    
# OAuth2 Scopes
QB_SCOPES = [
    "com.intuit.quickbooks.accounting",
    "app-foundations.custom-field-definitions"
]
    
# API Headers
def get_headers(token):
    """Generate standard headers for QuickBooks API requests"""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
# OAuth2 URL Generation
def get_auth_url():
    """Generate the OAuth2 authorization URL"""
    params = {
        "client_id": QB_CLIENT_ID,
        "redirect_uri": QB_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(QB_SCOPES),
        "state": "random_state_123"  # You may want to randomize this for production
    }
    return f"{QB_AUTH_URL}?{urlencode(params)}"
    
# API Query Parameters
def get_query_params(query):
    """Generate URL-encoded query parameters"""
    return urlencode({"query": query})
    
# Invoice Parameters
INVOICE_PARAMS = "?minorversion=70&include=enhancedAllCustomFields"
    
# Deep Link Base URL
QB_DEEP_LINK_BASE = "https://app.qbo.intuit.com/app/invoice"
    
def get_deep_link(invoice_id, realm_id):
    """Generate a deep link to an invoice in QuickBooks"""
    return f"{QB_DEEP_LINK_BASE}?txnId={invoice_id}&companyId={realm_id}"
