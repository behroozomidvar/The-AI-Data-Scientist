import openai
import streamlit as st

def orchestrator(df_head_string, user_input):
    with st.spinner("🤖💭 Orchestrator agent is thinking ..."):
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data scientist. You are an expert in data analysis."},
                {"role": "user", "content": f"You are given a dataset shown below. The dataset is already loaded in a dataframe called `df`. What are the steps that you take to analyze, clean, explore, and get insights for this specific dataset? Align the steps with what the customer wants: '{user_input}'. Each step should be precise enough that a function or pandas code can do it.\n\n {df_head_string} \n\n Identify each step with <step> and </step>. Each step should clearly and conscisely describe what will be done in that step. For instance 'check if there are any duplicate rows'. Avoid mentionning the step number. Avoid mentionning Python code in the step description."}
            ]
        )
        response = response.choices[0].message.content.strip()
    return response

def executor(plan_step, df_head_string):
    with st.spinner("🧑‍💻💭 Software engineering agent is working ..."):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data scientist. You are an expert in data analysis. Use first pronoun 'I' when answering."},
                {"role": "user", "content": f"You are given the following action recommendation as part of a data analysis pipeline: {plan_step}. Can you write a function in Python to do this? Please mention necessary imports as well such as pandas and numpy. The input should be the dataframe `df` and the output should be either one single dataframe or a text descriving insights. In both cases, call the function and put the output in one single variable called `result`. Given the whole code in one code block. It is important to assume df is given to you. You do not need to create any hypothetical dataframe for testing. Before you write the code, mention the objective between <goal> and </goal> starting with 'I'm going to write a code that ...'. Also mention a single word 'mutative' or 'introspective' between <status> and </status> where 'mutative' means that it returns a dataframe) and 'introspective' means it is returning insights in text form. For more context, here are the first few rows of the data: {df_head_string}."}
            ]
        )
        return response.choices[0].message.content.strip()

def explainer(step, code, results, df_head_string):
    with st.spinner("🧑‍🔬💭 Data scientist agent is working ..."):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data scientist called 'Sasan'. You are an expert in data analysis. Use first pronoun 'I' when answering."},
                {"role": "user", "content": f"You are given the following action recommendation: {step}. The code written to do this action is the following: {code}. The result of this step is: {results}. Explain the results to the customer as a follow-up to the action recommendation. Avoid explaining code or any programming or data structure aspect. The customer is only interested in the data insights. The answer should be concise and contain necessary information. For more context, here are the first few rows of the data: {df_head_string}."}
            ]
        )
        response = response.choices[0].message.content.strip()
    return response

def visualizer(step, results, explanation, df_head_string):
    with st.spinner("👁️💭 Visualization agent is working ..."):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data scientist. You are an expert in data analysis."},
                {"role": "user", "content": f"You are given the following action recommendtion: {step}. A Python code is executed to obtain the following results: {results}. Pick ONLY ONE streamlit visualization option such as st.line_chart(df), st.area_chart(df), st.bar_chart(df), st.dataframe(df.style.highlight_max(axis=0)) to show the results. Your Python executable code show contain processing the dataframe to prepare for visualization. You have the data available in `df`. Also ensure you import pandas as `pd` in your code. Between <explain> and </explain>, explain what the visualization is depicting, starting with 'I'm going to visualize ...'. For more context, here are the first few rows of the data: {df_head_string}."}
            ]
        )
        response = response.choices[0].message.content.strip()
    return response

def reporter(plan, step, final_results, explanation, visualization, df_head_string):
    with st.spinner("🎙️💭 Reporter agent is working ..."):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data scientist. You are an expert in data analysis."},
                {"role": "user", "content": f"You are given the following data analysis pipeline: {plan}. The following step is executed: {step}. The final results are: {final_results}. The explanation is: {explanation}. The visualization is: {visualization}. Please reflect the quality of the analyis so far based on the overall plan. The will be two paragraphs, one summarizing what we know so far from the data, and one commenting on the analysis process so far. Please be concise. For more context, here are the first few rows of the data: {df_head_string}."}
            ]
        )
        response = response.choices[0].message.content.strip()
    return response
