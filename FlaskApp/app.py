from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import requests
import urllib.parse
import json
from functools import wraps
from config import (
    QB_CLIENT_ID, QB_CLIENT_SECRET, QB_REDIRECT_URI, QB_BASE_URL,
    QB_OAUTH_URL, QB_GRAPHQL_URL, QB_AUTH_URL, get_headers
)

app = Flask(__name__, 
    static_folder='static',
    static_url_path='/static',
    template_folder='templates')

# Configure session
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['SESSION_COOKIE_SECURE'] = False  # Set to False for development
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Clear session on startup
@app.before_request
def clear_session():
    if request.endpoint == 'index':
        # Clear all flash messages
        if '_flashes' in session:
            del session['_flashes']



@app.route('/')
def index():
    token = session.get("oauth_token")
    realm_id = session.get("realm_id")
    
    if not token or not realm_id:
        return render_template('index.html', token=None)
    
    return render_template('index.html', token=token)

def fetch_customers(token, realm_id):
    customers = []
    if token and realm_id:
        headers = get_headers(token['access_token'])
        import urllib.parse
        customer_url = f"{QB_BASE_URL}/{realm_id}/query"
        query_str = urllib.parse.urlencode({"query": "SELECT * FROM Customer WHERE Active = true MAXRESULTS 10"})
        full_url = f"{customer_url}?{query_str}"
        try:
            resp = requests.get(full_url, headers=headers)
            resp_json = resp.json()
            if resp.status_code == 200 and 'QueryResponse' in resp_json:
                customers = resp_json['QueryResponse'].get('Customer', [])[:10]
                # Store customers in session
                session['customers'] = customers
        except Exception as e:
            flash(f"Error fetching customers: {str(e)}", "danger")
    return customers

def fetch_items(token, realm_id):
    items = []
    if token and realm_id:
        headers = get_headers(token['access_token'])
        import urllib.parse
        item_url = f"{QB_BASE_URL}/{realm_id}/query"
        query_str = urllib.parse.urlencode({"query": "SELECT * FROM Item WHERE Active = true MAXRESULTS 10"})
        full_url = f"{item_url}?{query_str}"
        try:
            resp = requests.get(full_url, headers=headers)
            resp_json = resp.json()
            if resp.status_code == 200 and 'QueryResponse' in resp_json:
                items = resp_json['QueryResponse'].get('Item', [])[:10]
                # Store items in session
                session['items'] = items
        except Exception as e:
            flash(f"Error fetching items: {str(e)}", "danger")
    return items

def fetch_custom_fields(token, realm_id):
    custom_fields = []
    if token and realm_id:
        headers = get_headers(token['access_token'])
        
        # Read GraphQL query from file
        try:
            with open(os.path.join(app.static_folder, 'graphql', 'query_custom_field.graphql'), 'r') as file:
                query = file.read()
        except Exception as e:
            error_msg = f"Failed to read GraphQL query file: {str(e)}"
            print(error_msg)
            flash(error_msg, "danger")
            return custom_fields
        
        payload = {"query": query}
        try:
            print("Sending GraphQL request for custom fields...")
            resp = requests.post(QB_GRAPHQL_URL, json=payload, headers=headers)
            print(f"Custom fields response status: {resp.status_code}")
            print(f"Custom fields response: {resp.text}")
            
            resp_json = resp.json()
            if resp.status_code == 200 and resp_json.get('data'):
                edges = resp_json['data']['appFoundationsCustomFieldDefinitions']['edges']
                print(f"Found {len(edges)} custom field edges")
                
                for edge in edges:
                    node = edge['node']
                    if node.get('active', False):
                        transaction_types = []
                        for assoc in node.get('associations', []):
                            if assoc.get('associatedEntity') == '/transactions/Transaction':
                                for sub_assoc in assoc.get('subAssociations', []):
                                    transaction_types.append(sub_assoc.get('associatedEntity', ''))
                        
                        custom_field = {
                            'id': node['id'],
                            'legacyIDV2': node['legacyIDV2'],
                            'label': node['label'],
                            'active': node['active'],
                            'transaction_types': transaction_types,
                            'selected': True
                        }
                        custom_fields.append(custom_field)
                        print(f"Added custom field: {custom_field}")
            else:
                print(f"Error in custom fields response: {resp_json.get('errors', [])}")
        except Exception as e:
            print(f"Exception fetching custom fields: {str(e)}")
            flash(f"Error fetching custom fields: {str(e)}", "danger")
    return custom_fields

