import streamlit as st
import pandas as pd
import openai
import os
import re
import agents
import util

# Set OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Initialize session state once
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'df' not in st.session_state:
    uploaded_file = "Example_DataSet.xlsx"
    df = pd.read_excel(uploaded_file, sheet_name='Sensors')
    df.columns = df.columns.str.lower().str.strip()
    st.session_state.df = df
if 'log' not in st.session_state:
    st.session_state.log = []
if 'next_step' not in st.session_state:
    st.session_state.next_step = None
if 'next_step_id' not in st.session_state:
    st.session_state.next_step_id = 0
if 'plan_steps' not in st.session_state:
    st.session_state.plan_steps = None
if "generated_code" not in st.session_state:
    st.session_state["generated_code"] = None
if "generated_viz_code" not in st.session_state:
    st.session_state["generated_viz_code"] = None
if "generated_result" not in st.session_state:
    st.session_state["generated_result"] = None
if "show_messages" not in st.session_state:
    st.session_state["show_messages"] = False  # Flag to show messages after the first click

# ✅ Streamlit UI
st.set_page_config(page_title="Sentravia: The AI Data Scientist", page_icon="🚀")
st.title("📊 Sentravia: The AI Data Scientist")

# ✅ Define a dictionary with emoji icons as avatars
avatar_mapping = {
    "user": "👤",
    "orchestrator agent": "🤖",
    "software engineer agent": "🧑‍💻",
    "data scientist agent": "🧑‍🔬",
    "visualization agent": "👁️",
    "reporter agent": "🎙️",
    "visualization": "📊"
}

# ✅ Input box and button in a container to prevent shifting
with st.container():
    user_input = st.text_area("Define your data science task below.", key="user_input")

    # Dynamic button label based on the current step
    if st.session_state['plan_steps'] and st.session_state.next_step_id < len(st.session_state['plan_steps']):
        button_label = f"Proceed to Step {st.session_state.next_step_id + 1}"
    else:
        button_label = "Proceed"  # Default label before starting or after finishing

    proceed_button = st.button(button_label)

