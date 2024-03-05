import streamlit as st
import base64
from openai import OpenAI
from pdf2image import convert_from_bytes
from io import BytesIO

openai_api_key = st.secrets["api_key"]
client = OpenAI(api_key=openai_api_key)


st.title("💬 Chatbot")

if uploaded_file := st.file_uploader(
    "Choose files to upload: ", accept_multiple_files=False
):
    images = convert_from_bytes(uploaded_file.read())
    for image in images:
        buffer = BytesIO()
        # Save the image to the buffer in PNG format
        image.save(buffer, format="PNG")
        # Retrieve the byte data from the buffer
        byte_data = buffer.getvalue()
        # Encode this byte data to Base64
        b64_image = base64.b64encode(byte_data).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Transcribe all the texts in the image. Only respond with the texts.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                        },
                    ],
                }
            ],
            max_tokens=4096,
        )
        msg = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", messages=st.session_state.messages
    )
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
