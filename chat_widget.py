import traceback
import requests
import streamlit as st

# Production webhook URL (via ngrok tunnel to local n8n)
# NOTE: this ngrok URL changes if you restart ngrok on a free plan —
# update this line whenever that happens.
WEBHOOK_URL = "https://apochromatic-sigrid-nondistractive.ngrok-free.dev/webhook/dashboard-chat"


def _fetch_answer(question):
    status_code = None
    try:
        response = requests.post(
            WEBHOOK_URL,
            json={"chatInput": question},  # must match CodeBase node's expected field
            timeout=60
        )
        status_code = response.status_code
        response.raise_for_status()

        try:
            data = response.json()

            # n8n's "Respond to Webhook" may return a list with one item
            if isinstance(data, list) and len(data) > 0:
                data = data[0]

            # Try common response keys
            answer = str(
                data.get("answer")
                or data.get("output")
                or data.get("response")
                or data.get("text")
                or ""
            )

            if not answer:
                answer = str(data)

        except Exception:
            answer = response.text

        # Final guard: if we still ended up with nothing (e.g. n8n returned
        # a 200 OK with a completely empty body — a misconfigured
        # "Respond to Webhook" node, or the workflow finishing without
        # actually returning anything), show a diagnostic instead of
        # silently rendering a blank message with no clue why.
        if not answer or not answer.strip():
            answer = (
                f"⚠️ The chatbot service returned an empty response (HTTP {status_code}). "
                "This usually means the n8n workflow finished without sending data back — "
                "check the 'Respond to Webhook' node's configuration and the workflow's execution log."
            )

    except requests.exceptions.ConnectionError:
        answer = (
            "❌ Can't reach the chatbot service. Check that n8n is running, "
            "the workflow is Active, and the ngrok tunnel is still live."
        )
    except requests.exceptions.Timeout:
        answer = "❌ The request timed out. Try a simpler question."
    except Exception as e:
        answer = f"❌ Request failed: {type(e).__name__}: {e}"

    return answer


def _safe_fragment_rerun():
    """
    Reruns just this fragment. Falls back to a normal full-app rerun if
    Streamlit rejects the fragment-scoped rerun — this happens in a rare
    race condition where something OUTSIDE the fragment (e.g. changing the
    period filter elsewhere on the page) triggers a full-page rerun at the
    same moment this fragment was about to rerun itself. A full rerun here
    is a safe degrade: worst case is one extra whole-page reload in a rare
    race, instead of a crash.
    """
    try:
        st.rerun(scope="fragment")
    except st.errors.StreamlitAPIException:
        st.rerun()


@st.fragment
def show_chat():
    """
    Floating chat bubble, bottom-right of the viewport — call this ONCE,
    ANYWHERE in the main app body (NOT inside `with st.sidebar:` anymore).
    It positions itself via fixed CSS regardless of where in the page it's
    called from, so it no longer competes for space with the sidebar's nav
    rail — a long conversation can never push nav links out of view again,
    since chat now lives in its own popover, not the sidebar's scroll area.

    Wrapped in @st.fragment so chat interactions only rerun this widget,
    not the entire dashboard (the "whole dashboard goes grey" fix from
    before still applies here).

    Two-phase question/answer flow (submit -> rerun -> answer -> rerun)
    keeps every message rendered before chat_input() is called in a given
    run, so the answer never lands below the input.
    """
    st.markdown("""
    <style>
    div.st-key-floating_chat_bubble {
        position: fixed !important;
        bottom: 24px !important;
        right: 24px !important;
        top: auto !important;
        left: auto !important;
        z-index: 9999 !important;
        width: 56px !important;
        height: 56px !important;
    }
    .st-key-floating_chat_bubble button {
        border-radius: 50% !important;
        width: 56px !important;
        height: 56px !important;
        padding: 0 !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
        border: none !important;
        background:
            url("data:image/png;base64,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") no-repeat center / 78% 78%,
            linear-gradient(135deg, #7C3AED, #D946EF) no-repeat center / 100% 100% !important;
    }
    .st-key-floating_chat_bubble button p {
        font-size: 0 !important;
        line-height: 0 !important;
    }
    .st-key-floating_chat_bubble svg {
        display: none !important;
    }
    .st-key-floating_chat_bubble [data-testid*="Icon"] {
        display: none !important;
    }
    .st-key-floating_chat_bubble button:hover {
        box-shadow: 0 6px 18px rgba(0,0,0,0.32);
        transform: scale(1.05);
    }
    </style>

    """, unsafe_allow_html=True)

    with st.container(key="floating_chat_bubble"):
        with st.popover("chat", use_container_width=False):
            st.markdown("### 🤖 AI Assistant")

            if "messages" not in st.session_state:
                st.session_state.messages = []
            if "chat_pending" not in st.session_state:
                st.session_state.chat_pending = False

            history_box = st.container(height=350)
            with history_box:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

                if st.session_state.chat_pending:
                    question = st.session_state.messages[-1]["content"]
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            answer = _fetch_answer(question)
                            st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.session_state.chat_pending = False
                    _safe_fragment_rerun()

            question = st.chat_input("Ask your dashboard...")

            if question:
                st.session_state.messages.append({"role": "user", "content": question})
                st.session_state.chat_pending = True
                _safe_fragment_rerun()