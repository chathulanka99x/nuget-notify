import requests
from bs4 import BeautifulSoup
import json
import os
import concurrent.futures

url = 'https://raw.githubusercontent.com/chathulanka99x/nuget-notify/main/list.json'
unwanted_substrings = ['pre', '-alpha', '-beta', '-rc','-dev']
MAX_WORKERS = 5  # Set to 5 concurrent requests

# Get the list of packages
response = requests.get(url)
if response.status_code == 200:
    packages = response.json()
else:
    print(f"Failed to retrieve the file. Status code: {response.status_code}")
    exit(1)

def get_nuget_url(name):
    return 'https://www.nuget.org/packages/'+name+'/#versions-body-tab'

def check_package(package):
    """Process a single package and return update info if available"""
    name = package["name"]
    target = package["version"]
    u = get_nuget_url(name)
    
    try:
        r = requests.get(u)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            version_history_div = soup.find('div', id='version-history')
            table = version_history_div.find('table')
            tbody = table.find('tbody')
            pkgs_list = []
            rows = tbody.find_all('tr')
            
            index = 0
            while index < len(rows):
                row = rows[index]
                first_td = row.find('td')
                link = first_td.find('a')
                cell_value = link.get_text(strip=True)
                if cell_value == target:
                    break
                pkgs_list.append(cell_value)
                index += 1
            
            # Filter out unwanted versions
            pkgs_list = [row for row in pkgs_list if not any(sub in row for sub in unwanted_substrings)]
            
            if len(pkgs_list) > 0:
                latest = pkgs_list[0]
                print(f"Found update for {name}: {target} -> {latest}")
                return {"name": name, "from": target, "to": latest}
        else:
            print(f'Failed to retrieve the webpage for {name}. Status code: {r.status_code}')
    except Exception as e:
        print(f"Error processing {name}: {str(e)}")
    
    return None

# Use ThreadPoolExecutor with 5 concurrent workers
updates = []
with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit all tasks and collect futures
    future_to_package = {executor.submit(check_package, package): package for package in packages}
    
    # Process results as they complete
    for future in concurrent.futures.as_completed(future_to_package):
        result = future.result()
        if result:
            updates.append(result)

# Write results to file
if os.path.exists('nuget.txt'):
    print("Deleting existing file")
    os.remove('nuget.txt')

if len(updates) > 0:
    print(f"Writing {len(updates)} updates to nuget.txt")  
    with open('nuget.txt', 'w') as f:
        f.write('\n'.join([f"{u['name']} :     {u['from']} -> {u['to']}" for u in updates]))
else:
    print("No updates found")
