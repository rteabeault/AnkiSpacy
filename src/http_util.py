import requests

def get(url, params=None, **kwargs):
  return requests.get(url, params=params, **kwargs)


