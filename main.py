import streamlit as st
import pandas as pd
import openai
import os
import matplotlib.pyplot as plt
import re
import numpy as np

# Streamlit UI
st.set_page_config(page_title="Data Scientist LLM Agent", page_icon="🚀")
st.title("📊 Data Scientist LLM Agent")

# Set OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'log' not in st.session_state:
    st.session_state.log = []
if 'next_step' not in st.session_state:
    st.session_state.next_step = None

# Orchestrator Agent
def orchestrator():
    with st.spinner("🤖💭 Orchestrator agent is thinking ..."):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data scientist. You are an expert in data analysis."},
                {"role": "user", "content": f"You are given a dataset shown below. The dataset is already loaded in a dataframe called `df`. What are the steps that you take to analyze, clean, explore, and get insights for this specific dataset? Each step should be precise enough that a function or pandas code can do it.\n\n {st.session_state.df.head()} \n\n Identify each step with <step> and </step>. Each step should clearly and conscisely describe what will be done in that step. For instance 'check if there are any duplicate rows'. Avoid mentionning the step number. Avoid mentionning Python code in the step description."}
            ]
        )
        response = response.choices[0].message.content.strip()
    return response

# Executor Agent
def executor(plan_step, df_head_string):
    with st.spinner("🧑‍💻💭 Software engineering agent is working ..."):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data scientist. You are an expert in data analysis. Use first pronoun 'I' when answering."},
                {"role": "user", "content": f"You are given the following action recommendation as part of a data analysis pipeline: {plan_step}. Can you write a function in Python to do this? Please mention necessary imports as well such as pandas and numpy. The input should be the dataframe `df` and the output should be either one single dataframe or a text descriving insights. In both cases, call the function and put the output in one single variable called `result`. Given the whole code in one code block. It is important to assume df is given to you. You do not need to create any hypothetical dataframe for testing. Before you write the code, mention the objective between <goal> and </goal> starting with 'I'm going to write a code that ...'. Also mention a single word 'mutative' or 'introspective' between <status> and </status> where 'mutative' means that it returns a dataframe) and 'introspective' means it is returning insights in text form. For more context, here are the first few rows of the data: {df_head_string}."}
            ]
        )
        response = response.choices[0].message.content.strip()
    return response

# Explainer Agent
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

# Visualizer Agent
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

# Reporter Agent
def reporter(plan, step, final_results, explanation, visualization, df_head_string):
    with st.spinner("🎙️💭 Reporter agent is working ..."):
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data scientist. You are an expert in data analysis."},
                {"role": "user", "content": f"You are given the following data analysis pipeline: {plan}. The following step is executed: {step}. The final results are: {final_results}. The explanation is: {explanation}. The visualization is: {visualization}. Please reflect the quality of the analyis so far based on the overall plan. The will be two paragraphs, one summarizing what we know so far from the data, and one commenting on the analysis process so far. For more context, here are the first few rows of the data: {df_head_string}."}
            ]
        )
        response = response.choices[0].message.content.strip()
    return response

uploaded_file = "Example_DataSet.xlsx"
df = pd.read_excel(uploaded_file)
df.columns = df.columns.str.lower().str.strip()
st.session_state.df = df
st.dataframe(st.session_state.df.head())

if st.button("Run Data Science") and 'df' in st.session_state and st.session_state.df is not None:
        df_head_string = st.session_state.df.head().to_string(index=False)
        plan = orchestrator()
        plan_pattern = r'<step>(.*?)</step>'
        steps = re.findall(plan_pattern, plan, re.DOTALL)
        number_of_steps = len(steps)
        for step_cnt, step in enumerate(steps):
            st.subheader(f"Step {step_cnt+1} of {number_of_steps}")
            orchestrator_message = f"🤖 **:orange[Orchestrator Agent]**: In step {step_cnt+1}, I do the following: {step}"
            st.info(orchestrator_message)

            successful_code = False
            attempt = 0
            while attempt < 4 and successful_code == False:
                attempt += 1
                try:
                    code = executor(step, df_head_string)
                    # st.warning(code)
                    code_goal_pattern = r'<goal>(.*?)</goal>'
                    code_type_pattern = r'<status>(.*?)</status>'
                    code_goal = re.findall(code_goal_pattern, code, re.DOTALL)
                    code_type = re.findall(code_type_pattern, code, re.DOTALL)
                    python_code = re.findall(r"```python\n(.*?)\n```", code, re.DOTALL)
                    code_goal_message = f"🧑‍💻 **:green[Software Engineer Agent]**: {code_goal[0]}"
                    st.info(code_goal_message)
                    mutative_message = "🧑‍💻 **:green[Software Engineer Agent]**: 🚨 This code will change the dataframe."
                    introspective_message = "🧑‍💻 **:green[Software Engineer Agent]**: 💡 This code will not change the dataframe and only report some insights."
                    if code_type[0] == "mutative":
                        st.info(mutative_message)
                    else:
                        st.info(introspective_message)
                    # st.info(code_goal_message)
                    with st.expander("💻 **Generated Python Code**"):
                        st.code(python_code[0], language="python")
                    with st.spinner("⏳ Running the code."):
                        exec_globals = {"df": st.session_state.df, "result": None}  # Ensure correct dataframe modification
                        exec(python_code[0], exec_globals)
                        final_results = exec_globals['result']
                        # st.info(final_results)
                        successful_code = True
                except Exception as e:
                    st.warning(f"🧑‍💻 **:green[Software Engineer Agent]**: I failed in executing the code in my attempt {attempt} due to the following error: {str(e)}. Let me try again.")
            
            if successful_code == True:
                st.info(f"🧑‍💻 **:green[Software Engineer Agent]**: I succeeded to execute the code after {attempt} attempt(s).")
                with st.expander("📊 **Generated Results**"):
                    st.code(final_results)
                explanation = explainer(step, python_code[0], final_results, df_head_string)
                explanation_message = f"🧑‍🔬 **:blue[Data Scientist Agent]**: {explanation}"
                st.info(explanation_message)
            
                visualization = visualizer(step, final_results, explanation, df_head_string)
                # st.warning(visualization)
                python_viz_code = re.findall(r"```python\n(.*?)\n```", visualization, re.DOTALL)
                viz_explain_pattern = r'<explain>(.*?)</explain>'
                viz_explain = re.findall(viz_explain_pattern, visualization, re.DOTALL)
                viz_explain_message = f"👁️ **:red[Visualization Agent]**: {viz_explain[0].strip()}"
                st.info(viz_explain_message)
                exec_globals = {"df": st.session_state.df, "result": None}  # Ensure correct dataframe modification
                if python_viz_code:
                    try:
                        exec(python_viz_code[0], exec_globals)
                    except Exception as e:
                        st.error(f"👁️ **:red[Visualization Agent]**: I wasn't able to show the visualization due to the following execution error: {e}")

                report = reporter(plan, step, final_results, explanation, visualization, df_head_string)
                report_message = f"🎙️ **:violet[Reporter Agent]**: {report}"
                st.info(report_message)
            else:
                st.error(f"🧑‍💻 **:green[Software Engineer Agent]**: I failed to execute the code after {attempt} attempt(s).")

            if step_cnt > 4:
                break


# Display process log
# st.write("### Process Log")/
# st.write(st.session_state.log)