@app.route("/login")
def login():
    scopes = [
        "com.intuit.quickbooks.accounting",
        "app-foundations.custom-field-definitions"
    ]
    params = {
        "response_type": "code",
        "client_id": QB_CLIENT_ID,
        "redirect_uri": QB_REDIRECT_URI,
        "scope": " ".join(scopes),
        "state": "random_state_123",  # Send state but don't validate
        "locale": "en-us"
    }
    encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    auth_url = f"{QB_AUTH_URL}?{encoded_params}"
    return redirect(auth_url)

@app.route("/callback")
def callback():
    session.pop('_flashes', None)
    
    # Log all callback parameters for debugging
    print(f"Callback parameters: {dict(request.args)}")
    
    # Check for OAuth errors
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    if error:
        error_msg = f"OAuth Error: {error} - {error_description}"
        print(f"OAuth Error in callback: {error_msg}")
        flash(error_msg, "danger")
        return render_template('index.html', token=None, custom_fields=[])
    
    auth_code = request.args.get('code')
    realm_id = request.args.get('realmId')
    
    if not auth_code or not realm_id:
        error_msg = "Missing code or realmId in callback"
        print(f"Missing parameters: {error_msg}")
        flash(error_msg, "danger")
        return render_template('index.html', token=None, custom_fields=[])
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    auth = (QB_CLIENT_ID, QB_CLIENT_SECRET)
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": QB_REDIRECT_URI
    }
    
    try:
        print(f"Token request data: {data}")
        resp = requests.post(QB_OAUTH_URL, headers=headers, data=data, auth=auth)
        print(f"Token response status: {resp.status_code}")
        print(f"Token response: {resp.text}")
        
        if resp.status_code == 200:
            token_json = resp.json()
            # Store token data in session
            session['oauth_token'] = {
                'access_token': token_json.get('access_token'),
                'refresh_token': token_json.get('refresh_token'),
                'id_token': token_json.get('id_token'),
                'expires_in': token_json.get('expires_in'),
            }
            session['realm_id'] = realm_id
            
            # Initialize all session data after successful authentication
            print("Fetching customers...")
            customers = fetch_customers(session['oauth_token'], realm_id)
            session['customers'] = customers
            print(f"Fetched {len(customers)} customers")
            
            print("Fetching items...")
            items = fetch_items(session['oauth_token'], realm_id)
            session['items'] = items
            print(f"Fetched {len(items)} items")
            
            print("Fetching custom fields...")
            custom_fields = fetch_custom_fields(session['oauth_token'], realm_id)
            session['custom_fields'] = custom_fields
            print(f"Fetched {len(custom_fields)} custom fields")
            print("Custom fields:", custom_fields)
            
            flash("Successfully authenticated with QuickBooks!", "success")
            return render_template('index.html', 
                                token=session['oauth_token'],
                                custom_fields=custom_fields,
                                customers=customers,
                                items=items)
        else:
            error_msg = f"Failed to get tokens. Status: {resp.status_code}, Response: {resp.text}"
            print(f"Token request failed: {error_msg}")
            flash(error_msg, "danger")
            return render_template('index.html', token=None, custom_fields=[])
    except Exception as e:
        error_msg = f"Exception during OAuth token exchange: {str(e)}"
        print(f"Exception in callback: {error_msg}")
        flash(error_msg, "danger")
        return render_template('index.html', token=None, custom_fields=[])

