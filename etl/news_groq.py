from dotenv import load_dotenv
load_dotenv()
from groq import Groq
import os

'''
This code entirely depends on Groq service. Just move it to Hugginface Inference API if this is failing. 
Or Just use spacy to format the content somehow? Maybe try a SLM or something that runs locally.
https://huggingface.co/microsoft/Phi-3-mini-4k-instruct

'''
client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)

def getNewsSummary(htmlBody:str) -> str:
    return htmlBody
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "system",
                "content": "JSON. You are the best news anchor. You take news article as input and produce a news article with the same content but cleaned and only paragraphs. NO TITLE. Minimum 2 Pragraphs."
            },
            {
                "role": "user",
                "content": f"{htmlBody}"
            }
        ],
        temperature=0,
        max_tokens=4096,
        top_p=0.01,
        stream=False,
        stop=None,
    )

    return (completion.choices[0].message.content)
