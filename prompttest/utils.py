import re
import openai
import os


def get_variables(prompt):
    variable_list = re.findall('(\{\{\S+\}\})', prompt)
    variable_list = [s.replace('{','').replace('}', '') for s in variable_list]
    return variable_list


def get_response(model, temperature, messages, key, stream=False):

    openai.api_key = key 
    response = openai.ChatCompletion.create(
            model=model,
            temperature=temperature,
            messages=messages
            )
    return response['choices'][0]['message']['content']


def format_prompt(prompt: str, variable_map: dict[str]):
    for variable_name in variable_map:
        prompt = prompt.replace('{{{{{}}}}}'.format(variable_name), variable_map[variable_name])
        return prompt


def is_key_valid(key: str):
    try:
        openai.api_key = key
        response = openai.Model.list()
    except:
        return False
    else:
        return True