@app.route("/create_custom_field", methods=["POST"])
def create_custom_field():
    session.pop('_flashes', None)
    session.pop('error_code', None)  # Clear any previous error code
    
    custom_field_name = request.form.get("custom_field_name")
    token = session.get("oauth_token")
    realm_id = session.get("realm_id")
    
    # Read GraphQL mutation from file
    try:
        with open(os.path.join(app.static_folder, 'graphql', 'custom_field.graphql'), 'r') as file:
            mutation = file.read()
    except Exception as e:
        error_msg = f"Failed to read GraphQL mutation file: {str(e)}"
        print(error_msg)
        flash(error_msg, "danger")
        return redirect(url_for('index'))
    
    # Read variables template from file
    try:
        with open(os.path.join(app.static_folder, 'graphql', 'custom_field_variables.json'), 'r') as file:
            variables_template = json.load(file)
            # Replace the placeholder with actual value
            variables_template['input']['label'] = custom_field_name
    except Exception as e:
        error_msg = f"Failed to read variables template file: {str(e)}"
        print(error_msg)
        flash(error_msg, "danger")
        return redirect(url_for('index'))
    
    payload = {
        "query": mutation,
        "variables": variables_template
    }
    try:
        print(f"Creating new custom field with name: {custom_field_name}")
        resp = requests.post(QB_GRAPHQL_URL, json=payload, headers=get_headers(token['access_token']))
        resp_json = resp.json()
        
        if resp_json.get('errors'):
            for error in resp_json['errors']:
                error_code = error.get('extensions', {}).get('errorCode', {}).get('errorCode')
                
                # Store the error code in session
                session['error_code'] = error_code
                
                # Handle specific error codes
                if error_code == 'CUSTOM_FIELD_ASSOCIATED_ENTITY_LIMIT_EXCEEDED':
                    flash("You've exceeded the maximum number of associated entities for custom fields.", "danger")
                elif error_code == 'LABEL_ALREADY_EXISTS':
                    flash("Custom field already exists", "danger")
                else:
                    flash("Unknown error", "danger")
                return redirect(url_for('index'))
        
        # After successful custom field creation, refresh custom fields
        custom_fields = fetch_custom_fields(token, realm_id)
        session['custom_fields'] = custom_fields
        session['custom_field_name'] = custom_field_name  # Store the created custom field name
        
        flash("Custom field created successfully.", "success")
        return redirect(url_for('index'))
    except Exception as e:
        error_msg = f"Failed to create custom field: {str(e)}"
        print(error_msg)
        flash(error_msg, "danger")
        return redirect(url_for('index'))

@app.route("/create_invoice", methods=["POST"])
def create_invoice():

    session.pop('invoice_id', None)
    session.pop('invoice_deep_link', None)
    
    amount = request.form.get("amount")
    token = session.get("oauth_token")
    realm_id = session.get("realm_id")
    custom_field_id = request.form.get("custom_field_id")
    custom_field_value = request.form.get("custom_field_value")
    customer_id = request.form.get("customer_id")
    item_id = request.form.get("item_id")
    item_name = request.form.get("item_name")
    
    if not token or not realm_id or not custom_field_id or not customer_id or not item_id:
        flash("Connect to QuickBooks and select all required fields.", "danger")
        return redirect(url_for('index'))
    
    headers = get_headers(token['access_token'])
    headers["Accept-Encoding"] = "gzip, deflate"
    
    url = f"{QB_BASE_URL}/{realm_id}/invoice?minorversion=75&include=enhancedAllCustomFields"
    data = {
        "Line": [
            {
                "Amount": float(amount),
                "DetailType": "SalesItemLineDetail",
                "SalesItemLineDetail": {
                    "ItemRef": {"value": item_id, "name": item_name}
                }
            }
        ],
        "CustomerRef": {"value": customer_id},
        "CustomField": [
            {
                "DefinitionId": custom_field_id,
                "Type": "StringType",
                "StringValue": custom_field_value
            }
        ]
    }
    
    try:
        print(f"Sending invoice creation request to: {url}")
        print(f"Request data: {json.dumps(data, indent=2)}")
        
        resp = requests.post(url, json=data, headers=headers)
        print(f"Invoice creation response status: {resp.status_code}")
        print(f"Invoice creation response: {resp.text}")
        
        if resp.status_code == 200:
            resp_json = resp.json()
            if 'Invoice' in resp_json and 'Id' in resp_json['Invoice']:
                inv_id = resp_json['Invoice']['Id']
                session['invoice_id'] = inv_id
                
                # Create deep link
                deep_link = f"https://app.qbo.intuit.com/app/invoice?txnId={inv_id}&companyId={realm_id}"
                session['invoice_deep_link'] = deep_link
                
                flash(f"Success! Invoice created with ID: {inv_id}", "success")
            else:
                error_msg = "Invoice created but ID not found in response"
                print(error_msg)
                print(f"Response JSON: {json.dumps(resp_json, indent=2)}")
                flash(error_msg, "warning")
        else:
            error_msg = f"Failed to create invoice. Status: {resp.status_code}, Response: {resp.text}"
            print(error_msg)
            flash(error_msg, "danger")
    except requests.exceptions.ContentDecodingError as e:
        error_msg = f"Error creating invoice: Content decoding error - {str(e)}"
        print(error_msg)
        flash(error_msg, "danger")
    except Exception as e:
        error_msg = f"Error creating invoice: {str(e)}"
        print(error_msg)
        flash(error_msg, "danger")
    
    return redirect(url_for('index'))

