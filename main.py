import streamlit as st
from huggingface_hub import InferenceClient
import json
import random

# Set up the Streamlit app
st.set_page_config(page_title="Medical Simulation App", page_icon=":hospital:")

# Retrieve the API key from the secrets file
HUGGINGFACE_API_KEY = st.secrets["huggingface"]["api_key"]
client = InferenceClient(token=HUGGINGFACE_API_KEY)

# Load patient cases from JSON file
with open("patient_cases.json", "r") as f:
    PATIENT_CASES = json.load(f)

# Define pages
PAGES = {
    "About": "about",
    "Select Case": "select_case",
    "Patient": "patient",
    "Physical Exam & Diagnostics": "physical_exam",
    "Attending Physician": "attending_physician"
}

# Define models for each page
MODELS = {
    "patient": "mistralai/Mistral-Nemo-Instruct-2407",
    "physical_exam": "mistralai/Mistral-Nemo-Instruct-2407",
    "attending_physician": "mistralai/Mistral-Nemo-Instruct-2407"
}

# Common instructions for each page
COMMON_INSTRUCTIONS = {
    "patient": """Provide information as if you are a real patient. Answers should generally be concise.""",
    "physical_exam": """You provide objective information about physical examination findings, laboratory studies, and imaging results. Keep your information factual. DO NOT interpret the results.""",
    "attending_physician": """You are an experienced attending physician overseeing the case but not revealing all information at once. Your role is to:
- Help formulate differential diagnoses based on the information provided.
- Suggest appropriate investigations like imaging, lab work, or additional clinical exams.
- Guide the user through the diagnostic process, providing feedback on their approach.
- Once the correct diagnosis is agreed upon, discuss treatment options, expected responses, and any relevant management considerations.
- When appropriate and natural, ask "pimp questions" about important information.
Remember to maintain an educational approach, encouraging critical thinking and clinical reasoning rather than spoiling the diagnostic process. You may need to ask the user for more information about the patient."""
}

# Function to combine common instructions with case-specific details
def construct_system_message(case_info, page):
    common = COMMON_INSTRUCTIONS.get(page, "")
    specific = case_info.get(page, {}).get("system_message", "")
    return f"{common}\n\n{specific}"

# Function to select a random case
def select_random_case():
    cases = list(PATIENT_CASES.keys())
    return random.choice(cases)

# Sidebar navigation
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

# Sidebar - Case reset
if st.sidebar.button("New Case"):
    st.session_state.clear()

# Page routing
if selection == "About":
    [About page content remains the same...]

elif selection == "Select Case":
    [Select Case page content remains the same...]

elif selection in ["Patient", "Physical Exam & Diagnostics", "Attending Physician"]:
    if 'selected_case' not in st.session_state:
        st.error("Please select a case first.")
    else:
        page = PAGES[selection]
        st.title(f"{selection} Encounter")

        # Initialize session state for messages
        if f"{page}_messages" not in st.session_state:
            st.session_state[f"{page}_messages"] = []

        # Add system message to the start of the conversation
        if not st.session_state[f"{page}_messages"]:
            case_info = PATIENT_CASES.get(st.session_state.selected_case, {})
            if case_info:
                system_message = construct_system_message(case_info, page)
                st.session_state[f"{page}_messages"].append({"role": "system", "content": system_message})
            else:
                st.error(f"No case information found for this case ({st.session_state.selected_case}). Please select a valid case.")

        # Display previous messages
        for message in st.session_state[f"{page}_messages"]:
            if message["role"] in ["user", "assistant"]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Get user input
        if prompt := st.chat_input("Interact with the patient, perform diagnostics or discuss with the attending physician:"):
            # Add user message to the session state
            st.session_state[f"{page}_messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate the assistant's response
            try:
                response = client.text_generation(
                    prompt=prompt,
                    model=MODELS[page],
                    max_new_tokens=500
                )
                assistant_response = response.strip()
                st.session_state[f"{page}_messages"].append({"role": "assistant", "content": assistant_response})
                with st.chat_message("assistant"):
                    st.markdown(assistant_response)
            except Exception as e:
                st.error(f"An error occurred: {e}")

