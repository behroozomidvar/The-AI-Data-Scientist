import streamlit as st

# Define a dictionary with emoji icons as avatars
avatar_mapping = {
    "user": "👤",
    "orchestrator agent": "🤖",
    "software engineer agent": "🧑‍💻",
    "data scientist agent": "🧑‍🔬",
    "visualization agent": "👁️",
    "reporter agent": "🎙️",
    "visualization": "📊"
}

def show_messages(session_state_messages):
    
    # Step 1: Group messages by user message
    groups = []
    current_group = []
    for message in session_state_messages:
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
                    successful_viz = False
                    attempt_viz = 0
                    while attempt_viz < 4 and not successful_viz:
                        attempt_viz += 1
                        try:
                            exec_globals = {"df": st.session_state.df, "st": st}  # ✅ Pass st for visualizations
                            exec(message["content"].strip(), exec_globals)
                            successful_viz = True
                        except Exception as e:
                            st.warning(f"**Visualization Agent**: Visualization failed in attempt {attempt_viz} due to `{str(e)}`. Retrying...")

                    # If still not successful after all attempts
                    if not successful_viz:
                        st.error("**Visualization Agent**: ❌ I could not generate the visualization after 3 attempts.")
                
                else:
                    if message["content"] == "":
                        st.markdown("_(No message communicated.)_")
                    else:
                        st.markdown(message["content"])

def show_sidebar(session_state):
    sidebar_showing = ['plan_steps', 'generated_code', 'generated_result', 'generated_viz_code', 'generated_report']
    sidebar_labels = {
        'plan_steps': 'Plan Steps',
        'generated_code': 'Generated Code',
        'generated_result': 'Generated Result',
        'generated_viz_code': 'Generated Visualization Code',
        'generated_report': 'Generated Report'
    }
    with st.sidebar:
        for sidebar_element in sidebar_showing:
            if session_state[sidebar_element]:
                with st.expander(f"💻 {sidebar_labels[sidebar_element]}"):
                    if sidebar_element in ["generated_code", "generated_viz_code"]:
                        st.code(session_state[sidebar_element], language="python")
                    elif sidebar_element == "plan_steps":
                        st.write(session_state[sidebar_element])
                    else:
                        st.markdown(session_state[sidebar_element])