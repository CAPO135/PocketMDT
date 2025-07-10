import streamlit as st
from utils.api import ask_question


def render_chat():
    st.subheader("💬 Chat with your AI Medical Team")

    if "messages" not in st.session_state:
        st.session_state.messages=[]

    # render existing chat history
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).markdown(msg["content"])

    # input and response
    user_input=st.chat_input("Type your question....")
    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role":"user","content":user_input})

        response=ask_question(user_input)
        if response.status_code==200:
            data=response.json()
            answer = (
                data.get("response") or
                data.get("summary") or
                data.get("message") or
                "Sorry, I couldn't process your request."
            )
            # Show follow-up questions if clarification is required
            if data.get("clarification_required"):
                follow_ups = data.get("follow_up_questions", [])
                if follow_ups:
                    answer += "\n\n**Follow-up questions:**\n" + "\n".join(f"- {q}" for q in follow_ups)
            sources=data.get("sources",[])
            st.chat_message("assistant").markdown(answer)
            # if sources:
            #     st.markdown("📄 **Sources: **")
            #     for src in sources:
            #         st.markdown(f"- `{src}`")
            st.session_state.messages.append({"role":"assistant","content":answer})
        else:
            st.error(f"Error: {response.text}")