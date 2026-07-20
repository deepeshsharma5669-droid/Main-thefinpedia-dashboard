import os
import traceback
import requests
import streamlit as st

st.write("Running:", os.path.abspath(__file__))

# Production webhook URL (via ngrok tunnel to local n8n)
# NOTE: this ngrok URL changes if you restart ngrok on a free plan —
# update this line whenever that happens.
WEBHOOK_URL = "https://apochromatic-sigrid-nondistractive.ngrok-free.dev/webhook/dashboard-chat"


def show_chat():
    st.markdown("## 🤖 AI Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Ask your dashboard...")

    if question:
        st.session_state.messages.append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                answer = None

                try:
                    response = requests.post(
                        WEBHOOK_URL,
                        json={"chatInput": question},  # must match CodeBase node's expected field
                        timeout=60
                    )

                    # Debug information — remove these once everything works reliably
                    st.write("Status Code:", response.status_code)
                    st.write("Headers:", dict(response.headers))
                    st.write("Raw Response:", response.text)

                    response.raise_for_status()

                    try:
                        data = response.json()
                        st.write("Parsed JSON:", data)

                        # n8n's "Respond to Webhook" may return a list with one item
                        if isinstance(data, list) and len(data) > 0:
                            data = data[0]

                        # Try common response keys
                        answer = (
                            data.get("output")
                            or data.get("response")
                            or data.get("answer")
                            or data.get("text")
                        )

                        if answer is None:
                            answer = str(data)

                    except Exception as e:
                        st.error(f"JSON Parse Error: {e}")
                        answer = response.text

                except requests.exceptions.ConnectionError:
                    st.code(traceback.format_exc())
                    answer = (
                        "❌ Can't reach the chatbot service. Check that n8n is running, "
                        "the workflow is Active, and the ngrok tunnel is still live."
                    )
                except requests.exceptions.Timeout:
                    st.code(traceback.format_exc())
                    answer = "❌ The request timed out. Try a simpler question."
                except Exception:
                    st.code(traceback.format_exc())
                    answer = "❌ Request failed."

                st.markdown(answer)

        st.session_state.messages.append(
            {"role": "assistant", "content": answer}
        )