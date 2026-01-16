import os
import google.genai as genai

client = genai.Client(api_key="dummy_key") 
print(dir(client.models))