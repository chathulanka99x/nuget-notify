import requests
from bs4 import BeautifulSoup
import json
import os
import concurrent.futures

url = 'https://raw.githubusercontent.com/chathulanka99x/nuget-notify/run/list.json'
unwanted_substrings = ['pre', 'alpha', 'beta', 'rc', 'dev', 'nightly', 'build', 'snapshot', '-g']
MAX_WORKERS = 5

response = requests.get(url)
if response.status_code == 200:
    packages = response.json()
else:
    print(f"Failed to retrieve the file. Status code: {response.status_code}")
    exit(1)

def get_nuget_url(name):
    return 'https://www.nuget.org/packages/'+name+'/#versions-body-tab'

def check_package(package):
    name = package["name"]
    target = package["version"]
    u = get_nuget_url(name)
    
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
        
        print(pkgs_list)
        pkgs_list = [row for row in pkgs_list if not any(sub in row for sub in unwanted_substrings)]
        
        if len(pkgs_list) > 0:
            latest = pkgs_list[0]
            return {"name": name, "from": target, "to": latest}
    else:
        print(f'Failed to retrieve the webpage. Status code: {response.status_code}')
    
    return None

updates = []
with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_to_package = {executor.submit(check_package, package): package for package in packages}
    
    for future in concurrent.futures.as_completed(future_to_package):
        result = future.result()
        if result:
            updates.append(result)

if os.path.exists('nuget.txt'):
    print("delete existing")
    os.remove('nuget.txt')

if len(updates) > 0:
    print("writing update")  
    with open('nuget.txt', 'w') as f:
        f.write('\n'.join([f"{u['name']} :     {u['from']} -> {u['to']}" for u in updates]))
