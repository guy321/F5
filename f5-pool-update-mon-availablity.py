import requests
from requests.auth import HTTPBasicAuth
import json
import urllib3
import getpass

# Disable warnings for self-signed certificates (if applicable)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# BIG-IP details
bigip_ip = "10.0.0.111"          # Replace with your BIG-IP IP
username = "admin"               # Replace with your username 
password = getpass.getpass(f"Enter your password for user {username} on device {bigip_ip}: ")   # Replace with your password from terminal password prompt

# Lists of system and none loadbalancing teants on the F5 device that we do NOT want to touch
tentants_exclude_list = ["/", "Common", "Drafts", "EPSEC", "Status", "POLICYSYNC_pvr-sites-internal", "ServiceDiscovery", "appsvcs", "asm_nsyncd", "atgTeem", "bigiq-analytics.app", "datasync-global" , "f5-appsvcs-templates", "ssloGS_global.app"]

# Show reponse data in output like GET Response JSON: {'kind': 'tm:ltm:pool:poolstate'...............
# 0 = no
# 1 = yes
response_output = 0

# Global counts
g_tenant_count = 0
g_pool_count = 0

#######################################################

def get_tenants(exclude=None):
    
    #Retrieve a list of tenants (partitions) from the BIG-IP sys folder.
    
    url = f"https://{bigip_ip}/mgmt/tm/sys/folder"
    response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)
    
    if response.status_code == 401:
        print("Unauthorized: Incorrect username or password.")
        exit(1)  # Exit the program, or you could raise an Exception here.

    # Catch for none 200OK http status
    if response.status_code != 200:
        print("Error retrieving tenants:", response.text)
        return []
        
    folders = response.json().get("items", [])
    
    # Build a list of tenant info dictionaries. Use get() for 'partition' to avoid KeyError.
    tenants_search = [
        {"name": folder["name"],"partition": folder.get("partition", "")}
        for folder in folders
    ]
   
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
   
    # Retrieve a list of pools for the given tenant as dictionaries containing both
    # the pool name and the cleaned-up pool path (with slashes replaced by tildes).
    # Use the partition key to filter pools by tenant
    url = f"https://{bigip_ip}/mgmt/tm/ltm/pool"
    response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)
    
    if response.status_code != 200:
        print(f"Error retrieving pools for tenant '{tenant}':", response.text)
        return []
    
    pools = response.json().get('items', [])
    
    pools_info = [ {"name": pool["name"],"path": pool["fullPath"].replace("/", "~")}
        for pool in pools
        if pool["partition"] == tenant
    ]
    
    # Count number of pools found
    pool_count = len(pools_info)
    return pools_info, pool_count

def update_pool(pool_path):

    # Construct the API URL. The default partition is often "Common"
    url = f"https://{bigip_ip}/mgmt/tm/ltm/pool/{pool_path}"

    # GET the current pool configuration
    get_response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False)

    if get_response.status_code != 200:
        print("Error retrieving pool configuration:", get_response.text)
        exit()

    # Print full JSON response
    data = get_response.json()

    # Show full reponse data if varable is set to 1
    if response_output == 1:
        print("\n")
        print("GET Response JSON:", data)
    
    # Print the monitor key from the JSON response    
    print(" --- Monitor original value:", data['monitor'])

    # Set headers to indicate JSON content
    headers = {"Content-Type": "application/json"}

    # New monitor to be set for the pool (example payload)
    payload = ""
    mon_str = data['monitor']
    start_index = mon_str.find("{")
    end_index = mon_str.rfind("}")
    if start_index != -1 and end_index != -1:
        result = mon_str[start_index+1:end_index].strip()
        print(f" --- Monitor updated value: {result}") 
        payload = {"monitor": result}
        print(f" --- Json playload: {payload}")
    else:
        print(" --- Monitor Availability update NOT needed\n")
        return
    
    # Send a PATCH request to update the monitor field
    response = requests.patch(
        url,
        auth=HTTPBasicAuth(username, password),
        headers=headers,
        data=json.dumps(payload),
        verify=False
    )
    # Status of the PATCH reponse call to update the selected pool    
    print(" --- Patch Reponse Status Code:", response.status_code,"\n")    

    # Show full reponse data if varable is set to 1
    if response_output == 1:
        print(" --- Patch Response JSON:", response.json())
        print("\n")

if __name__ == "__main__":
    
    # Get tenants and their count
    tenants, g_tenant_count = get_tenants(exclude=tentants_exclude_list)
    print("Number of usable tenants found:", g_tenant_count)

    if not tenants:
        print("No usable tenants found.")
    else:
        # For each tenant show the pools        
        for tenant in tenants:
            # Print teant names
            
            pools = get_pools(tenant)[0]
            print(f"\nTenant: {tenant} - {get_pools(tenant)[1]} pools")            
            g_pool_count += get_pools(tenant)[1]           
        
            # Print pools names within the selected tenant
            for pool in pools:
                print(f" - Pool Name: {pool['name']}")
            print("\n")    
            # Print pool info and update monitor availbily value 
            for pool in pools:
                print(f" - Pool Name: {pool['name']}, Pool Path: {pool['path']}")
                print(f" -- Updating pool: {pool['name']}")          
                update_pool(pool['path'])
            
        print(f"\nUpdate complete\n{g_tenant_count} tenants and {g_pool_count} pools reviewed\n")        