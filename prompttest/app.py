import streamlit as st
import pandas as pd

from utils import get_variables, get_response, format_prompt, is_key_valid
from db import add_row, delete_rows, get_row

# global variables
if 'response' not in st.session_state:
    st.session_state['response'] = ''

if 'runs_dataframe' not in st.session_state:
    runs_df = pd.read_sql_table(table_name='runs', con='sqlite:///database.db')
    st.session_state['runs_dataframe'] = runs_df

# functions
def update_df():
    runs_df = pd.read_sql_table(table_name='runs', con='sqlite:///database.db')
    st.session_state['runs_dataframe'] = runs_df
    return

def update_response(model: str, temperature: float, prompt: str, key: str):
    messages = [{'role': 'user', 'content': prompt}]
    with st.spinner('Generando respuesta...'):
        response = get_response(
                model=model,
                temperature=temperature,
                messages=messages,
                key=key
                )
    
    if response:
        st.success('Hecho', icon='✅')
        st.session_state['response'] = response
    return

def save_prompt(model: str, temperature: float, name: str, prompt: str, variable_list: list[str], response: str, ranking :int):
    add_row(
            model=model, temperature=temperature,
            name=name, prompt=prompt, variable_list=variable_list,
            response=response, ranking=ranking)
    st.success('Experimento guardado', icon='✅')
    return

def clean_values():
    st.session_state['response'] = ''
    st.session_state['run_name'] = ''
    st.session_state['prompt_template'] = ''
    return

def load_values(row: int):
    row_values = get_row(row)
    st.session_state['response'] = ''
    st.session_state['run_name'] = row_values['run_name']
    st.session_state['prompt_template'] = row_values['prompt_template']
    return

def check_key(key: str):
    if is_key_valid(key):
        st.success('API Key Guardada', icon='✅')
        return True
    else:
        st.error('La API Key no es correcta', icon="🚨")
        return False


# Page config 
st.set_page_config(page_title='Promptest', layout='wide' )

# sidebar stuff
with st.sidebar:
    model = st.selectbox(
            label='Seleccione el modelo',
            options=('gpt-4', 'gpt-3.5-turbo'),
            index=1
            )
    temperature = st.slider(
        label='Seleccione la temperatura de GPT',
        min_value=0.0,
        max_value=1.0,
        step=0.05,
        value=0.0
        ),
    api_key = st.text_input(
            label='Ingrese su "api key" de OpenAI',
            type="password") 

# check if api_key is valid 
api_key_bool = check_key(api_key)
# get float temp
temperature_float = temperature[0] # extraer dato de temperatura

# title 
st.title('Experimentación de prompts')

# main container
with st.container():
    col1, col2 = st.columns([1,1])
    run_name = col1.text_input(
            label='**Nombre del experimento**',
            placeholder='Experimento 1',
            key='run_name'
            )
    prompt_template = col1.text_area(
        label='**Prompt Template**',
        help='De instrucciones al modelo. Utilice {{}} para agregar variables al prompt.',
        placeholder='¿Qué significa {{palabra}}?', 
        key='prompt_template'
    )
    variables = get_variables(prompt_template)
    for i,variable in enumerate(variables):
        col2.text_input(label='**{}**'.format(variable), key='variable_{}'.format(i))
   
    variable_map = {variable_name:st.session_state['variable_{}'.format(i)] for i,variable_name in enumerate(variables)}
    formated_prompt = format_prompt(prompt_template, variable_map)

    # openai response
    st.write('**Respuesta**:\n{}'.format(st.session_state['response']))
    rank_col, __  = st.columns([1,1])
    ranking = rank_col.select_slider(
            label='**Califique la respuesta**',
            options=list(range(1,6)),
            disabled=(not prompt_template or not run_name or not st.session_state['response'] ),
            format_func=lambda x: '⭐️'*x
            )
    
    # Buttons
    col1_button, col2_button, col3_button,  __ = st.columns([0.12, 0.12, 0.12, 0.64])
    run_button = col1_button.button(
            label='Ejecutar',
            on_click=update_response,
            args=[model, temperature_float, formated_prompt, api_key],
            disabled=(not prompt_template or not run_name or not api_key_bool)
            )
    save_button = col2_button.button(
            label='Guardar', on_click=save_prompt,
            args=[model, temperature_float, run_name, 
                  prompt_template, variables,
                  st.session_state['response'], ranking],
            disabled=(not prompt_template or not run_name)
            )
    clean_button = col3_button.button(
            label='Limpiar',
            on_click=clean_values
            )

# Historic data
st.markdown('---')
with st.expander('Experimentos guardados'):
    update_df()
    show_df = st.session_state['runs_dataframe']
    id_list = show_df.id.tolist()
    action_option = st.selectbox(
            label='**Seleccione una acción**',
            options=['Ver', 'Filtrar', 'Borrar', 'Editar']
            )
    if action_option == 'Filtrar':
        id_filter = st.multiselect(
                label='**Seleccione los ids**',
                options=id_list,
                default = id_list[:10]
                )
        show_df = show_df[show_df.id.isin(id_filter)]
    elif action_option == 'Borrar':
        id_delete = st.multiselect(
                label='**Seleccione las filas que desea borrar**',
                options=id_list, 
                key='delete_ids'
                )
        delete_button = st.button(label='Borrar', on_click=delete_rows, args=[id_delete])
    elif action_option == 'Editar':
       id_edit = st.selectbox(
               label='**Selecciona la fila que desea editar**',
               options=id_list,
               key='edit_row'
               ) 
       edit_button = st.button(
               label='Editar',
               on_click=load_values,
               args=[id_edit]
               )
    else:
        pass
    st.write('**Experimentos**')
    st.dataframe(
        data=show_df,
        hide_index=True,
        column_config={
            'id': 'Fila', 'model': 'Modelo', 'temperature': 'Temperatura',
            'name':st.column_config.TextColumn('Nombre Experimento', width='medium'), 'creation_date': 'Fecha de Creación', 
            'response': st.column_config.TextColumn('Respuesta', width='large'),
            'ranking': st.column_config.NumberColumn('Ranking', format='%d ⭐️')}
        )
