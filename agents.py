import openai
import streamlit as st
import yaml

# Load YAML file once
with open("prompts.yaml", "r") as file:
    PROMPTS = yaml.safe_load(file)

# Default model
DEFAULT_MODEL = "gpt-4o-mini"

# Common OpenAI Call
def call_openai(agent_name, model=DEFAULT_MODEL, **kwargs):
    prompt_data = PROMPTS[agent_name]
    system_prompt = prompt_data["system"]
    user_prompt = prompt_data["user"].format(**kwargs)
    agent_title = prompt_data["name"]
    
    with st.spinner(f"💭 {agent_title.capitalize()} agent is acting ..."):
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content.strip()

# Functions for each agent
def orchestrator(df_head_string, user_input):
    user_preference = PROMPTS['user_preference']['description']
    return call_openai("orchestrator", df_head_string=df_head_string, user_input=user_input, user_preference=user_preference)

def executor(plan_step, df_head_string):
    return call_openai("executor", plan_step=plan_step, df_head_string=df_head_string)

def explainer(step, code, results, df_head_string):
    return call_openai("explainer", step=step, code=code, results=results, df_head_string=df_head_string)

def visualizer(step, results, explanation, df_head_string):
    return call_openai("visualizer", step=step, results=results, explanation=explanation, df_head_string=df_head_string)

def reporter(plan, step, final_results, explanation, visualization, df_head_string, user_input, model=DEFAULT_MODEL):
    return call_openai("reporter", plan=plan, step=step, final_results=final_results, explanation=explanation, visualization=visualization, df_head_string=df_head_string, user_input=user_input, model=model)
