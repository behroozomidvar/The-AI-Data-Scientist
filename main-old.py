import streamlit as st
import pandas as pd
import openai
import re
import matplotlib.pyplot as plt
import os

# Streamlit UI
st.title("Data Assist")

# Set OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize session state for storing modified dataframe
if 'df' not in st.session_state:
    st.session_state.df = None

# Upload Excel or CSV file
uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("Select a sheet", sheet_names)
        df = pd.read_excel(xls, sheet_name=selected_sheet)
    
    # Convert column names to lowercase and remove whitespace
    df.columns = df.columns.str.lower().str.strip()
    st.session_state.df = df  # Store the initial dataframe
    
    st.write("### Preview of the Data:")
    st.dataframe(df.head())
    
    # User input question
    question = st.text_area("Ask a question about the data:")
    
    if st.button("Get Answer"):
        if question and st.session_state.df is not None:
            df = st.session_state.df
            
            # OpenAI API call to generate Python code
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that generates clean Python code to compute answers based on a dataset provided in a dataframe named 'df'. Ensure the code updates 'df' if necessary and stores the computed answer in 'result'. Use only available column names from 'df' and reference exact values from the dataset. Make sure that filtering operations correctly modify the dataframe. Return only executable code without explanations."},
                    {"role": "user", "content": f"Generate a Python script that will compute the answer to the following question using the dataframe 'df' with these columns: {list(df.columns)} and sample values: {df.head(3).to_dict()}. {question}. Alwasy remember to import pandas as `pd` at the top of the code."}
                ]
            )
            
            # Extract only the code from the response
            python_code = response.choices[0].message.content
            python_code = re.findall(r"```python\n(.*?)\n```", python_code, re.DOTALL)
            python_code = python_code[0] if python_code else response.choices[0].message.content
            
            st.write("### Generated Python Code:")
            st.code(python_code, language='python')
            
            # Execute the generated code
            try:
                exec_globals = {"df": df.copy(), "result": None}  # Ensure correct dataframe modification
                exec(python_code, exec_globals)
                
                # Check if any output variable exists
                if exec_globals.get("result") is not None:
                    computed_answer = exec_globals["result"]
                    st.write("### Computed Answer (Top 5 Rows):")
                    st.dataframe(computed_answer if isinstance(computed_answer, pd.DataFrame) else pd.DataFrame([[computed_answer]], columns=["Result"]))
                    
                    # Generate a concise final answer in an information box
                    response = openai.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an AI assistant that generates a natural language summary of the tabular output."},
                            {"role": "user", "content": f"The user asked the following question: '{question}'. Provide an answer to the question using the following information: {computed_answer if isinstance(computed_answer, pd.DataFrame) else [computed_answer]}. The answer should be concise and contain necessary information."}
                        ]
                    )
                    final_answer = response.choices[0].message.content
                    st.info(final_answer)  # Display in an information box
                    
                    # Ask LLM what visualization should be generated
                    response = openai.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an AI assistant that determines the most relevant visualization type based on the computed answer and user question. Provide only executable Python code inside triple backticks."},
                            {"role": "user", "content": f"The user asked the following question: '{question}'. The computer answer is the following: '{computed_answer if isinstance(computed_answer, pd.DataFrame) else [computed_answer]}'. The available dataframe contains these columns: {list(df.columns)}. The computed answer has this structure: {computed_answer.head(3).to_dict() if isinstance(computed_answer, pd.DataFrame) else str(computed_answer)}. I'd like to create a visualization to let the user get some insights relevant to their question and motivate them to explore further. What visualization do you propose? Provide only a Python matplotlib or pandas visualization code snippet inside triple backticks. You have the data available in `df`. Also ensure you import pandas as `pd` in your code."}
                        ]
                    )
                    visualization_code = response.choices[0].message.content.strip()
                    
                    # Extract visualization code
                    visualization_code = re.findall(r"```python\n(.*?)\n```", visualization_code, re.DOTALL)
                    visualization_code = visualization_code[0] if visualization_code else ""
                    
                    if visualization_code:
                        st.write("### Suggested Visualization Code:")
                        st.code(visualization_code, language='python')
                        
                        st.write("### Generated Visualization:")
                        try:
                            exec_globals = {"df": st.session_state.df, "plt": plt}
                            exec(visualization_code, exec_globals)
                            fig = plt.gcf()
                            st.pyplot(fig)
                        except Exception as e:
                            st.write("Could not generate visualization.", e)
                else:
                    st.error("The generated code did not produce a result. Please refine your question or check the code.")
            except Exception as e:
                st.error(f"Error executing code: {e}")
        else:
            st.warning("Please enter a question.")
