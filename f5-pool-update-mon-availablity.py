import requests
from requests.auth import HTTPBasicAuth
import json
import urllib3
import getpass

# Disable warnings for self-signed certificates (if applicable)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# BIG-IP details
bigip_ip = "10.0.0.111"          # Replace with your BIG-IP IP <<===================================================================================
username = "admin"               # Replace with your username <<====================================================================================
password = getpass.getpass("Enter your password: ")   # Replace with your password

#To be change to pulling from the f5 device for all pools in all tenants
pool_name = "~tyf5wauxapi-vip~tyF5wauxapi-vip_ssl-app~pool_tyF5wauxapi-vip_ssl"  # Replace with your pool name

tentants_exclude_list = ["/", "Common", "Drafts", "EPSEC", "Status", "POLICYSYNC_pvr-sites-internal", "ServiceDiscovery", "appsvcs", "asm_nsyncd", "atgTeem", "bigiq-analytics.app", "datasync-global" , "f5-appsvcs-templates", "ssloGS_global.app"]
#tentants_exclude_list = []

def get_tenants(exclude=None):
    
    #Retrieve a list of tenants (partitions) from the BIG-IP.
    
    url = f"https://{bigip_ip}/mgmt/tm/sys/folder"
    response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)
    

    if response.status_code != 200:
        print("Error retrieving tenants:", response.text)
        return []
    
    folders = response.json().get("items", [])
    
    # Build a list of tenant info dictionaries. Use get() for 'partition' to avoid KeyError.
    tenants_search = [
        {"name": folder["name"],           
         "partition": folder.get("partition", "")}
        for folder in folders
    ]
    
    if exclude is None:
        exclude = []
    
    # Filter out tenants based on multiple conditions    
    tenants = [
        tenant["name"] for tenant in tenants_search 
        if tenant["name"] not in exclude 
            and not tenant["name"].startswith("device-group")
            and tenant["partition"] == ""
            
    ]        
    
    tenant_count = len(tenants)

    return tenants, tenant_count

def get_pools(tenant):
    
    #Retrieve a list of pools for the given tenant.
    
    # Use the partition query parameter to filter pools by tenant
    url = f"https://{bigip_ip}/mgmt/tm/ltm/pool?partition={tenant}"
    response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)
    if response.status_code != 200:
        print(f"Error retrieving pools for tenant '{tenant}':", response.text)
        return []
    items = response.json().get('items', [])
    # Return a list of pool names (you can modify this to return the full details)
    pools = [pool['name'] for pool in items]
    return pools

def update_pool():

    # Construct the API URL. The default partition is often "Common"
    url = f"https://{bigip_ip}/mgmt/tm/ltm/pool/{pool_name}"

    #GET the current pool configuration
    get_response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)
    if get_response.status_code != 200:
        print("Error retrieving pool configuration:", get_response.text)
        exit()

    # Print full JSON response
    data = get_response.json()
    print("\n")
    print("GET Response JSON:", data)
    print("\n")
    print("Pool Name", data['name'])

    # Print the monitor key from the JSON response
    print("\n")      
    print("Monitor value:", data['monitor'])

    # Set headers to indicate JSON content
    headers = {
        "Content-Type": "application/json"
    }

    # New monitor to be set for the pool (example payload)
    payload = {
        "monitor": "/Common/tcp and /Common/gateway_icmp and /Common/https"
    }

    # Send a PATCH request to update the monitor field
    response = requests.patch(
        url,
        auth=HTTPBasicAuth(username, password),
        headers=headers,
        data=json.dumps(payload),
        verify=False  # Use verify=True in production with valid certificates
    )

    print("\n")
    print("Status Code:", response.status_code)
    print("\n")
    print("Patch Response JSON:", response.json())


if __name__ == "__main__":
    # First, list all tenants (partitions)
    print("Number of usable teants found: ", get_tenants(exclude=tentants_exclude_list)[1])
    tenants = get_tenants(exclude=tentants_exclude_list)[0]
    if not tenants:
        print("No usable tenants found.")
    else:        
        for tenant in tenants:
            print(f"{tenant}")
    
    # print("\nListing pools within each tenant:")
    # # For each tenant, list pools found
    # for tenant in tenants:
    #     print(f"\nTenant: {tenant}")
    #     pools = get_pools(tenant)
    #     if pools:
    #         for pool in pools:
    #             print(f"    Pool: {pool}")
    #     else:
    #         print("    No pools found in this tenant.")
