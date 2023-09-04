# Given the client ID and tenant ID for an app registered in Azure,
# provide an Azure AD access token and a refresh token.

# If the caller is not already signed in to Azure, the caller's
# web browser will prompt the caller to sign in first.

# pip install msal
import PublicClientApplication
import sys

# You can hard-code the registered app's client ID and tenant ID here,
# or you can provide them as command-line arguments to this script.
client_id = 'dcd47f2d-bda3-46b9-bd90-70718944e9b3'
tenant_id = 'fde7ec07-ff18-4eac-8be7-36b50f109f24'

# Do not modify this variable. It represents the programmatic ID for
# Azure Databricks along with the default scope of '/.default'.
scopes = [ 'api://1217394a-b874-47ea-b557-d4e038cb834e/data.read' ]

app = PublicClientApplication(
  client_id = client_id,
  authority = "https://login.microsoftonline.com/" + tenant_id
)

acquire_tokens_result = app.acquire_token_interactive(
  scopes = scopes
)

if 'error' in acquire_tokens_result:
  print("Error: " + acquire_tokens_result['error'])
  print("Description: " + acquire_tokens_result['error_description'])
else:
  print("Access token:\n")
  print(acquire_tokens_result['access_token'])
  print("\nRefresh token:\n")
  print(acquire_tokens_result['refresh_token'])