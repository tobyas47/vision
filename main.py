import streamlit as st
import base64
from openai import OpenAI
from pdf2image import convert_from_bytes
import PyPDF2
from io import BytesIO


def new_upload():
    st.session_state["flag"] = True


def on_file_upload():
    if not uploaded_file:
        return
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    if uploaded_file.type in ["image/png", "image/jpeg", "image/jpg"]:
        byte_stream = BytesIO(uploaded_file.getvalue())
        byte_content = byte_stream.getvalue()
        base64_encoded_data = base64.b64encode(byte_content).decode("utf-8")

        content = [
            {
                "type": "text",
                "text": "Answer the user's questions based on the image.",
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_encoded_data}"},
            },
        ]

    elif selected_option == "Plain texts":
        pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.read()))

        # Initialize a variable to store all the text
        full_text = ""

        # Iterate through each page in the PDF
        for page in pdf_reader.pages:
            # Extract text from the current page
            text = page.extract_text()

            # Add the text to the full_text variable
            if text:  # Making sure text is not None
                full_text += text

        content = f"Answer the user's questions based on the following file: <<<file begins>>> {full_text} <<<file ends>>>"

    elif selected_option == "GPT-Vision":
        images = convert_from_bytes(uploaded_file.read())
        content = [
            {
                "type": "text",
                "text": "Answer the user's questions based on the images.",
            }
        ]
        for image in images:
            buffer = BytesIO()
            # Save the image to the buffer in PNG format
            image.save(buffer, format="PNG")
            # Retrieve the byte data from the buffer
            byte_data = buffer.getvalue()
            # Encode this byte data to Base64
            b64_image = base64.b64encode(byte_data).decode("utf-8")

            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                }
            )

    st.session_state.context = [{"role": "system", "content": content}]

    st.session_state["flag"] = False


options = ["Plain texts", "GPT-Vision"]


if "context" not in st.session_state:
    st.session_state["context"] = []

with st.sidebar:
    openai_api_key = st.text_input(
        "OpenAI API Key", key="chatbot_api_key", type="password"
    )
    if st.button("Clear Chat History"):
        st.session_state.messages = []

    # Create the selectbox widget
    selected_option = st.selectbox(
        label="Choose how to parse pdfs...", options=options, on_change=new_upload
    )

    if uploaded_file := st.file_uploader(
        "Choose a file to upload: ",
        accept_multiple_files=False,
        on_change=new_upload,
    ):
        if st.session_state["flag"]:
            on_file_upload()
    else:
        st.session_state.context = []

st.title("💬 Chatbot")

if "messages" not in st.session_state or st.session_state["messages"] == []:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Message ChatGPT..."):
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})

    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    messages.extend(st.session_state.context)
    messages.extend(st.session_state.messages[-10:])

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            max_tokens=4096,
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
