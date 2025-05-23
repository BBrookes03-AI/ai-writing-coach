import streamlit as st
import openai

openai.api_key = st.secrets["OPENAI_API_KEY"]

st.title("Nova: AI Writing Coach")

user_input = st.text_area("Paste your thesis or paragraph draft below:")

focus = st.selectbox("What kind of feedback would you like?", [
    "Clarity",
    "Thesis strength",
    "Tone and audience awareness",
    "Grammar and sentence structure",
    "General improvement"
])

if st.button("Get Feedback"):
    if user_input.strip() == "":
        st.warning("Please enter some text.")
    else:
        with st.spinner("Nova is reviewing your writing..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are an academic writing tutor. Provide feedback focusing on {focus}."},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=500
            )
            reply = response["choices"][0]["message"]["content"]
            st.success("Here's Nova's feedback:")
            st.markdown(reply)
