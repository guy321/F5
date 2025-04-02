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
password = getpass.getpass("Enter your password: ")   # Replace with your password from terminal password prompt

# Lists of system and none loadbalancing teants on the F5 device that we do NOT want to touch
tentants_exclude_list = ["/", "Common", "Drafts", "EPSEC", "Status", "POLICYSYNC_pvr-sites-internal", "ServiceDiscovery", "appsvcs", "asm_nsyncd", "atgTeem", "bigiq-analytics.app", "datasync-global" , "f5-appsvcs-templates", "ssloGS_global.app"]

def get_tenants(exclude=None):
    
    #Retrieve a list of tenants (partitions) from the BIG-IP sys folder.
    
    url = f"https://{bigip_ip}/mgmt/tm/sys/folder"
    response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)
    
    # Catch for none 200OK http status
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
    
    # if exclude is None:
    #     exclude = []
    
    # Filter out tenants based on multiple conditions. Catch for any tenant that name stats with device-group and or is in the above exlucde list, 
    # and also if the tenant returned does not have a partition path. 
    # No partition path idicates it is the tenant class object from AS3 deployments, 
    # where if the path was present it would most likely be ppplication class object from the AS3 deoployments.     
    tenants = [
        tenant["name"] for tenant in tenants_search 
        if tenant["name"] not in exclude 
            and not tenant["name"].startswith("device-group")
            and tenant["partition"] == ""            
    ] 

    # Count number of tenants found
    tenant_count = len(tenants)

    return tenants, tenant_count

def get_pools(tenant):
    
    # #Retrieve a list of pools for the given tenant.
    
    # # Use the partition query parameter to filter pools by tenant
    # url = f"https://{bigip_ip}/mgmt/tm/ltm/pool"
    # response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)
    
    # if response.status_code != 200:
    #     print(f"Error retrieving pools for tenant '{tenant}':", response.text)
    #     return []
    
    # items = response.json().get('items', [])

    # # Return a list of pool names tha match the selected tenant
    # pools = [
    #     pool['name'] for pool in items
    #     if pool['partition'] == tenant
    # ]
    # pool_path  = [
    #     pool['fullPathj'].replace("/","~") for pool in items
    #     if pool['partition'] == tenant
    # ]
    # return pools, pool_path


    #  Retrieve a list of pools for the given tenant as dictionaries containing both
    # the pool name and the cleaned-up pool path (with slashes replaced by tildes).
    
    # Use the partition query parameter to filter pools by tenant
    url = f"https://{bigip_ip}/mgmt/tm/ltm/pool"
    response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)
    
    if response.status_code != 200:
        print(f"Error retrieving pools for tenant '{tenant}':", response.text)
        return []
    
    items = response.json().get('items', [])
    
    pools_info = [
        {
            "name": pool["name"],
            "path": pool["fullPath"].replace("/", "~")
        }
        for pool in items
        if pool["partition"] == tenant
    ]
    
    return pools_info

def update_pool(pool_path):

    # Construct the API URL. The default partition is often "Common"
    url = f"https://{bigip_ip}/mgmt/tm/ltm/pool/{pool_path}"

    #GET the current pool configuration
    get_response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)

    if get_response.status_code != 200:
        print("Error retrieving pool configuration:", get_response.text)
        exit()

    # Print full JSON response
    data = get_response.json()
    print("\n")
    print("GET Response JSON:", data)
    
    # Print the monitor key from the JSON response
    print("\n")      
    print("Monitor original value:", data['monitor'])

    # Set headers to indicate JSON content
    headers = {
        "Content-Type": "application/json"
    }

    # New monitor to be set for the pool (example payload)
    payload = ""
    s = data['monitor']
    start_index = s.find("{")
    end_index = s.rfind("}")
    if start_index != -1 and end_index != -1:
        result = s[start_index+1:end_index].strip()
        print(f"Monitor updated value: {result}") 
        payload = {"monitor": result}
        print(payload)
    else:
        print("Monitor Availability update NOT needed\n")
        return
    
    # Send a PATCH request to update the monitor field
    response = requests.patch(
        url,
        auth=HTTPBasicAuth(username, password),
        headers=headers,
        data=json.dumps(payload),
        verify=False
    )

    print("\n")
    print("Status Code:", response.status_code)
    print("\n")
    print("Patch Response JSON:", response.json())
    print("\n")

if __name__ == "__main__":
    # First, list all tenants (partitions)
    print("Number of usable teants found: ", get_tenants(exclude=tentants_exclude_list)[1])
    tenants = get_tenants(exclude=tentants_exclude_list)[0]
    if not tenants:
        print("No usable tenants found.")
    else:
        # For each tenant show the pools        
        for tenant in tenants:
            print(f"\nTenant: {tenant}")            
            pools = get_pools(tenant)
            
            for pool_list in pools:
                print(f" - Pool Name: {pool_list['name']}")

            print("\n Starting to update pools\n")
            
            for pool in pools:
                print(f" - Pool Name: {pool['name']}, Pool Path: {pool['path']}")
                print(f" -- Updating pool: {pool['name']}")          
                update_pool(pool['path'])
            
            print("\nUpdating pools complete\n")