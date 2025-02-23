import streamlit as st
import pandas as pd
import openai
import os
import re
import agents

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
if 'next_step_id' not in st.session_state:
    st.session_state.next_step_id = 0
if 'plan_steps' not in st.session_state:
    st.session_state.plan_steps = None

uploaded_file = "Example_DataSet.xlsx"
df = pd.read_excel(uploaded_file, sheet_name='Sales')
df.columns = df.columns.str.lower().str.strip()
st.session_state.df = df
st.dataframe(st.session_state.df.head())

if st.button("Run Data Science") and 'df' in st.session_state and st.session_state.df is not None:
        if st.session_state['plan_steps'] == None:
            df_head_string = st.session_state.df.head().to_string(index=False)
            plan = agents.orchestrator(df_head_string)
            st.write(plan)
            plan_pattern = r'<step>(.*?)</step>'
            steps = re.findall(plan_pattern, plan, re.DOTALL)
            number_of_steps = len(steps)
            st.session_state.plan_steps = steps
            st.session_state.next_step = steps[0]
            st.session_state.next_step_id = 1
        
        st.subheader(f"Step {st.session_state.next_step_id} of {len(st.session_state.plan_steps)}")
        orchestrator_message = f"🤖 **:orange[Orchestrator Agent]**: In step {st.session_state.next_step_id}, I do the following: {st.session_state.next_step}"
        st.info(orchestrator_message)

        st.session_state.next_step_id += 1
        st.session_state.next_step = st.session_state.plan_steps[st.session_state.next_step_id]

        successful_code = False
        attempt = 0
        while attempt < 4 and successful_code == False:
            attempt += 1
            try:
                code = agents.executor(st.session_state.next_step, df_head_string)
                code_goal_pattern = r'<goal>(.*?)</goal>'
                code_type_pattern = r'<status>(.*?)</status>'
                code_goal = re.findall(code_goal_pattern, code, re.DOTALL)
                code_type = re.findall(code_type_pattern, code, re.DOTALL)
                python_code = re.findall(r"```python\n(.*?)\n```", code, re.DOTALL)
                code_goal_message = f"🧑‍💻 **:green[Software Engineer Agent]**: {code_goal[0]}"
                st.info(code_goal_message)
                if code_type[0] == "mutative":
                    st.info("🧑‍💻 **:green[Software Engineer Agent]**: 🚨 This code will change the dataframe.")
                else:
                    st.info("🧑‍💻 **:green[Software Engineer Agent]**: 💡 This code will not change the dataframe and only report some insights.")
                with st.expander("💻 **Generated Python Code**"):
                    st.code(python_code[0], language="python")
                with st.spinner("⏳ Running the code."):
                    exec_globals = {"df": st.session_state.df, "result": None}  # Ensure correct dataframe modification
                    exec(python_code[0], exec_globals)
                    final_results = exec_globals['result']
                    successful_code = True
            except Exception as e:
                st.warning(f"🧑‍💻 **:green[Software Engineer Agent]**: I failed in executing the code in my attempt {attempt} due to the following error: {str(e)}. Let me try again.")
            
        if successful_code == True:
            st.info(f"🧑‍💻 **:green[Software Engineer Agent]**: I succeeded to execute the code after {attempt} attempt(s).")
            with st.expander("📊 **Generated Results**"):
                st.code(final_results)
            explanation = agents.explainer(st.session_state.next_step, python_code[0], final_results, df_head_string)
            explanation_message = f"🧑‍🔬 **:blue[Data Scientist Agent]**: {explanation}"
            st.info(explanation_message)
            
            visualization = agents.visualizer(st.session_state.next_step, final_results, explanation, df_head_string)
            # st.warning(visualization)
            python_viz_code = re.findall(r"```python\n(.*?)\n```", visualization, re.DOTALL)
            viz_explain_pattern = r'<explain>(.*?)</explain>'
            viz_explain = re.findall(viz_explain_pattern, visualization, re.DOTALL)
            viz_explain_message = f"👁️ **:red[Visualization Agent]**: {viz_explain[0].strip()}"
            st.info(viz_explain_message)
            exec_globals = {"df": st.session_state.df, "result": None}  # Ensure correct dataframe modification
            if python_viz_code:
                with st.expander("💻 **Generated Visualization Code**"):
                    st.code(python_viz_code[0], language="python")
                try:
                    exec(python_viz_code[0], exec_globals)
                except Exception as e:
                    st.error(f"👁️ **:red[Visualization Agent]**: I wasn't able to show the visualization due to the following execution error: {e}")

            report = agents.reporter(plan, st.session_state.next_step, final_results, explanation, visualization, df_head_string, user_input)
            report_message = f"🎙️ **:violet[Reporter Agent]**: {report}"
            st.info(report_message)
        else:
            st.error(f"🧑‍💻 **:green[Software Engineer Agent]**: I failed to execute the code after {attempt} attempt(s).")

            # if step_cnt > 4:
            #     break
