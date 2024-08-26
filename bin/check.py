import requests
from bs4 import BeautifulSoup
import json
import os
url = 'https://raw.githubusercontent.com/chathulanka99x/nuget-notify/main/list.json'
response = requests.get(url)
if response.status_code == 200:
    packages = response.json()
else:
    print(f"Failed to retrieve the file. Status code: {response.status_code}")
def get_nuget_url(name):
  return 'https://www.nuget.org/packages/'+name+'/#versions-body-tab'

updates = []
for i in packages:
  u = get_nuget_url(i["name"])
  r = requests.get(u)
  if r.status_code == 200:
      soup = BeautifulSoup(r.content, 'html.parser')
      version_history_div = soup.find('div', id='version-history')
      table = version_history_div.find('table')
      tbody = table.find('tbody')
      pkgs_list = []
      target = i["version"]
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
        index +=1
      pkgs_list = [row for row in pkgs_list if 'pre' not in row]
      if len(pkgs_list) > 0:
        latest = pkgs_list[0]
        updates.append({"name":i["name"], "from": i["version"],"to":latest})
  else:
      print(f'Failed to retrieve the webpage. Status code: {response.status_code}')

if os.path.exists('updates.txt'):
    os.remove('updates.txt')

if len(updates) > 0:
  with open('updates.txt', 'w') as f:
    f.write('\n'.join([f"{u['name']} :     {u['from']} -> {u['to']}" for u in updates]))
