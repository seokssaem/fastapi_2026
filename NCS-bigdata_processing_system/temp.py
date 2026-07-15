# Python3 샘플 코드 #


import requests

url = 'http://apis.data.go.kr/B551015/API187/HorseRaceInfo'
params ={'serviceKey' : '99c2b74393bf9ad904c2ee0e30d9855816a3347ccbd514747caa7ce851497c25', 'pageNo' : '1', 'numOfRows' : '10', 'ym_fr' : '201901', 'ym_to' : '202012' }

response = requests.get(url, params=params)
print(response.content)