@app.route('/read_custom_fields')
def read_custom_fields():
    token = session.get("oauth_token")
    realm_id = session.get("realm_id")
    if not token or not realm_id:
        flash("Please connect to QuickBooks first.", "danger")
        return redirect(url_for('index'))
    
    custom_fields = session.get('custom_fields', [])
    if not custom_fields:
        flash("You do not have any active custom fields", "info")
        return render_template("index.html", 
                             show_custom_field_selection=False,
                             token=token)
    
    return render_template("index.html", 
                         show_custom_field_selection=True,
                         token=token)

@app.route('/deactivate_custom_fields', methods=['POST'])
def deactivate_custom_fields():
    token = session.get("oauth_token")
    realm_id = session.get("realm_id")
    if not token or not realm_id:
        flash("Please connect to QuickBooks first.", "danger")
        return redirect(url_for('index'))
    
    headers = get_headers(token['access_token'])
    selected_ids = request.form.getlist('selected_custom_fields')
    query = '''
    query {
      appFoundationsCustomFieldDefinitions {
        edges {
          node {
            id
            legacyIDV2
            label
            active
          }
        }
      }
    }
    '''
    payload = {"query": query}
    resp = requests.post(QB_GRAPHQL_URL, json=payload, headers=headers)
    resp_json = resp.json()
    if resp.status_code == 200 and resp_json.get('data'):
        edges = resp_json['data']['appFoundationsCustomFieldDefinitions']['edges']
        for edge in edges:
            node = edge['node']
            if node['id'] not in selected_ids and node['active']:
                legacy_id = node.get('legacyIDV2', '')
                mutation = '''
                mutation {
                  appFoundationsUpdateCustomFieldDefinition(
                    input: {
                      id: "%s"
                      legacyIDV2: "%s"
                      label: "%s"
                      active: false
                    }
                  ) {
                    id
                    active
                  }
                }
                ''' % (node['id'], legacy_id, node['label'].replace('"', '\\"').replace('\\', '\\\\'))
                payload_mut = {"query": mutation}
                resp_mut = requests.post(QB_GRAPHQL_URL, json=payload_mut, headers=headers)
                resp_json_mut = resp_mut.json()
                if "errors" in resp_json_mut:
                    flash(f"Failed to deactivate {node['label']}: {resp_json_mut['errors']}", "danger")
            elif node['id'] in selected_ids and not node['active']:
                legacy_id = node.get('legacyIDV2', '')
                mutation = '''
                mutation {
                  appFoundationsUpdateCustomFieldDefinition(
                    input: {
                      id: "%s"
                      legacyIDV2: "%s"
                      label: "%s"
                      active: true
                    }
                  ) {
                    id
                    active
                  }
                }
                ''' % (node['id'], legacy_id, node['label'].replace('"', '\\"').replace('\\', '\\\\'))
                payload_mut = {"query": mutation}
                resp_mut = requests.post(QB_GRAPHQL_URL, json=payload_mut, headers=headers)
                resp_json_mut = resp_mut.json()
                if "errors" in resp_json_mut:
                    flash(f"Failed to activate {node['label']}: {resp_json_mut['errors']}", "danger")
    flash("Custom fields updated successfully.", "success")
    return redirect(url_for('index'))

def get_api_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def validate_quickbooks_session():
    token = session.get("oauth_token")
    realm_id = session.get("realm_id")
    if not token or not realm_id:
        flash("Please connect to QuickBooks first.", "danger")
        return None, None
    return token, realm_id

class QuickBooksAPI:
    def __init__(self, token, realm_id):
        self.token = token
        self.realm_id = realm_id
        self.headers = get_api_headers(token)
        
    def make_request(self, method, endpoint, data=None):
        # Common request handling logic
        pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)