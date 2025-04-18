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
app.secret_key = 'your-secret-key-123'  # Replace with your own secret key

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
        query = '''
        query {
          appFoundationsCustomFieldDefinitions {
            edges {
              node {
                id
                legacyIDV2
                label
                active
                associations {
                  associatedEntity
                  active
                  validationOptions { required }
                  allowedOperations
                  associationCondition
                  subAssociations {
                    associatedEntity
                    active
                    allowedOperations
                  }
                }
              }
            }
          }
        }
        '''
        payload = {"query": query}
        try:
            resp = requests.post(QB_GRAPHQL_URL, json=payload, headers=headers)
            resp_json = resp.json()
            if resp.status_code == 200 and resp_json.get('data'):
                edges = resp_json['data']['appFoundationsCustomFieldDefinitions']['edges']
                for edge in edges:
                    node = edge['node']
                    if node.get('active', False):
                        transaction_types = []
                        for assoc in node.get('associations', []):
                            if assoc.get('associatedEntity') == '/transactions/Transaction':
                                for sub_assoc in assoc.get('subAssociations', []):
                                    transaction_types.append(sub_assoc.get('associatedEntity', ''))
                        
                        custom_fields.append({
                            'id': node['id'],
                            'legacyIDV2': node['legacyIDV2'],
                            'label': node['label'],
                            'active': node['active'],
                            'transaction_types': transaction_types,
                            'selected': True
                        })
        except Exception as e:
            flash(f"Error fetching custom fields: {str(e)}", "danger")
    return custom_fields

@app.route("/login")
def login():

    scopes = [
        "com.intuit.quickbooks.accounting",
        "app-foundations.custom-field-definitions"
    ]
    params = {
        "client_id": QB_CLIENT_ID,
        "redirect_uri": QB_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": "random_state_123"
    }
    auth_url = f"{QB_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route("/callback")
def callback():
    session.pop('_flashes', None)
    
    auth_code = request.args.get('code')
    realm_id = request.args.get('realmId')
    if not auth_code or not realm_id:
        flash("Missing code or realmId in callback.", "danger")
        return redirect(url_for('index'))
    
    headers = {"Accept": "application/json"}
    auth = (QB_CLIENT_ID, QB_CLIENT_SECRET)
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": QB_REDIRECT_URI
    }
    resp = requests.post(QB_OAUTH_URL, headers=headers, data=data, auth=auth)
    if resp.status_code == 200:
        token_json = resp.json()
        session['oauth_token'] = {
            'access_token': token_json.get('access_token'),
            'refresh_token': token_json.get('refresh_token'),
            'id_token': token_json.get('id_token'),
            'expires_in': token_json.get('expires_in'),
        }
        session['realm_id'] = realm_id
        
        # Initialize all session data after successful authentication
        customers = fetch_customers(session['oauth_token'], realm_id)
        items = fetch_items(session['oauth_token'], realm_id)
        custom_fields = fetch_custom_fields(session['oauth_token'], realm_id)
        
        session['customers'] = customers
        session['items'] = items
        session['custom_fields'] = custom_fields
        
        flash("Successfully authenticated with QuickBooks!", "success")
    else:
        flash(f"Failed to get tokens: {resp.text}", "danger")
    return redirect(url_for('index'))

@app.route("/create_tag", methods=["POST"])
def create_tag():
    session.pop('_flashes', None)
    
    tag_name = request.form.get("tag_name")
    token = session.get("oauth_token")
    realm_id = session.get("realm_id")
    if not token or not realm_id:
        flash("Please connect to QuickBooks first.", "danger")
        return redirect(url_for('index'))
    
    headers = get_headers(token['access_token'])
    mutation = '''
    mutation AppFoundationsCreateCustomFieldDefinition($input: AppFoundations_CustomFieldDefinitionCreateInput!) {
      appFoundationsCreateCustomFieldDefinition(input: $input) {
        label
        active
        associations {
          associatedEntity
          active
          validationOptions { required }
          allowedOperations
          associationCondition
          subAssociations {
            associatedEntity
            active
            allowedOperations
          }
        }
        dataType
        dropDownOptions {
          value
          active
          order
        }
      }
    }
    '''
    variables = {
        "input": {
            "label": tag_name,
            "associations": [
                {
                    "validationOptions": {"required": False},
                    "associatedEntity": "/transactions/Transaction",
                    "active": True,
                    "allowedOperations": [],
                    "associationCondition": "INCLUDED",
                    "subAssociations": [
                        {
                            "associatedEntity": "SALE_INVOICE",
                            "active": True,
                            "allowedOperations": []
                        }
                    ]
                },
                {
                    "associatedEntity": "/network/Contact",
                    "active": True,
                    "validationOptions": {"required": False},
                    "allowedOperations": [],
                    "associationCondition": "INCLUDED",
                    "subAssociations": [
                        {
                            "associatedEntity": "CUSTOMER",
                            "active": True,
                            "allowedOperations": []
                        }
                    ]
                }
            ],
            "dataType": "STRING",
            "active": True
        }
    }
    payload = {
        "query": mutation,
        "variables": variables
    }
    try:
        resp = requests.post(QB_GRAPHQL_URL, json=payload, headers=headers)
        resp_json = resp.json()
    except Exception as e:
        flash(f"Failed to create tag: {e}", "danger")
        return redirect(url_for('index'))
    
    if resp_json.get('errors'):
        for error in resp_json['errors']:
            if error.get('extensions', {}).get('errorCode', {}).get('errorCode') == "CUSTOM_FIELD_ASSOCIATED_ENTITY_LIMIT_EXCEEDED":
                flash("You've exceeded the maximum number of associated entities for custom fields.", "danger")
                return redirect(url_for('index'))
        flash(f"Failed to create tag: {resp_json['errors']}", "danger")
        return redirect(url_for('index'))
    
    # After successful tag creation, only refresh custom fields
    custom_fields = fetch_custom_fields(token, realm_id)
    session['custom_fields'] = custom_fields
    
    flash("Tag created successfully.", "success")
    return redirect(url_for('index'))

@app.route("/create_invoice", methods=["POST"])
def create_invoice():
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
    
    url = f"{QB_BASE_URL}/{realm_id}/invoice?minorversion=70&include=enhancedAllCustomFields"
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
        resp = requests.post(url, json=data, headers=headers)
        
        if resp.status_code == 200:
            resp_json = resp.json()
            if 'Invoice' in resp_json and 'Id' in resp_json['Invoice']:
                inv_id = resp_json['Invoice']['Id']
                session['invoice_id'] = inv_id
                
                if inv_id:
                    deep_link = f"https://app.qbo.intuit.com/app/invoice?txnId={inv_id}&companyId={realm_id}"
                    session['invoice_deep_link'] = deep_link
                    flash(f"Success! Invoice created with ID: {inv_id}", "success")
                else:
                    flash("Invoice created but ID not found in response", "warning")
            else:
                flash("Invoice created but response format unexpected", "warning")
        else:
            session['invoice_id'] = None
            session['invoice_deep_link'] = None
            flash(f"Failed to create invoice: {resp.text}", "danger")
    except requests.exceptions.ContentDecodingError as e:
        flash("Error creating invoice: Content decoding error", "danger")
    except Exception as e:
        flash(f"Error creating invoice: {str(e)}", "danger")
    
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
    app.run(host="0.0.0.0", port=5001, debug=True)