# ✅ Button Logic (Second click now works as expected)
if proceed_button:
    st.session_state["show_messages"] = True  # Show messages after the first click
    st.session_state['messages'].append({"role": "user", "content": f"**User**: {user_input}"})

    df_head_string = st.session_state.df.head().to_string(index=False)

    # Initialize plan steps only once
    if st.session_state['plan_steps'] is None:
        plan = agents.orchestrator(df_head_string, user_input)
        plan_pattern = r'<step>(.*?)</step>'
        steps = re.findall(plan_pattern, plan, re.DOTALL)
        st.session_state.plan_steps = steps
        st.session_state.next_step_id = 0

    # ✅ Proceed to the next step if available
    if st.session_state.next_step_id < len(st.session_state.plan_steps):
        st.session_state.next_step = st.session_state.plan_steps[st.session_state.next_step_id]

        orchestrator_message = f"**Orchestrator Agent**: In step {st.session_state.next_step_id + 1} of {len(st.session_state.plan_steps)}, I do the following: {st.session_state.next_step}"
        st.session_state['messages'].append({"role": "orchestrator agent", "content": orchestrator_message})

        successful_code = False
        attempt = 0
        while attempt < 4 and not successful_code:
            attempt += 1
            try:
                code = agents.executor(st.session_state.next_step, df_head_string)
                code_goal_pattern = r'<goal>(.*?)</goal>'
                code_type_pattern = r'<status>(.*?)</status>'
                code_goal = re.findall(code_goal_pattern, code, re.DOTALL)
                code_type = re.findall(code_type_pattern, code, re.DOTALL)
                python_code = re.findall(r"```python\n(.*?)\n```", code, re.DOTALL)
                code_goal_message = f"**Software Engineer Agent**: **:green[(Attempt {attempt})]** {code_goal[0]}"
                if code_type[0] == "mutative":
                    code_goal_message += " 🚨 This code will change the dataframe."
                else:
                    code_goal_message += " 💡 This code will not change the dataframe and only report some insights."
                st.session_state['messages'].append({"role": "software engineer agent", "content": code_goal_message})

                st.session_state["generated_code"] = python_code[0]
                with st.spinner("⏳ Running the code."):
                    exec_globals = {"df": st.session_state.df, "result": None}
                    exec(python_code[0], exec_globals)
                    final_results = exec_globals['result']
                    successful_code = True
            except Exception as e:
                st.session_state['messages'].append(
                    {"role": "software engineer agent",
                     "content": f"**Software Engineer Agent**: I failed in executing the code in my attempt {attempt} due to the following error: `{str(e)}`. Let me try again."})

            if successful_code:
                st.session_state['messages'].append({"role": "software engineer agent",
                                                     "content": f"**Software Engineer Agent**: I succeeded to execute the code after {attempt} attempt(s)."})
                st.session_state["generated_result"] = final_results

                explanation = agents.explainer(st.session_state.next_step, python_code[0], final_results, df_head_string)
                explanation_message = f"**Data Scientist Agent**: {explanation}"
                st.session_state['messages'].append({"role": "data scientist agent", "content": explanation_message})

                visualization = agents.visualizer(st.session_state.next_step, final_results, explanation, df_head_string)
                python_viz_code = re.findall(r"```python\n([\s\S]*?)\n```", visualization)
                viz_explain_pattern = r'<explain>(.*?)</explain>'
                viz_explain = re.findall(viz_explain_pattern, visualization, re.DOTALL)
                viz_explain_message = f"**Visualization Agent**: {viz_explain[0].strip()}"
                st.session_state['messages'].append({"role": "visualization agent", "content": viz_explain_message})
                exec_globals = {"df": st.session_state.df, "result": None}
                if python_viz_code:
                    st.session_state["generated_viz_code"] = python_viz_code[0]
                    st.session_state['messages'].append({"role": "visualization", "content": python_viz_code[0]})

                report = agents.reporter(st.session_state.plan_steps, st.session_state.next_step, final_results,
                                         explanation, visualization,
                                         df_head_string, user_input)
                report_message = f"**Reporter Agent**: {report}"
                st.session_state['messages'].append({"role": "reporter agent", "content": report_message})

        st.session_state.next_step_id += 1
    else:
        st.session_state['messages'].append(
            {"role": "orchestrator agent", "content": "**:orange[Orchestrator Agent]**: All steps have been successfully completed!"})

# ✅ Display messages grouped by user message and reverse order
if st.session_state["show_messages"]:
    # Step 1: Group messages by user message
    groups = []
    current_group = []
    for message in st.session_state['messages']:
        if message['role'] == "user" and current_group:
            groups.append(current_group)  # Save the previous group
            current_group = []
        current_group.append(message)
    if current_group:
        groups.append(current_group)  # Save the last group

    # Step 2: Reverse the order of groups
    groups.reverse()

    # Step 3: Display each group in order (latest first)
    for group in groups:
        for message in group:
            avatar = avatar_mapping.get(message["role"], "💬")
            with st.chat_message(message["role"], avatar=avatar):
                if message["role"] == "visualization":
                    try:
                        exec_globals = {"df": st.session_state.df, "st": st}  # ✅ Pass st for visualizations
                        exec(message["content"].strip(), exec_globals)
                    except Exception as e:
                        st.error(f"Visualization Error: {str(e)}")
                        continue
                else:
                    if message["content"] == "":
                        st.markdown("_(No message communicated.)_")
                    else:
                        st.markdown(message["content"])


# ✅ Sidebar content persists now
with st.sidebar:
    if st.session_state["plan_steps"]:
        with st.expander("📋 **Plan Steps**"):
            st.write(st.session_state["plan_steps"])

    if st.session_state["generated_code"]:
        with st.expander("💻 **Generated Python Code**"):
            st.code(st.session_state["generated_code"], language="python")
    else:
        st.write("No code generated yet.")

    if st.session_state["generated_result"] is not None:
        with st.expander("💻 **Generated Results**"):
            st.write(st.session_state["generated_result"])
    else:
        st.write("No results generated yet.")

    if st.session_state["generated_viz_code"]:
        with st.expander("💻 **Generated Viz Code**"):
            st.code(st.session_state["generated_viz_code"], language="python")
    else:
        st.write("No code generated yet.")
