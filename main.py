import streamlit as st
from openai import OpenAI
import json
import random


# Set up the Streamlit app
st.set_page_config(page_title="Medical Simulation App", page_icon=":hospital:")

# Retrieve the API key from the secrets file
PERPLEXITY_API_KEY = st.secrets["perplexity"]["api_key"]
client = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")

# Load patient cases from JSON file (Using absolute path as requested)
with open(r"patient_cases.json", "r") as f:
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
    "patient": "llama-3.1-8b-instruct",
    "physical_exam": "llama-3.1-8b-instruct",
    "attending_physician": "llama-3.1-70b-instruct"
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
- When appropriate and natural ask "pimp questions" about important information

Remember to maintain an educational approach, encouraging critical thinking and clinical reasoning rather than spoiling the diagnostic process. You may need to ask the user for more information about the patient. """
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
    st.session_state.clear()  # Clear all session state to start fresh

# Page routing
if selection == "About":
    st.title("**House Calls - The Diagnostic Challenge**")
    st.write("""
    Welcome to House Calls - The Diagnostic Challenge! Here, students can practice patient encounters through interactive chat simulations. Experience different aspects of patient care from initial consultation to diagnosis and management under the guidance of simulated physicians.
    """)

    st.subheader("How to Use the App")
    st.markdown("""
    - **Select a Case**: Navigate to the 'Select Case' page to choose or randomly select a medical case to simulate.
    - **Interact with the Patient**: On the 'Patient' page, you can gather patient history as if you were conducting an actual consultation.
    - **Perform Physical Exam & Diagnostics**: Here, you'll receive objective information on physical examination findings, lab results, and imaging. Use this to make differential diagnoses.
    - **Consult with the Attending Physician**: Get guidance, suggest appropriate investigations, and discuss potential diagnoses and treatments with an experienced physician simulation.
    - **Start a New Case**: Use the 'New Case' button in the sidebar to reset the simulation for a fresh start.
    
    After going through a case, you can choose another or select a random one for more practice. Your goal is to diagnose the patient by synthesizing the information provided through each interaction.
    """)

    # Insert a clickable link to the Qualtrics survey
    st.markdown("Please [take this survey](https://rvu.qualtrics.com/jfe/form/SV_bQTnsSPyFuNWsKy) to help us improve the app!")

    st.subheader("Disclaimer")
    st.markdown("""
    **House Calls - The Diagnostic Challenge** is an educational tool intended for medical students and practitioners to practice clinical reasoning. The information provided here is for educational purposes only and should not be used for real patient care. Always consult with a licensed healthcare provider for actual medical diagnosis and treatment. Use of this app does not create a doctor-patient relationship, nor does it guarantee diagnostic accuracy or replace the need for professional medical judgment.
    """)

elif selection == "Select Case":
    st.title("Select a Patient Case")
    cases = list(PATIENT_CASES.keys())
    # Prepend a placeholder option to the list of cases
    options = ["Select a case..."] + cases
    # Use the placeholder as the default value
    selected_case = st.selectbox("Choose a case:", options, index=0)
    
    if selected_case != "Select a case...":
        # If a case is selected, proceed with the selection
        if st.button("Select"):
            st.session_state.selected_case = selected_case
            st.success(f"Case '{selected_case}' selected. Navigate to other pages to interact with the case.")
    
    # Integrate random case selection into the Select Case page
    if st.button("Random Case"):
        random_case = select_random_case()
        st.session_state.selected_case = random_case
        st.success(f"Random case selected. Navigate to other pages to interact with the case.")

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
            case_info = PATIENT_CASES.get(st.session_state.selected_case, {})  # Safely attempt to get case info
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

            # Display assistant's message while streaming
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for response in client.chat.completions.create(
                    model=MODELS[page],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state[f"{page}_messages"]
                    ],
                    stream=True,
                ):
                    if response.choices:
                        chunk = response.choices[0].delta.content or ""
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")

                # Remove the cursor indicator once the message is complete
                message_placeholder.markdown(full_response)

            # Add the assistant's message to the session state
            st.session_state[f"{page}_messages"].append({"role": "assistant", "content": full_response})
